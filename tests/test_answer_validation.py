"""Phase 5 step 1 — answer validation (hallucination guard). No network: the grounding LLM is faked."""

import pytest

from backend.app.config import settings
from backend.app.quality import answer_validator as av
from backend.app.rag.markdown_processor import MarkdownChunk

EVIDENCE_TEXT = (
    "To release a credit hold, open the Customer Orders form, clear the Credit Hold check box, "
    "and save. Payment terms such as Net 30 are set on the Customers form. "
    "Orders above 1,000 USD need approval."
)


def _chunk(text: str = EVIDENCE_TEXT) -> MarkdownChunk:
    return MarkdownChunk(
        chunk_id="credit-1", document_id="credit", text=text, embed_text=text, level="credit",
        section_level1="Credit", section_level2="Release a credit hold", section_level3="",
        full_context_path="Credit > Release a credit hold", source_file="credit.md",
        chunk_index=0, total_chunks=1, keywords="credit hold",
    )


@pytest.fixture(autouse=True)
def validation_on(monkeypatch):
    monkeypatch.setattr(settings, "answer_validation_enabled", True)


def _fake_llm(monkeypatch, *responses):
    """Each call to the grounding check returns the next response (or raises it)."""
    calls = list(responses)

    def fake(question, answer, evidence):
        item = calls.pop(0)
        if isinstance(item, Exception):
            raise item
        return item

    monkeypatch.setattr(av, "llm_grounding_check", fake)


def _run(answer: str, regenerate=lambda claims: "", question="How do I release a credit hold?"):
    return av.validate_answer(question, answer, [_chunk()], request_id="test", regenerate=regenerate)


# ── Rule checks ────────────────────────────────────────────────────────

def test_number_missing_from_evidence_is_flagged():
    assert av.unsupported_numbers("Payment terms are Net 45.", "", EVIDENCE_TEXT) == ["45"]


@pytest.mark.parametrize("answer", [
    "1. Open the Customer Orders form.\n2. Clear the Credit Hold check box.\n3. Save.",
    "Payment terms such as Net 30 are set on the Customers form.",
    "Orders above 1000 USD need approval.",  # same number as "1,000" in the evidence
    "Orders above 1,000 USD need approval.",
    "You can do this in 2 steps.",  # single digits are counts, not facts
])
def test_supported_numbers_and_step_numbering_pass(answer):
    assert av.unsupported_numbers(answer, "", EVIDENCE_TEXT) == []


def test_number_from_the_question_is_allowed():
    assert av.unsupported_numbers("Order CO-12345 is shown on the form.", "where is order 12345", "") == []


@pytest.mark.parametrize("answer", [
    "I have released the credit hold for you.",
    "I've updated the payment terms.",
    "We have posted the payment.",
    "The invoice has been created for you.",
])
def test_action_claims_are_flagged(answer):
    assert av.action_claims(answer)


@pytest.mark.parametrize("answer", [
    "Once the order has been created, open the Customer Orders form.",
    "After you have posted the payment, the invoice closes.",
    "I can explain how to release a credit hold.",
])
def test_instructions_are_not_action_claims(answer):
    assert av.action_claims(answer) == []


@pytest.mark.parametrize("answer", [
    "The retrieved information does not provide specific steps for adding items to an estimate.",
    "I'm sorry, but there is no information available here about how SyteLine permissions work.",
    "The steps to change customer payment terms are not provided in the available information. "
    "I can help with setting up a new customer instead.",
])
def test_refusals_are_recognised(answer):
    assert av.looks_not_found(answer)


@pytest.mark.parametrize("answer", [
    "Detailed approval rules are not provided, but you can release a hold like this:\n"
    "1. Open the Customer Orders form.\n2. Clear the Credit Hold check box.\n3. Save.",
    "Open the Customer Orders form, clear the Credit Hold check box, and save.",
    "No information is posted to the ledger until the invoice is printed.",
])
def test_real_answers_are_not_refusals(answer):
    assert not av.looks_not_found(answer)


def test_polite_refusal_is_not_found_even_if_llm_says_answered(monkeypatch):
    _fake_llm(monkeypatch, av.GroundingCheck([], True))
    result = _run("I'm sorry, but there is no information available here about that.")
    assert result.action == "not_found"


