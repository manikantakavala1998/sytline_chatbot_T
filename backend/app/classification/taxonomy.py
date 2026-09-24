"""Shared Phase 3 classification taxonomy.

The taxonomy is intentionally hierarchical instead of a flat list of
hundreds of intents.  These values are the stable contract between the
security, ambiguity, classification, routing, orchestration, API, and
future SLM-training layers.
"""

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class SecurityLabel(str, Enum):
    SAFE = "SEC_SAFE"
    PROMPT_INJECTION = "SEC_PROMPT_INJECTION"
    PERMISSION_BYPASS = "SEC_PERMISSION_BYPASS"
    SOCIAL_ENGINEERING = "SEC_SOCIAL_ENGINEERING"
    OBFUSCATED_ATTACK = "SEC_OBFUSCATED_ATTACK"
    TOOL_ABUSE = "SEC_TOOL_ABUSE"
    DATA_EXFILTRATION = "SEC_DATA_EXFILTRATION"
    CREDENTIAL_REQUEST = "SEC_CREDENTIAL_REQUEST"
    MALICIOUS_INSTRUCTION = "SEC_MALICIOUS_INSTRUCTION"


class ScopeLabel(str, Enum):
    SYTELINE_RELATED = "SYTELINE_RELATED"
    OFF_TOPIC = "OFF_TOPIC"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    COMPETITOR_OTHER_ERP = "COMPETITOR_OTHER_ERP"
    IRRELEVANT = "IRRELEVANT"


class IntentLabel(str, Enum):
    GREETING = "GREETING"
    CHITCHAT = "CHITCHAT"
    HELP_GENERIC = "HELP_GENERIC"
    HELP_SCREEN = "HELP_SCREEN"
    HELP_FIELD = "HELP_FIELD"
    HELP_PROCESS = "HELP_PROCESS"
    TROUBLESHOOTING = "TROUBLESHOOTING"
    LIVE_DATA = "LIVE_DATA"
    NAVIGATION = "NAVIGATION"
    ACTION = "ACTION"
    ANALYSIS = "ANALYSIS"
    FEEDBACK = "FEEDBACK"
    COMPLAINT = "COMPLAINT"
    SECURITY_HELP = "SECURITY_HELP"
    MIXED = "MIXED"
    UNKNOWN = "UNKNOWN"


class AmbiguityLabel(str, Enum):
    CLEAR = "A0_CLEAR"
    MISSING_TOPIC = "A1_MISSING_TOPIC"
    MISSING_DETAIL = "A2_MISSING_DETAIL"
    CONTRADICTORY = "A3_CONTRADICTORY"
    VERSION_RECENCY = "A4_VERSION_RECENCY"
    REFERENTIAL = "A5_REFERENTIAL_AMBIGUITY"
    MULTIPLE_ENTITY = "A6_MULTIPLE_ENTITY_MATCH"
    UNANSWERABLE = "A7_UNANSWERABLE"


class ComplexityLabel(str, Enum):
    DIRECT = "DIRECT"
    SYNONYM_VARIATION = "SYNONYM_VARIATION"
    CONTEXT_SHIFT = "CONTEXT_SHIFT"
    CONCEPT_MAPPING = "CONCEPT_MAPPING"
    CONSTRAINT_BASED = "CONSTRAINT_BASED"
    NEGATIVE_EXCEPTION = "NEGATIVE_EXCEPTION"
    PROCESS_WORKFLOW = "PROCESS_WORKFLOW"
    HYPOTHETICAL = "HYPOTHETICAL"
    REVERSE_LOGIC = "REVERSE_LOGIC"
    MULTI_PART = "MULTI_PART"
    COMPARISON = "COMPARISON"
    ROOT_CAUSE = "ROOT_CAUSE"
    CALCULATION = "CALCULATION"


class EmotionLabel(str, Enum):
    NORMAL = "F0_NORMAL"
    CONFUSED = "F1_CONFUSED"
    COMPLAINT = "F2_COMPLAINT"
    FRUSTRATED = "F3_FRUSTRATED"
    PERSISTENT = "F4_PERSISTENT"


class RouteLabel(str, Enum):
    BLOCK = "BLOCK"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"
    CLARIFY = "CLARIFY"
    DIRECT_RESPONSE = "DIRECT_RESPONSE"
    FAST_QA = "FAST_QA"
    MARKDOWN_RAG = "MARKDOWN_RAG"
    LIVE_DATA = "LIVE_DATA"
    RAG_IDO = "RAG_IDO"
    NAVIGATION = "NAVIGATION"
    ACTION = "ACTION"
    LLM_REASONING = "LLM_REASONING"


class SecurityResult(BaseModel):
    label: SecurityLabel = SecurityLabel.SAFE
    allowed: bool = True
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = "safe"
    signals: list[str] = Field(default_factory=list)


class ScopeResult(BaseModel):
    label: ScopeLabel
    in_scope: bool
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str


class AmbiguityResult(BaseModel):
    label: AmbiguityLabel = AmbiguityLabel.CLEAR
    resolved: bool = True
    resolved_query: str | None = None
    clarification_question: str | None = None
    reason: str = "clear"


class QueryTransformResult(BaseModel):
    normalized_query: str
    rewritten_query: str
    expanded_query: str
    entities: dict[str, list[str]] = Field(default_factory=dict)
    subqueries: list[str] = Field(default_factory=list)
    # Retrieval-ready (glossary-expanded) version of each sub-question, searched separately.
    expanded_subqueries: list[str] = Field(default_factory=list)
    # "good_morning", "hi", ... when the message opened with a greeting before the real question.
    leading_greeting: str | None = None
    transformations: list[str] = Field(default_factory=list)


class QueryClassification(BaseModel):
    intent: IntentLabel = IntentLabel.UNKNOWN
    sub_intent: str | None = None
    module: str | None = None
    form: str | None = None
    field: str | None = None
    entity: str | None = None
    operation: str = "READ"
    complexity: ComplexityLabel = ComplexityLabel.DIRECT
    emotion: EmotionLabel = EmotionLabel.NORMAL
    route: RouteLabel = RouteLabel.MARKDOWN_RAG
    tool_candidate: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reasoning_summary: str = "fallback classification"

    # The LLM classifier returns null for `operation` on plain questions and a
    # list for `entity` on multi-object questions; both used to fail validation
    # and silently drop the request to the heuristic fallback.
    @field_validator("operation", mode="before")
    @classmethod
    def _default_operation(cls, value):
        return value or "READ"

    @field_validator("entity", mode="before")
    @classmethod
    def _join_entities(cls, value):
        if isinstance(value, list):
            return ", ".join(str(item) for item in value) or None
        return value

