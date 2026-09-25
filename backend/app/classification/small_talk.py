"""
One shared definition of greetings and small talk, used by scope, query
transformation, classification, follow-up resolution and the direct-response
node — so they can never disagree about what "good morning buddy" is.

Handles the variations real users type:
  time of day      good morning / gud mrng / gm / morning / good evening / good night
  casual forms     hi / hii / hiya / hello / helo / hey / heyyy / yo / howdy / namaste
  who they greet   buddy / bro / team / everyone / there / sir / friend / bot ...
  pleasantries     how are you (doing) / how's it going / hope you are well ...
  noise            any case, punctuation, emoji ("Good Morning!!! 😊")

A pure greeting is answered directly. A greeting in front of a real question
("good morning buddy, what is a lead?") is stripped before search and echoed
back in the answer.
"""

import re
from dataclasses import dataclass

_SEP = r"[\s,!.?:;~\-]+"

_FULL_GREETINGS = (
    r"(?:good|gud|gd)\s?(?:morning|mornin|mrng|morng|mng)|gm"
    r"|(?:good|gud|gd)\s?(?:afternoon|aftrnoon|afternun|noon)"
    r"|(?:good|gud|gd)\s?(?:evening|evng|evenin|eve)"
    r"|(?:good|gud|gd)\s?(?:night|nite|nyt)"
    r"|good\s?day|greetings|namaste|howdy|hiya|hola"
    r"|h+i+|he+y+|hel+o+w?|hai"
)
# Bare "morning" / "evening" / "yo" are greetings only when they are the whole message —
# in front of other words ("morning shipment schedule") they are part of the question.
_GREETING = rf"(?P<greet>{_FULL_GREETINGS}|morning|afternoon|evening|yo)(?![\w'])"
_LEADING_GREETING_WORD = rf"(?P<greet>{_FULL_GREETINGS})(?![\w'])"
_ADDRESSEE = (
    r"(?:(?:my|dear)\s)?"
    r"(?:there|team|everyone|every\sone|everybody|all|y'?all|folks|guys|buddy|bud|bro|brother|sis|friend|"
    r"mate|pal|man|sir|madam|ma'?am|mam|dear|bot|chatbot|assistant|champ|boss)(?![\w'])"
)
_WELLBEING = (
    r"(?:how\s(?:are|r)\s(?:you|u|ya)(?:\s(?:doing|keeping))?(?:\s(?:today|now|there))?"
    r"|hru|how'?s\s(?:it\sgoing|your\sday|everything|life)|how\sis\s(?:it\sgoing|your\sday|everything|life)"
    r"|how\sare\sthings|how\shave\syou\sbeen|how\sdo\syou\sdo|what'?s\sup|wassup|sup"
    r"|hope\s(?:you'?re|you\sare|u\sr|you\sare\sdoing|you'?re\sdoing)\s(?:doing\s)?(?:well|good|fine|great|ok|okay))"
    r"(?![\w'])"
)

_PURE_GREETING = re.compile(
    rf"^\s*{_GREETING}(?:{_SEP}{_ADDRESSEE})?(?:{_SEP}(?P<wellbeing>{_WELLBEING}))?(?:{_SEP}{_ADDRESSEE})?[\s,!.?:;~\-]*$",
    re.IGNORECASE,
)
# No "-" / "~" as separators here, so "hi-tech customers" keeps its first word.
_LEAD_SEP = r"[\s,!.?:;]+"
_LEADING_GREETING = re.compile(
    rf"^\s*{_LEADING_GREETING_WORD}(?:{_LEAD_SEP}{_ADDRESSEE})?(?:{_LEAD_SEP}(?P<wellbeing>{_WELLBEING}))?"
    rf"(?:{_LEAD_SEP}{_ADDRESSEE})?{_LEAD_SEP}(?=\S)",
    re.IGNORECASE,
)

