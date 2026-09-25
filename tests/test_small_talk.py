"""Greeting and small-talk edge cases — the shared detector (small_talk.py) and the
replies the orchestrator gives for them. No network calls: the LLM is disabled."""

import pytest

from backend.app.classification.query_transformer import transform_query
from backend.app.classification.small_talk import chitchat_kind, is_small_talk, parse_greeting
from backend.app.config import settings
from backend.app.orchestration.graph import ChatOrchestrator
from tests.test_phase3_orchestration import make_context, make_user


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    monkeypatch.setattr(settings, "orchestrator_llm_enabled", False)


@pytest.mark.parametrize(
    ("text", "key", "wellbeing"),
    [
        ("good morning buddy", "good_morning", False),
        ("Good Morning!!! 😊", "good_morning", False),
        ("gud mrng", "good_morning", False),
        ("goodmorning", "good_morning", False),
        ("gm", "good_morning", False),
        ("morning", "good_morning", False),
        ("good morning team, how are you?", "good_morning", True),
        ("good morning buddy how are you doing today", "good_morning", True),
        ("Good afternoon sir", "good_afternoon", False),
        ("good evening everyone", "good_evening", False),
        ("gud evng", "good_evening", False),
        ("good night", "good_night", False),
        ("hi", "hello", False),
        ("hiii", "hello", False),
        ("Hello there!", "hello", False),
        ("helo", "hello", False),
        ("heyyy bro", "hello", False),
        ("hey buddy, how's it going?", "hello", True),
        ("hi, hope you are doing well", "hello", True),
        ("hello my friend", "hello", False),
        ("yo", "hello", False),
        ("howdy", "hello", False),
        ("namaste", "hello", False),
        ("Hi bot", "hello", False),
    ],
)
def test_greeting_variants_are_recognised(text, key, wellbeing):
    greeting = parse_greeting(text)
    assert greeting is not None, text
    assert (greeting.key, greeting.wellbeing) == (key, wellbeing)


@pytest.mark.parametrize(
    "text",
    [
        "what is a lead?",
        "hierarchy of customer orders",
        "high credit limit",
        "hello world program",
        "morning shipment schedule",
        "good morning, what is a customer order?",  # greeting + real question is not pure small talk
        "heya what",  # not a greeting word we accept
    ],
)
def test_non_greetings_are_not_pure_greetings(text):
    assert parse_greeting(text) is None


@pytest.mark.parametrize(
    ("text", "kind"),
    [
        ("how are you", "wellbeing"),
        ("how r u buddy", "wellbeing"),
        ("hru", "wellbeing"),
        ("are you ok?", "wellbeing"),
        ("what's up", "casual_checkin"),
        ("thanks", "thanks"),
        ("thank you so much!", "thanks"),
        ("thanks buddy", "thanks"),
        ("thx", "thanks"),
        ("ok thanks", "thanks"),
        ("thanks for the help", "thanks"),
        ("bye", "farewell"),
        ("bye buddy", "farewell"),
        ("see you later", "farewell"),
        ("take care", "farewell"),
        ("have a nice day", "farewell"),
        ("goodbye", "farewell"),
        ("who are you", "identity"),
        ("what is your name?", "identity"),
        ("what can you do", "capabilities"),
        ("how can you help me", "capabilities"),
        ("nice to meet you", "introduction"),
        ("ok", "acknowledgement"),
        ("got it", "acknowledgement"),
        ("sounds good 👍", "acknowledgement"),
    ],
)
def test_chitchat_variants(text, kind):
    assert chitchat_kind(text) == kind


@pytest.mark.parametrize("text", ["what is a credit hold", "thanks, what is a lead?", "ok so how do I invoice"])
def test_questions_are_not_small_talk(text):
    assert not is_small_talk(text)


@pytest.mark.parametrize(
    ("query", "greeting", "wellbeing", "clean"),
    [
        ("good morning buddy, what is a lead?", "good_morning", False, "what is a lead?"),
        ("Hey team! How do I create a customer order?", "hello", False, "How do I create a customer order?"),
        ("gm, explain credit hold", "good_morning", False, "explain credit hold"),
        ("good morning, how are you? what is a quotation", "good_morning", True, "what is a quotation"),
        ("hi 😊 what is an invoice", "hello", False, "what is an invoice"),
        ("morning shipment schedule", None, False, "morning shipment schedule"),
        ("hi-tech customer list", None, False, "hi-tech customer list"),
    ],
)
def test_leading_greeting_stripped_before_search(query, greeting, wellbeing, clean):
    transformed = transform_query(query, make_context())
    assert transformed.leading_greeting == greeting
    assert transformed.leading_wellbeing == wellbeing
    assert transformed.rewritten_query == clean


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("good morning buddy", "Good morning! How can I help"),
        ("Good Morning!!! 😊", "Good morning! How can I help"),
        ("gud mrng bro", "Good morning! How can I help"),
        ("good morning buddy, how are you?", "Good morning! I’m doing well, thank you for asking! How can I help"),
        ("good afternoon sir", "Good afternoon! How can I help"),
        ("good evening team", "Good evening! How can I help"),
        ("good night", "Good night! I’ll be here"),
        ("hey buddy", "Hello! How can I help"),
        ("hi, how's it going?", "Hello! I’m doing well, thank you for asking!"),
        ("how are you buddy", "I’m doing well, thank you for asking!"),
        ("thanks bro", "You’re welcome."),
        ("bye buddy", "Goodbye!"),
        ("see you later", "Goodbye!"),
    ],
)
def test_direct_replies_for_edge_cases(query, expected):
    result = ChatOrchestrator().run(query, make_context(), make_user())
    assert result.route == "DIRECT_RESPONSE", (query, result.route)
    assert (result.answer or "").startswith(expected), (query, result.answer)


def test_scope_treats_greeting_variants_as_in_scope():
    from backend.app.classification.scope import classify_scope

    for text in ("good morning buddy", "heyyy bro", "thanks a lot", "bye buddy"):
        assert classify_scope(text, make_context()).in_scope, text
