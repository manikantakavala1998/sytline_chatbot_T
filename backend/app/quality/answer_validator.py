"""Answer validation (Phase 5, step 1) — the hallucination guard.

Every generated answer is checked against the evidence it was generated from
before the user sees it. Curated Excel answers shown word for word are
SME-approved and skip this check; so do fixed templates (greetings, blocks).

Two layers:
  1. Rule checks (always run, no LLM): leaked secrets / prompt text, claims
     that the bot changed something in SyteLine (it is read-only), and
     numbers that do not appear in the evidence.
  2. Grounding check (ANSWER_VALIDATION_MODEL, default gpt-4.1, JSON): lists
     invented forms, fields, buttons, numbers, rules or behaviour — things the
     evidence does not contain — and says whether the answer answers the
     question. gpt-4.1-mini was measured too literal (it rejected steps the
     documents clearly support), so the stronger model is the default.

Outcome:
  passed     — nothing unsupported; answer sent as is.
  repaired   — unsupported claims found; answer regenerated once without
               them and the new draft passed.
  replaced   — still unsupported after the repair (or unsafe): a safe
               "I couldn't confirm this" message is sent instead.
  not_found  — the evidence does not answer the question; the reply is the
               model's polite "not available" text and the route becomes
               NO_ANSWER so it is counted as an unanswered question.
  unverified — the grounding LLM was unavailable; rule checks passed, so the
               answer is sent and the trace says it was not LLM-verified.
"""

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable

from openai import OpenAI

from backend.app.config import settings
from backend.app.monitoring.usage import metered_create
from backend.app.rag.answer_service import build_context
from backend.app.rag.markdown_processor import MarkdownChunk
from backend.app.utils import trace as rt  # "rt" = request trace; ValidationResult has its own .trace()
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

UNCONFIRMED_ANSWER = (
    "I found related information, but I couldn’t confirm every detail of the answer against the "
    "approved documents, so I won’t guess. Try naming the specific form, field, or step you’re "
    "working on, or contact your SyteLine support team."
)
UNSAFE_ANSWER = "I can’t share that response. Please rephrase your question about the SyteLine process."
LEAK_REASONS = ("secret_pattern", "prompt_text")

# ── Rule checks ────────────────────────────────────────────────────────

SECRET_PATTERNS = _SECRET_PATTERNS = [
    re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"),  # OpenAI-style key
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{20,}", re.IGNORECASE),
    re.compile(r"\b(?:password|passwd|api[_\s-]?key|secret)\s*[:=]\s*\S{4,}", re.IGNORECASE),
]
# Text that only exists in our own prompts — seeing it in an answer means the prompt leaked.
_PROMPT_MARKERS = ("retrieved context:", "answer only using the", "[source:", "never use outside knowledge")

# The assistant is read-only: an answer must never say it changed something.
_ACTION_CLAIM = re.compile(
    r"\b(?:I(?:\s+have|'ve|’ve)?|we(?:\s+have|'ve|’ve)?)\s+(?:just\s+|now\s+|successfully\s+)?"
    r"(?:created|updated|posted|deleted|removed|released|approved|changed|submitted|cancell?ed|"
    r"shipped|invoiced|converted|applied|saved|entered|booked|placed)\b"
    r"|\b(?:has|have)\s+been\s+(?:created|updated|posted|deleted|released|approved|changed|submitted|"
    r"cancell?ed|shipped|invoiced|converted|applied|saved)\s+for\s+you\b",
    re.IGNORECASE,
)

_NUMBER = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?%?")
_LIST_MARKER = re.compile(r"^\s*\d+[.)]\s", re.MULTILINE)

# "The documents don't answer this" wording. Checked together with the grounding LLM's
# answers_question flag, because the small model sometimes calls a polite refusal an answer.
_NOT_FOUND = re.compile(
    r"\b(?:does not|doesn't|do not|don't|did not)\s+(?:provide|include|contain|cover|describe|detail|"
    r"mention|specify|explain)\b"
    r"|\bno (?:specific |detailed )?information (?:is )?(?:available|provided|about|on|here)\b"
    r"|\b(?:is|are)\s+not\s+(?:provided|included|detailed|described|covered|available|specified)\b"
    r"|\b(?:isn't|aren't)\s+(?:provided|included|covered|available)\b"
    r"|\bI don't have (?:the |any |specific )?(?:information|details|steps)\b",
    re.IGNORECASE,
)
_LIST_LINE = re.compile(r"^\s*(?:\d+[.)]|[-*•])\s+\S", re.MULTILINE)