# Small talk without a greeting word. Order matters: first match wins.
_CHITCHAT_RULES: list[tuple[str, str]] = [
    ("casual_checkin", r"what'?s\s?up|wassup|sup"),
    ("wellbeing", rf"{_WELLBEING}(?:{_SEP}{_ADDRESSEE})?|are\s(?:you|u)\s(?:ok|okay|well|good|fine|doing\swell)"),
    ("thanks", r"(?:ok(?:ay)?\s|great\s|cool\s)?(?:thanks?|thank\s?(?:you|u)|thx|ty|tnx|many\sthanks|much\sappreciated|appreciate\sit)"
               r"(?:\s(?:so\smuch|a\slot|a\ston|very\smuch|again|for\s(?:the|your)\s(?:help|answer|info)))?"),
    ("farewell", r"(?:bye+|goodbye|good\sbye|bye\sbye|see\s(?:you|ya|u)(?:\s(?:later|soon|tomorrow))?|take\scare|"
                 r"catch\syou\slater|talk\s(?:to\syou\s)?later|ttyl|have\sa\s(?:good|nice|great)\s(?:day|one|evening|weekend))"),
    ("identity", r"who\sare\s(?:you|u)|what\sare\s(?:you|u)|what(?:'s|\sis)\syour\sname"),
    ("capabilities", r"what\scan\s(?:you|u)\sdo|how\scan\s(?:you|u)\shelp(?:\sme)?|what\sdo\s(?:you|u)\sdo"),
    ("introduction", r"nice\sto\smeet\s(?:you|u)|pleased\sto\smeet\s(?:you|u)"),
    ("acknowledgement", r"ok(?:ay)?|k|cool|great|nice|perfect|got\sit|sounds\sgood|alright|all\sright|fine|noted|understood"),
]
_CHITCHAT = [
    (name, re.compile(rf"^\s*(?:{pattern})(?:{_SEP}{_ADDRESSEE})?[\s,!.?:;~\-]*$", re.IGNORECASE))
    for name, pattern in _CHITCHAT_RULES
]

# Emoji and pictographs carry no meaning for search; drop them before matching.
_EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍]+")


@dataclass(frozen=True)
class Greeting:
    key: str  # good_morning | good_afternoon | good_evening | good_night | hello
    wellbeing: bool  # the user also asked how we are


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", _EMOJI.sub(" ", text.replace("’", "'"))).strip()


def _greeting_key(greet: str) -> str:
    g = greet.lower()
    if g == "gm" or "morn" in g or "mrng" in g or "mng" in g:
        return "good_morning"
    if "noon" in g or "aftr" in g:
        return "good_afternoon"
    if "even" in g or "evng" in g or g.endswith("eve"):
        return "good_evening"
    if "night" in g or "nite" in g or "nyt" in g:
        return "good_night"
    return "hello"


def parse_greeting(text: str) -> Greeting | None:
    """The whole message is a greeting (optionally + addressee + "how are you")."""
    match = _PURE_GREETING.match(clean(text))
    if not match:
        return None
    return Greeting(key=_greeting_key(match.group("greet")), wellbeing=bool(match.group("wellbeing")))


def strip_leading_greeting(text: str) -> tuple[str, Greeting | None]:
    """"Good morning buddy, what is a lead?" -> ("what is a lead?", good_morning).
    Only strips when a real question of at least 2 words remains."""
    cleaned = clean(text)
    match = _LEADING_GREETING.match(cleaned)
    if not match:
        return text, None
    remainder = cleaned[match.end():].strip()
    if len(remainder.split()) < 2 or parse_greeting(remainder) or chitchat_kind(remainder):
        return text, None
    return remainder, Greeting(key=_greeting_key(match.group("greet")), wellbeing=bool(match.group("wellbeing")))


def chitchat_kind(text: str) -> str | None:
    """wellbeing / thanks / farewell / identity / capabilities / introduction / acknowledgement."""
    cleaned = clean(text)
    for name, pattern in _CHITCHAT:
        if pattern.match(cleaned):
            return name
    return None


def is_small_talk(text: str) -> bool:
    return parse_greeting(text) is not None or chitchat_kind(text) is not None


def greeting_key_from_label(label: str | None) -> str | None:
    """Map a free-form classifier label (GREETING_MORNING, good morning, ...) to a greeting key."""
    if not label:
        return None
    key = _greeting_key(label.replace("_", " "))
    return key if key != "hello" else None
