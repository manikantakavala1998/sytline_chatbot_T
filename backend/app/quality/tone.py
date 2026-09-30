"""Tone manager (Phase 5, step 2) — answer in a way that fits the user's mood.

Mood levels (master prompt "Frustration / Emotion Classes"):
  F0 NORMAL      plain, concise answer
  F1 CONFUSED    simpler words, short numbered steps, offer to explain more
  F2 COMPLAINT   one short acknowledgement, then the solution
  F3 FRUSTRATED  calm, one empathy sentence, most likely fix first (+ ticket offer)
  F4 PERSISTENT  acknowledge it's still unresolved, don't repeat the same generic steps,
                 give the next diagnostic step (+ ticket offer)

Mood may change TONE, explanation style and (via escalation/policy.py) the ticket offer only. It never changes
facts (the answer validator still checks every claim), security, or permissions: blocked,
out-of-scope and clarification templates are not touched.

Where the mood comes from: the conversation-understanding LLM reads the user's raw message
and the conversation (the classifier only sees the cleaned-up question, which has lost the
"!!!", CAPS and "still"), plus the rules below as a floor for obvious signals and the
fallback when the LLM is down. The strongest reading wins.
"""

import re

from backend.app.classification.taxonomy import EmotionLabel
from backend.app.history.store import Turn
from backend.app.utils.search_tokens import search_tokens

SEVERITY = {
    EmotionLabel.NORMAL: 0,
    EmotionLabel.CONFUSED: 1,
    EmotionLabel.COMPLAINT: 2,
    EmotionLabel.FRUSTRATED: 3,
    EmotionLabel.PERSISTENT: 4,
}
REPEAT_SIMILARITY = 0.75


def strongest(*moods: EmotionLabel | None) -> EmotionLabel:
    present = [m for m in moods if m is not None]
    return max(present, key=SEVERITY.__getitem__, default=EmotionLabel.NORMAL)


# ── Rules (floor + offline fallback) ───────────────────────────────────

# "still"/"again" only count when they are about the user's problem not being solved —
# "customer paid but invoice still open" is a normal question.
_PERSISTENT = re.compile(
    r"\b(?:still|again)\s+(?:not|no|doesn't|does not|isn't|is not|can't|cannot|won't|didn't|"
    r"the same|getting|having|stuck|failing|broken|same)\b"
    r"|\b(?:asked|told|tried|said)\s+(?:you\s+)?(?:this\s+|that\s+|it\s+)?(?:already|before|twice|again)\b"
    r"|\balready\s+(?:asked|told|tried|did that|done that)\b"
    r"|\b(?:second|third|fourth|fifth|2nd|3rd|4th|5th)\s+time\b"
    r"|\bkeeps?\s+(?:happening|failing|coming back|giving)\b"
    r"|\bsame\s+(?:issue|problem|error|answer)\s+again\b"
    r"|\bnot\s+(?:working|solved|fixed|resolved)\s+(?:yet|still)\b",
    re.IGNORECASE,
)
_FRUSTRATED = re.compile(
    r"\b(?:useless|ridiculous|terrible|horrible|stupid|pathetic|worst|annoying|annoyed|furious|angry|"
    r"damn|wtf|fed up|sick of|waste of time|nonsense|rubbish|hate)\b",
    re.IGNORECASE,
)
_COMPLAINT = re.compile(
    r"\b(?:complaint|complain|unacceptable|not satisfied|dissatisfied|disappointed|not happy|unhappy|"
    r"poor service|not helpful|unhelpful|wrong answer|doesn't help|didn't help)\b",
    re.IGNORECASE,
)
_CONFUSED = re.compile(
    r"\b(?:confused|confusing|don't understand|do not understand|didn't understand|not clear|unclear|"
    r"not sure|makes no sense|what does (?:that|this|it) mean|i'm lost|im lost|lost here)\b"
    r"|\?{3,}",
    re.IGNORECASE,
)