def _find_leak(answer: str) -> str | None:
    lowered = answer.casefold()
    if any(p.search(answer) for p in _SECRET_PATTERNS):
        return "secret_pattern"
    if any(marker in lowered for marker in _PROMPT_MARKERS):
        return "prompt_text"
    return None


def _normalize_number(token: str) -> str:
    return token.replace(",", "").rstrip("%").rstrip(".")


def unsupported_numbers(answer: str, question: str, evidence: str) -> list[str]:
    """Numbers in the answer that appear neither in the evidence nor in the question.

    Single digits and list markers ("1. ", "2) ") are ignored: step numbering and
    "one or two" style counts are not facts that can be looked up.
    """
    body = _LIST_MARKER.sub(" ", answer)
    known = {_normalize_number(n) for n in _NUMBER.findall(evidence + " " + question)}
    missing: list[str] = []
    for token in _NUMBER.findall(body):
        value = _normalize_number(token)
        if len(value.replace(".", "")) < 2:
            continue
        if value not in known and token not in missing:
            missing.append(token)
    return missing


def action_claims(answer: str) -> list[str]:
    return [m.group(0) for m in _ACTION_CLAIM.finditer(answer)]


def looks_not_found(answer: str) -> bool:
    """A reply that says the information isn't available and gives no real steps of its own.

    "The steps aren't provided, but here is how X works: 1. ... 2. ..." is still an answer.
    """
    text = answer.replace("’", "'")
    return bool(_NOT_FOUND.search(text)) and len(_LIST_LINE.findall(text)) < 2


def rule_issues(answer: str, question: str, evidence: str) -> list[str]:
    issues = [f"number not in the documents: {n}" for n in unsupported_numbers(answer, question, evidence)]
    issues += [f"claims a SyteLine change was made: “{c}”" for c in action_claims(answer)]
    return issues


# ── Grounding check (LLM) ──────────────────────────────────────────────

GROUNDING_PROMPT = """You check a SyteLine assistant's answer against the EVIDENCE it was given.

Your job is to catch INVENTED facts, not to demand word-for-word steps. List a claim only if it
  (a) names a form, field, button, menu path, report, utility, status or setting that appears
      NOWHERE in the evidence, or
  (b) states a number, limit, rule or system behaviour the evidence does not state, or
  (c) contradicts the evidence.
SUPPORTED (never list): rewording or summarising the evidence; using a form, field, report or
utility the evidence names for the purpose the evidence describes (e.g. evidence "the Opportunities
form holds status and won/lost reason" supports "update the status and record the lost reason on the
Opportunities form"); generic actions like open, find the record, enter, save; greetings,
politeness, offers to help, suggestions of what to ask next, and saying information is not available.
When in doubt, treat it as supported.

Also decide whether the answer actually answers the QUESTION. If the answer mainly says the
information is not available / not covered, "answers_question" is false.

Return JSON only:
{"unsupported_claims": ["<short quote or paraphrase>", ...], "answers_question": true|false}"""

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.openai_api_key, timeout=settings.orchestrator_timeout_seconds, max_retries=1)
    return _client


@dataclass
class GroundingCheck:
    unsupported_claims: list[str]
    answers_question: bool


def llm_grounding_check(question: str, answer: str, evidence: str) -> GroundingCheck:
    response = metered_create("grounding_check", _get_client(),
        model=settings.answer_validation_model,
        temperature=0,
        max_tokens=300,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": GROUNDING_PROMPT},
            {"role": "user", "content": f"EVIDENCE:\n{evidence}\n\nQUESTION: {question}\n\nANSWER:\n{answer}"},
        ],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    claims = payload.get("unsupported_claims") or []
    if not isinstance(claims, list):
        claims = [str(claims)]
    return GroundingCheck(
        unsupported_claims=[str(c).strip() for c in claims if str(c).strip()][:8],
        answers_question=bool(payload.get("answers_question", True)),
    )


# ── Orchestration ──────────────────────────────────────────────────────


@dataclass
class ValidationResult:
    action: str  # passed | repaired | replaced | not_found | unverified
    answer: str
    unsupported_claims: list[str] = field(default_factory=list)
    reason: str | None = None
    llm_checked: bool = True

    def trace(self) -> dict[str, object]:
        """Safe summary for the decision trace (labels and counts, no answer text)."""
        return {
            "validation": self.action,
            "validation_llm_checked": self.llm_checked,
            "unsupported_claim_count": len(self.unsupported_claims),
            **({"validation_reason": self.reason} if self.reason else {}),
        }


