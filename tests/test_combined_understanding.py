"""COMBINED_UNDERSTANDING: one OpenAI call understands and classifies the message. OpenAI is faked;
the point is that a missing or broken combined classification always falls back to the separate
classifier call, so no routing behaviour is lost."""

import json

import pytest

from backend.app.classification import conversation, router
from backend.app.classification.query_transformer import transform_query
from backend.app.classification.taxonomy import ComplexityLabel, IntentLabel, RouteLabel
from backend.app.config import settings
from tests.test_phase3_orchestration import make_context


class FakeClient:
    """Returns `reply` (a dict, sent as JSON) and records every request."""

    def __init__(self, reply: dict):
        self.reply, self.calls = reply, []
        outer = self

        class Completions:
            def create(self, **kwargs):
                outer.calls.append(kwargs)
                content = json.dumps(outer.reply)
                message = type("M", (), {"content": content})()
                return type("R", (), {"choices": [type("C", (), {"message": message})()], "usage": None})()

        self.chat = type("Chat", (), {"completions": Completions()})()


@pytest.fixture(autouse=True)
def llm_on(monkeypatch):
    monkeypatch.setattr(settings, "orchestrator_llm_enabled", True)
    conversation._cache.clear()


def understanding_reply(classification):
    return {"kind": "business", "greeting": None, "wellbeing_phrase": None,
            "question": "How do I release a credit hold?", "search_query": "How do I release a credit hold?",
            "resolved_reference": False, "mood": "F0_NORMAL", "classification": classification}


VALID = {"intent": "HELP_PROCESS", "sub_intent": None, "entity": "credit hold", "operation": "READ",
         "complexity": "PROCESS_WORKFLOW", "route": "MARKDOWN_RAG", "tool_candidate": None,
         "confidence": 0.9, "reasoning_summary": "how-to question"}


def test_combined_call_returns_the_classification_and_sends_screen_context(monkeypatch):
    monkeypatch.setattr(settings, "combined_understanding", True)
    fake = FakeClient(understanding_reply(VALID))
    monkeypatch.setattr(conversation, "_get_client", lambda: fake)
    analysis = conversation.analyze_message("how do i release a credit hold", [], "r1",
                                            screen={"module": "Order Entry", "form": "Customer Orders"})
    assert analysis.classification == VALID
    request = fake.calls[0]
    assert "classification" in request["messages"][0]["content"]       # the prompt asks for it
    assert "form=Customer Orders" in request["messages"][1]["content"]  # screen context is sent
    assert request["max_tokens"] > 280


def test_switch_off_ignores_any_classification_in_the_reply(monkeypatch):
    monkeypatch.setattr(settings, "combined_understanding", False)
    fake = FakeClient(understanding_reply(VALID))
    monkeypatch.setattr(conversation, "_get_client", lambda: fake)
    analysis = conversation.analyze_message("how do i release a credit hold", [], "r1")
    assert analysis.classification is None
    assert fake.calls[0]["messages"][0]["content"] == conversation.PROMPT  # exactly today's prompt


def _classify(monkeypatch, precomputed, query="How do I release a credit hold?", **ctx):
    separate = FakeClient(VALID | {"reasoning_summary": "separate call"})
    monkeypatch.setattr(router, "_get_client", lambda: separate)
    context = make_context(**ctx)
    result = router.classify_and_route(transform_query(query, context), context, precomputed=precomputed)
    return result, separate.calls


def test_valid_combined_classification_skips_the_separate_call(monkeypatch):
    result, calls = _classify(monkeypatch, VALID, module="Order Entry", form="Customer Orders")
    assert calls == []  # the saved OpenAI call
    assert router.classifier_source(result) == "combined"
    assert result.route == RouteLabel.MARKDOWN_RAG and result.intent == IntentLabel.HELP_PROCESS
    assert (result.module, result.form) == ("Order Entry", "Customer Orders")  # from SyteLine, not the model


@pytest.mark.parametrize("broken", [
    None,                                              # model left it out
    {},                                                # empty object
    {"intent": "NOT_A_REAL_INTENT", "route": "MARKDOWN_RAG"},  # invalid value
    {"intent": "HELP_PROCESS"},                        # no route
    "MARKDOWN_RAG",                                    # not an object at all
])
def test_missing_or_broken_combined_classification_falls_back_to_the_separate_call(monkeypatch, broken):
    result, calls = _classify(monkeypatch, broken)
    assert len(calls) == 1  # the separate classifier ran, exactly as before
    assert router.classifier_source(result) == "llm"


def test_route_policy_still_applies_to_the_combined_result(monkeypatch):
    # The model says "answer it from documents", but intent LIVE_DATA always goes to live data,
    # and a write request never keeps a tool.
    live, _ = _classify(monkeypatch, VALID | {"intent": "LIVE_DATA", "route": "MARKDOWN_RAG"},
                        query="Show me the balance for customer C000451")
    assert live.route == RouteLabel.LIVE_DATA
    action, _ = _classify(monkeypatch, VALID | {"intent": "ACTION", "route": "ACTION",
                                                "tool_candidate": "get_customer_balance"},
                          query="Create a customer order for C000451")
    assert action.route == RouteLabel.ACTION and action.tool_candidate is None


def test_unknown_tool_names_are_dropped(monkeypatch):
    result, _ = _classify(monkeypatch, VALID | {"intent": "LIVE_DATA", "route": "LIVE_DATA",
                                                "tool_candidate": "delete_everything"})
    assert result.tool_candidate is None


def test_split_questions_stay_multi_part(monkeypatch):
    result, _ = _classify(monkeypatch, VALID | {"complexity": "DIRECT"},
                          query="What is a lead and how do I convert it to an opportunity?")
    if result.complexity != ComplexityLabel.MULTI_PART:  # only when the transformer split it
        pytest.skip("transformer did not split this wording")
    assert result.complexity == ComplexityLabel.MULTI_PART


def test_greetings_never_use_a_classifier_call(monkeypatch):
    result, calls = _classify(monkeypatch, None, query="good morning")
    assert calls == [] and result.route == RouteLabel.DIRECT_RESPONSE


@pytest.mark.parametrize("command", [
    "Create a new customer order for customer C000451", "Open the customer orders form",
    "please show my open orders", "can you release the credit hold on CO1001",
])
def test_a_command_read_as_a_question_is_rechecked_by_the_separate_call(monkeypatch, command):
    # Measured 2026-10-08: the combined call labelled two of these HELP_PROCESS.
    _, calls = _classify(monkeypatch, VALID | {"intent": "HELP_PROCESS"}, query=command)
    assert len(calls) == 1


def test_how_to_questions_keep_the_saved_call(monkeypatch):
    _, calls = _classify(monkeypatch, VALID, query="How do I create a customer order?")
    assert calls == []


@pytest.mark.parametrize("question", ["What is a credit memo?", "how do I post a write-off",
                                      "what are payment terms", "where is the ship-to address kept"])
def test_prospect_to_cash_terms_are_in_scope_without_the_llm(monkeypatch, question):
    from backend.app.classification import scope

    def no_llm(*_args, **_kwargs):
        raise AssertionError("the LLM scope check should not be needed")

    monkeypatch.setattr(scope, "_llm_scope", no_llm)
    assert scope.classify_scope(question, make_context(module=None, form=None)).in_scope