# ── Leaks ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("answer, reason", [
    ("Use key sk-abcdefghijklmnopqrstuvwx to connect.", "secret_pattern"),
    ("password = Hunter2024", "secret_pattern"),
    ("Retrieved Context: [Source: credit.md]", "prompt_text"),
])
def test_leaks_are_replaced_without_calling_the_llm(monkeypatch, answer, reason):
    _fake_llm(monkeypatch)  # any LLM call would pop from an empty list and fail the test
    result = _run(answer)
    assert result.action == "replaced"
    assert result.reason == reason
    assert result.answer == av.UNSAFE_ANSWER


# ── Full flow ──────────────────────────────────────────────────────────

GOOD = "Open the Customer Orders form, clear the Credit Hold check box, and save."


def test_grounded_answer_passes(monkeypatch):
    _fake_llm(monkeypatch, av.GroundingCheck([], True))
    result = _run(GOOD)
    assert (result.action, result.answer, result.llm_checked) == ("passed", GOOD, True)


def test_answer_that_does_not_answer_is_not_found(monkeypatch):
    text = "The steps to change payment terms are not provided in the available information."
    _fake_llm(monkeypatch, av.GroundingCheck([], False))
    result = _run(text)
    assert result.action == "not_found"
    assert result.answer == text


def test_unsupported_claim_is_repaired_once(monkeypatch):
    seen = []

    def regenerate(claims):
        seen.append(claims)
        return GOOD

    _fake_llm(monkeypatch, av.GroundingCheck(["Click the Release button"], True), av.GroundingCheck([], True))
    result = _run(GOOD + " Then click the Release button.", regenerate=regenerate)
    assert result.action == "repaired"
    assert result.answer == GOOD
    assert seen == [["Click the Release button"]]
    assert result.unsupported_claims == ["Click the Release button"]


def test_still_unsupported_after_repair_is_replaced(monkeypatch):
    _fake_llm(monkeypatch, av.GroundingCheck(["invented step"], True), av.GroundingCheck(["invented step"], True))
    result = _run("Invented step.", regenerate=lambda claims: "Still the invented step.")
    assert result.action == "replaced"
    assert result.reason == "not_grounded"
    assert result.answer == av.UNCONFIRMED_ANSWER


def test_rule_issue_triggers_repair_even_if_llm_sees_nothing(monkeypatch):
    _fake_llm(monkeypatch, av.GroundingCheck([], True), av.GroundingCheck([], True))
    seen = []
    result = _run("Terms are Net 45.", regenerate=lambda claims: seen.append(claims) or "Terms such as Net 30.")
    assert result.action == "repaired"
    assert seen and "45" in seen[0][0]


def test_repair_that_fails_is_replaced(monkeypatch):
    _fake_llm(monkeypatch, av.GroundingCheck(["made up"], True))

    def broken(claims):
        raise RuntimeError("LLM down")

    result = _run("Made up.", regenerate=broken)
    assert result.action == "replaced"


def test_llm_down_with_clean_rules_is_unverified(monkeypatch):
    _fake_llm(monkeypatch, RuntimeError("timeout"))
    result = _run(GOOD)
    assert (result.action, result.answer, result.llm_checked) == ("unverified", GOOD, False)


def test_llm_down_uses_not_found_phrases(monkeypatch):
    _fake_llm(monkeypatch, RuntimeError("timeout"))
    result = _run("Sorry, that is not provided in the available information.")
    assert result.action == "not_found"


def test_llm_down_still_repairs_rule_issues(monkeypatch):
    _fake_llm(monkeypatch, RuntimeError("timeout"), RuntimeError("timeout"))
    result = _run("I have released the credit hold for you.", regenerate=lambda claims: GOOD)
    assert result.action == "unverified"  # fixed, but only the rule checks could confirm it
    assert result.answer == GOOD


def test_validation_can_be_switched_off(monkeypatch):
    monkeypatch.setattr(settings, "answer_validation_enabled", False)
    _fake_llm(monkeypatch)
    result = _run(GOOD)
    assert result.action == "unverified"
    assert result.reason == "validation_disabled"


def test_trace_has_labels_only(monkeypatch):
    _fake_llm(monkeypatch, av.GroundingCheck(["secret step text"], True), av.GroundingCheck([], True))
    trace = _run("x", regenerate=lambda c: GOOD).trace()
    assert trace == {"validation": "repaired", "validation_llm_checked": True, "unsupported_claim_count": 1}
    assert "secret step text" not in str(trace)