def _check(question: str, answer: str, evidence: str, request_id: str) -> tuple[list[str], bool, bool]:
    """Returns (issues, answers_question, llm_checked)."""
    issues = rule_issues(answer, question, evidence)
    refusal = looks_not_found(answer)
    rt.detail(f"    rules: numbers not in the evidence / 'I changed it' claims → "
              + ("none" if not issues else f"{len(issues)} issue(s): " + "; ".join(rt.clean(i, 90) for i in issues)))
    if refusal:
        rt.detail("    rules: the draft says the information is not available")
    started = time.perf_counter()
    try:
        grounding = llm_grounding_check(question, answer, evidence)
    except Exception as exc:
        logger.warning("event=answer_grounding_check_failed request_id=%s action=rules_only", request_id)
        rt.detail(f"    grounding check ({settings.answer_validation_model}) unavailable: {type(exc).__name__} "
                  "— rules only")
        return issues, not refusal, False
    claims = grounding.unsupported_claims
    rt.detail(f"    grounding check ({settings.answer_validation_model}, {time.perf_counter() - started:.1f}s): "
              + ("every statement is backed by the evidence" if not claims
                 else f"{len(claims)} statement(s) NOT in the evidence:"))
    for claim in claims:
        rt.detail(f"      ✗ {rt.text(claim, 150)}")
    rt.detail(f"    answers the question: {'yes' if grounding.answers_question and not refusal else 'no'}")
    return issues + claims, grounding.answers_question and not refusal, True


def validate_answer(
    question: str,
    answer: str,
    chunks: list[MarkdownChunk],
    request_id: str,
    regenerate: Callable[[list[str]], str],
) -> ValidationResult:
    """Check a generated answer against its evidence; repair once, else replace it."""
    rt.detail("▸ cross-check the draft against the evidence (hallucination guard)")
    leak = _find_leak(answer)
    if leak:
        log_event(logger, "answer_validation", request_id=request_id, action="replaced", reason=leak)
        rt.detail(f"    ⛔ the draft contains {leak.replace('_', ' ')} → replaced with a safe message")
        return ValidationResult(action="replaced", answer=UNSAFE_ANSWER, reason=leak, llm_checked=False)

    if not settings.answer_validation_enabled:
        rt.detail("    switched off (ANSWER_VALIDATION_ENABLED=false) → sent unchecked")
        return ValidationResult(action="unverified", answer=answer, reason="validation_disabled", llm_checked=False)

    evidence = build_context(chunks)
    issues, answers_question, llm_checked = _check(question, answer, evidence, request_id)

    if not answers_question and not issues:
        log_event(logger, "answer_validation", request_id=request_id, action="not_found", llm_checked=llm_checked)
        rt.detail("    result: NOT FOUND — the documents don't answer this; counted as a content gap")
        return ValidationResult(action="not_found", answer=answer, llm_checked=llm_checked)

    if not issues:
        action = "passed" if llm_checked else "unverified"
        log_event(logger, "answer_validation", request_id=request_id, action=action, llm_checked=llm_checked)
        rt.detail(f"    result: {'PASSED' if llm_checked else 'UNVERIFIED (rules only)'} — sent as written")
        return ValidationResult(action=action, answer=answer, llm_checked=llm_checked)

    rt.detail(f"    result: {len(issues)} unsupported statement(s) → write the answer again without them")

    log_event(logger, "answer_validation_repair_started", request_id=request_id, issues=len(issues))
    # Flagged text comes from the answer (knowledge-base wording), never from secrets — those were
    # replaced above. Logged locally so the checker can be tuned; never put in the API trace.
    logger.info("event=answer_validation_flagged request_id=%s claims=%s", request_id, json.dumps(issues)[:600])
    try:
        repaired = regenerate(issues)
    except Exception:
        logger.exception("event=answer_repair_failed request_id=%s", request_id)
        repaired = ""

    if repaired and not _find_leak(repaired):
        rt.detail("▸ cross-check the re-written answer")
        remaining, answers_question, llm_checked = _check(question, repaired, evidence, request_id)
        if not remaining:
            if not answers_question:
                action = "not_found"
            else:
                action = "repaired" if llm_checked else "unverified"
            log_event(logger, "answer_validation", request_id=request_id, action=action, fixed=len(issues))
            rt.detail(f"    result: {action.upper()} — the re-written answer is clean and is sent")
            return ValidationResult(action=action, answer=repaired, unsupported_claims=issues, llm_checked=llm_checked)
        issues = remaining

    log_event(logger, "answer_validation", request_id=request_id, action="replaced", reason="not_grounded",
              issues=len(issues))
    rt.detail("    result: REPLACED — still not backed by the evidence; the user gets “I couldn't confirm this” "
              "instead of a guess")
    return ValidationResult(
        action="replaced", answer=UNCONFIRMED_ANSWER, unsupported_claims=issues, reason="not_grounded",
        llm_checked=llm_checked,
    )