def _shouting(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 12 and sum(c.isupper() for c in letters) / len(letters) >= 0.7


_FILLER = set(search_tokens(
    "a an the i me my we you your it this that is are was do does did how what why when where which "
    "who can could should would to of in on for and or with please pls again still now so"
))


def topic_tokens(text: str) -> set[str]:
    """The words that say what a question is about (stemmed, filler removed). Also used by the
    feedback console to group unanswered questions by topic."""
    return set(search_tokens(text)) - _FILLER


def _repeats_earlier_question(text: str, history: list[Turn]) -> bool:
    """The user asks (nearly) the same question they already asked in this conversation."""
    current = topic_tokens(text)
    if len(current) < 3:
        return False
    for turn in history:
        earlier = topic_tokens(turn.question)
        if len(earlier) >= 3 and len(current & earlier) / len(current | earlier) >= REPEAT_SIMILARITY:
            return True
    return False


def rules_mood(text: str, history: list[Turn] | None = None) -> EmotionLabel:
    normalized = text.replace("’", "'")
    if _PERSISTENT.search(normalized) or (history and _repeats_earlier_question(normalized, history)):
        return EmotionLabel.PERSISTENT
    if _FRUSTRATED.search(normalized) or _shouting(normalized) or "!!" in normalized:
        return EmotionLabel.FRUSTRATED
    if _COMPLAINT.search(normalized):
        return EmotionLabel.COMPLAINT
    if _CONFUSED.search(normalized):
        return EmotionLabel.CONFUSED
    return EmotionLabel.NORMAL


# ── Applying the tone ──────────────────────────────────────────────────

# Added to the answer model's system prompt. Style only — the grounding rules stay first.
_INSTRUCTIONS = {
    EmotionLabel.CONFUSED: (
        "The user is confused. Use plain words, explain any SyteLine term the first time you use it, "
        "and give short numbered steps with one action each. End by offering to explain any step in "
        "more detail."
    ),
    EmotionLabel.COMPLAINT: (
        "The user is unhappy. Start with ONE short, sincere acknowledgement (no over-apologising, "
        "no blaming the user), then go straight to the solution."
    ),
    EmotionLabel.FRUSTRATED: (
        "The user is frustrated. Stay calm and respectful. Start with ONE short empathy sentence, "
        "then give the most likely fix first, in as few steps as possible. No filler, no "
        "exclamation marks."
    ),
    EmotionLabel.PERSISTENT: (
        "The user has had this problem before and it is still not solved. Acknowledge that in one "
        "short sentence. Do not just repeat generic steps: lead with the most likely cause and the "
        "next thing to check, then any remaining checks. Keep it short and calm."
    ),
}

# For text that must not be rewritten (SME-approved Excel answers, "not found" replies).
_PREFIX = {
    EmotionLabel.CONFUSED: "No problem — here it is step by step.",
    EmotionLabel.COMPLAINT: "Sorry about the trouble.",
    EmotionLabel.FRUSTRATED: "I’m sorry this is getting in your way — here’s what to do.",
    EmotionLabel.PERSISTENT: "Sorry this still isn’t sorted — let’s look at it again.",
}
# The support / ticket offer for F3/F4 is added by the API from the escalation decision
# (escalation/policy.py), because only the API knows whether a ticket can be stored right now.


def tone_instruction(mood: EmotionLabel) -> str | None:
    return _INSTRUCTIONS.get(mood)


GENERATED = "generated"  # the answer model already wrote it in the right tone
APPROVED = "approved"  # SME-approved text that must stay word for word
NOT_FOUND = "not_found"  # "I couldn't find / confirm that" replies


def apply_tone(answer: str | None, mood: EmotionLabel, kind: str) -> str | None:
    """Fit an answer to the mood without touching its facts.

    APPROVED text gets a short opener in front and is otherwise left exactly as approved.
    GENERATED and NOT_FOUND text get no opener ("here's what to do" in front of "I couldn't
    find that" reads wrong).
    """
    if not answer or mood == EmotionLabel.NORMAL:
        return answer
    if kind == APPROVED and mood in _PREFIX:
        answer = f"{_PREFIX[mood]}\n\n{answer}"
    return answer
