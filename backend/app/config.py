"""
All app settings live here, loaded from the .env file.
If OPENAI_API_KEY is missing, this fails immediately on startup instead of
failing later in the middle of a chat request.
"""

import sys
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


BASE_DIR = get_base_dir()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,  # tests and code can still set fields by their Python name
    )

    openai_api_key: str

    @field_validator("openai_api_key")
    @classmethod
    def openai_api_key_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("OPENAI_API_KEY is blank — paste your real key into .env")
        return value

    primary_llm: str = "gpt-4.1"
    orchestrator_model: str = "gpt-4.1-mini"
    orchestrator_llm_enabled: bool = True
    orchestrator_timeout_seconds: float = 12.0
    temperature: float = 0.1
    max_tokens: int = 500
    # Phase 5 hallucination guard: check every generated answer against its evidence.
    answer_validation_enabled: bool = True
    # gpt-4.1-mini was measured too literal for this judgement (it flagged steps the documents
    # clearly support), so the grounding check uses the primary model.
    answer_validation_model: str = "gpt-4.1"

    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dim: int = 768

    # Logging (utils/trace.py). Show question / answer / document text in the step-by-step trace
    # (secrets are always masked) — turn off in production. LOG_TERMINAL: "trace" = clear steps
    # + warnings/errors in the terminal; "all" = also every technical event line.
    log_conversation_text: bool = True
    log_terminal: str = "trace"

    # Phase 6 — audit and monitoring.
    # Keep audit records this many days (older ones are purged at startup and daily).
    audit_retention_days: int = 365
    # Store the (secret-masked) question / a short answer preview in the audit record. Set the
    # answer preview off once live SyteLine data (Phase 4) can appear in answers.
    audit_store_question_text: bool = True
    audit_store_answer_preview: bool = True
    # USD per 1 million tokens, for the cost figures. Defaults are OpenAI list prices at the
    # time of writing — check against your invoice; override with MODEL_PRICES as JSON in .env.
    model_prices: dict[str, dict[str, float]] = {
        "gpt-4.1": {"input": 2.00, "output": 8.00},
        "gpt-4.1-mini": {"input": 0.40, "output": 1.60},
    }
    # Health alerts (checked every monitor_interval_seconds over the last alert_window_minutes).
    monitor_interval_seconds: int = 300
    alert_window_minutes: int = 15
    alert_min_requests: int = 10  # don't judge rates on fewer requests than this
    alert_error_rate_pct: float = 5.0
    alert_p95_latency_seconds: float = 25.0
    alert_llm_fallback_rate_pct: float = 20.0
    alert_answered_pct_min: float = 60.0
    alert_daily_cost_usd: float = 10.0
    ops_alert_email: str = ""  # where health alerts are mailed (Outlook notifier); empty = log only

    api_host: str = "0.0.0.0"
    api_port: int = 8001

    # Ports match this project's own docker-compose.yml (ptc-redis), not
    # the default Redis port — kept different on purpose so this project
    # never collides with some other Redis container on the same machine.
    redis_host: str = "localhost"
    redis_port: int = 6380
    redis_db: int = 0

    # Docker Milvus standalone (+ etcd + MinIO + Attu for browsing the
    # data visually) — ptc-milvus from this project's own docker-compose.yml,
    # on a non-default port for the same isolation reason as Redis above.
    # Point this at a local file path instead (e.g.
    # "data/vector_store/milvus.db") to fall back to Milvus Lite with no
    # containers — pymilvus's MilvusClient supports both via one URI.
    milvus_uri: str = "http://localhost:19531"

    # Phase 5 escalation. Tickets and security events are stored in Postgres; the notifier sends
    # them on ("log" = write an event to the log only — email/Teams plug in here later).
    escalation_notifier: str = "log"  # "log" | "outlook"
    # Outlook / Microsoft 365 mail for tickets and security alerts (ESCALATION_NOTIFIER=outlook).
    # graph = Microsoft Graph sendMail with an Azure app registration (Mail.Send, application
    # permission, limited to the sender mailbox); smtp = smtp.office365.com with SMTP AUTH.
    # Each setting also accepts the names used by the team's other bots (second name in each
    # AliasChoices), so one .env layout works for both.
    enable_ticket_raising: bool = False  # True = same as ESCALATION_NOTIFIER=outlook
    use_graph_api: bool | None = None  # True = graph, False = smtp (overrides OUTLOOK_SEND_METHOD)
    outlook_send_method: str = "graph"
    outlook_sender: str = Field("", validation_alias=AliasChoices("OUTLOOK_SENDER", "TICKET_FROM_EMAIL"))
    outlook_sender_name: str = Field("SyteLine Assistant",
                                     validation_alias=AliasChoices("OUTLOOK_SENDER_NAME", "TICKET_FROM_NAME"))
    # Where new tickets go (comma-separated for several).
    support_ticket_email: str = Field("", validation_alias=AliasChoices("SUPPORT_TICKET_EMAIL", "TICKET_RECIPIENT_EMAIL"))
    security_alert_email: str = ""  # where security alerts go; empty = no alert mail
    outlook_tenant_id: str = Field("", validation_alias=AliasChoices("OUTLOOK_TENANT_ID", "GRAPH_TENANT_ID"))
    outlook_client_id: str = Field("", validation_alias=AliasChoices("OUTLOOK_CLIENT_ID", "GRAPH_CLIENT_ID"))
    outlook_client_secret: str = Field("", validation_alias=AliasChoices("OUTLOOK_CLIENT_SECRET", "GRAPH_CLIENT_SECRET"))
    outlook_smtp_host: str = Field("smtp.office365.com",
                                   validation_alias=AliasChoices("OUTLOOK_SMTP_HOST", "OUTLOOK_SMTP_SERVER"))
    outlook_smtp_port: int = 587
    outlook_smtp_username: str = ""  # defaults to the sender mailbox
    outlook_smtp_password: str = Field("", validation_alias=AliasChoices("OUTLOOK_SMTP_PASSWORD", "OUTLOOK_PASSWORD"))
    outlook_timeout_seconds: float = 15.0
    # Address of the feedback console as support staff reach it (e.g. http://chatbot.company.local/admin.html).
    # When set, ticket and alert emails get an "Open in feedback console" button; empty = no button.
    admin_console_url: str = ""

    @model_validator(mode="after")
    def _ticket_mail_switches(self):
        if self.enable_ticket_raising and self.escalation_notifier.lower() == "log":
            self.escalation_notifier = "outlook"
        if self.use_graph_api is not None:
            self.outlook_send_method = "graph" if self.use_graph_api else "smtp"
        return self
    # Security alert when one user is blocked this many times inside the window.
    security_alert_threshold: int = 3
    security_alert_window_minutes: int = 15

    # Conversation history — ptc-postgres from docker-compose.yml, on 5433 so it
    # never collides with a Postgres already installed on this machine. The
    # defaults match the compose file's local-dev container only; set real
    # values in .env for any shared environment.
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_db: str = "ptc_chat"
    postgres_user: str = "ptc"
    postgres_password: str = "ptc_local_dev"
    # How many earlier question/answer pairs the bot reads to understand a follow-up.
    history_turns_for_context: int = 3
    # One OpenAI call understands AND classifies the message (saves the separate classifier call,
    # ~1.5 s per question). If the combined reply has no valid classification, the separate call
    # still runs, so nothing is lost. Set COMBINED_UNDERSTANDING=false to go back to two calls.
    combined_understanding: bool = True
    # Database connections shared by all parallel requests (Postgres allows 100 by default).
    postgres_pool_max_size: int = 20


try:
    settings = Settings()
except Exception as exc:
    raise RuntimeError(
        "App settings are missing or invalid. Copy .env.example to .env and "
        "fill in OPENAI_API_KEY before starting the server."
    ) from exc
