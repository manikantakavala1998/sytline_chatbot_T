"""LangGraph workflow for Phase 3.

SyteLine session validation and normalized context construction remain at
the trusted API boundary. The graph owns every AI/query step after that
boundary: security -> scope -> ambiguity -> transformation -> hierarchical
classification -> code-enforced routing -> route execution.
"""

from langgraph.graph import END, START, StateGraph

from backend.app.authorization.resolver import resolve_permission
from backend.app.classification.ambiguity import resolve_ambiguity
from backend.app.classification.query_transformer import transform_query
from backend.app.classification.router import classify_and_route
from backend.app.classification.scope import classify_scope
from backend.app.classification.taxonomy import IntentLabel, RouteLabel
from backend.app.orchestration.state import ChatWorkflowState, WorkflowResult
from backend.app.qa.retriever import get_qa_index
from backend.app.rag.answer_service import generate_answer
from backend.app.rag.retriever import get_rag_index
from backend.app.security.input_gate import evaluate_security
from backend.app.utils.logger import get_logger, log_event

logger = get_logger(__name__)

SECURITY_BLOCK_MESSAGE = (
    "I can’t help with requests that attempt to bypass security, expose restricted data, "
    "or override system instructions."
)
OUT_OF_SCOPE_MESSAGE = "This question is outside the scope of the SyteLine assistant."


def _decision_trace(state: ChatWorkflowState) -> dict[str, object]:
    security = state.get("security")
    scope = state.get("scope")
    ambiguity = state.get("ambiguity")
    transformed = state.get("transformed")
    classification = state.get("classification")
    selected_route = state.get("selected_route")
    return {
        "security": security.label.value if security else None,
        "scope": scope.label.value if scope else None,
        "ambiguity": ambiguity.label.value if ambiguity else None,
        "intent": classification.intent.value if classification else None,
        "sub_intent": classification.sub_intent if classification else None,
        "complexity": classification.complexity.value if classification else None,
        "emotion": classification.emotion.value if classification else None,
        "selected_route": selected_route.value if selected_route else None,
        "tool_candidate": classification.tool_candidate if classification else None,
        "transformations": transformed.transformations if transformed else [],
    }


class ChatOrchestrator:
    def __init__(self) -> None:
        builder = StateGraph(ChatWorkflowState)
        builder.add_node("security_gate", self._security_node)
        builder.add_node("blocked_response", self._blocked_response_node)
        builder.add_node("scope_check", self._scope_node)
        builder.add_node("out_of_scope_response", self._out_of_scope_node)
        builder.add_node("ambiguity_resolution", self._ambiguity_node)
        builder.add_node("clarify_response", self._clarify_node)
        builder.add_node("query_transformation", self._transform_node)
        builder.add_node("query_classification", self._classification_node)
        builder.add_node("route_selection", self._route_node)
        builder.add_node("direct_response", self._direct_response_node)
        builder.add_node("fast_qa", self._fast_qa_node)
        builder.add_node("markdown_rag", self._rag_node)
        builder.add_node("capability_pending", self._capability_pending_node)

        builder.add_edge(START, "security_gate")
        builder.add_conditional_edges(
            "security_gate",
            self._after_security,
            {"blocked": "blocked_response", "safe": "scope_check"},
        )
        builder.add_edge("blocked_response", END)
        builder.add_conditional_edges(
            "scope_check",
            self._after_scope,
            {"out_of_scope": "out_of_scope_response", "in_scope": "ambiguity_resolution"},
        )
        builder.add_edge("out_of_scope_response", END)
        builder.add_conditional_edges(
            "ambiguity_resolution",
            self._after_ambiguity,
            {"clarify": "clarify_response", "resolved": "query_transformation"},
        )
        builder.add_edge("clarify_response", END)
        builder.add_edge("query_transformation", "query_classification")
        builder.add_edge("query_classification", "route_selection")
        builder.add_conditional_edges(
            "route_selection",
            self._dispatch_route,
            {
                "blocked": "blocked_response",
                "clarify": "clarify_response",
                "direct": "direct_response",
                "fast_qa": "fast_qa",
                "rag": "markdown_rag",
                "pending": "capability_pending",
            },
        )
        builder.add_edge("direct_response", END)
        builder.add_conditional_edges(
            "fast_qa",
            self._after_fast_qa,
            {"rag": "markdown_rag", "done": END},
        )
        builder.add_edge("markdown_rag", END)
        builder.add_edge("capability_pending", END)
        self.graph = builder.compile()

    @staticmethod
    def _security_node(state: ChatWorkflowState) -> dict:
        return {"security": evaluate_security(state["query"], state["request_id"])}

    @staticmethod
    def _after_security(state: ChatWorkflowState) -> str:
        return "safe" if state["security"].allowed else "blocked"

    @staticmethod
    def _blocked_response_node(state: ChatWorkflowState) -> dict:
        security = state.get("security")
        reason = f"security:{security.label.value}" if security and not security.allowed else "blocked"
        result = WorkflowResult(
            route="BLOCKED",
            answer=SECURITY_BLOCK_MESSAGE,
            reason=reason,
            decision_trace=_decision_trace(state),
        )
        log_event(logger, "orchestration_blocked", request_id=state["request_id"], reason=reason)
        return {"result": result}

    @staticmethod
    def _scope_node(state: ChatWorkflowState) -> dict:
        return {"scope": classify_scope(state["query"], state["context"])}

    @staticmethod
    def _after_scope(state: ChatWorkflowState) -> str:
        return "in_scope" if state["scope"].in_scope else "out_of_scope"

    @staticmethod
    def _out_of_scope_node(state: ChatWorkflowState) -> dict:
        result = WorkflowResult(
            route="OUT_OF_SCOPE",
            answer=OUT_OF_SCOPE_MESSAGE,
            reason=state["scope"].label.value,
            decision_trace=_decision_trace(state),
        )
        log_event(
            logger,
            "orchestration_out_of_scope",
            request_id=state["request_id"],
            scope=state["scope"].label.value,
        )
        return {"result": result}

    @staticmethod
    def _ambiguity_node(state: ChatWorkflowState) -> dict:
        return {"ambiguity": resolve_ambiguity(state["query"], state["context"])}

    @staticmethod
    def _after_ambiguity(state: ChatWorkflowState) -> str:
        return "resolved" if state["ambiguity"].resolved else "clarify"

    @staticmethod
    def _clarify_node(state: ChatWorkflowState) -> dict:
        ambiguity = state.get("ambiguity")
        answer = (
            ambiguity.clarification_question
            if ambiguity and ambiguity.clarification_question
            else "Could you clarify the SyteLine topic or record you mean?"
        )
        result = WorkflowResult(
            route="CLARIFY",
            answer=answer,
            reason=ambiguity.label.value if ambiguity else "clarification_required",
            decision_trace=_decision_trace(state),
        )
        log_event(
            logger,
            "orchestration_clarification_requested",
            request_id=state["request_id"],
            ambiguity=result.reason,
        )
        return {"result": result}

    @staticmethod
    def _transform_node(state: ChatWorkflowState) -> dict:
        query = state["ambiguity"].resolved_query or state["query"]
        return {"transformed": transform_query(query, state["context"])}

    @staticmethod
    def _classification_node(state: ChatWorkflowState) -> dict:
        return {"classification": classify_and_route(state["transformed"], state["context"])}

    @staticmethod
    def _route_node(state: ChatWorkflowState) -> dict:
        route = state["classification"].route
        log_event(
            logger,
            "orchestration_route_selected",
            request_id=state["request_id"],
            route=route.value,
            intent=state["classification"].intent.value,
        )
        return {"selected_route": route}

    @staticmethod
    def _dispatch_route(state: ChatWorkflowState) -> str:
        route = state["selected_route"]
        if route == RouteLabel.BLOCK:
            return "blocked"
        if route == RouteLabel.CLARIFY:
            return "clarify"
        if route == RouteLabel.DIRECT_RESPONSE:
            return "direct"
        if route == RouteLabel.FAST_QA:
            return "fast_qa"
        if route == RouteLabel.MARKDOWN_RAG:
            return "rag"
        return "pending"

    @staticmethod
    def _direct_response_node(state: ChatWorkflowState) -> dict:
        intent = state["classification"].intent
        sub_intent = state["classification"].sub_intent
        answers = {
            IntentLabel.GREETING: "Hello! How can I help with your SyteLine Prospect-to-Cash work?",
            IntentLabel.FEEDBACK: "Thank you for the feedback. It has been noted for the improvement workflow.",
            IntentLabel.COMPLAINT: "I understand this is frustrating. Tell me the SyteLine screen or process involved, and I’ll help narrow it down.",
        }
        chitchat_answers = {
            "wellbeing": "I’m doing well, thank you for asking! How can I help you with SyteLine today?",
            "casual_checkin": "Not much—I’m here and ready to help with SyteLine. What are you working on?",
            "identity": (
                "I’m the SyteLine Prospect-to-Cash Assistant. I help with approved business concepts, "
                "screens, fields, processes, and safe request routing."
            ),
            "capabilities": (
                "I can explain approved Prospect-to-Cash concepts, screens, fields, and processes, "
                "and I can classify live-data, navigation, and action requests for the appropriate route."
            ),
            "thanks": "You’re welcome. Ask me anytime about the SyteLine Prospect-to-Cash process.",
            "introduction": "Nice to meet you too. I’m here to help with SyteLine Prospect-to-Cash.",
            "acknowledgement": "Got it. What would you like to work on in SyteLine?",
            "farewell": "Goodbye! I’ll be here when you need more SyteLine help.",
        }
        result = WorkflowResult(
            route="DIRECT_RESPONSE",
            answer=(
                chitchat_answers.get(
                    sub_intent,
                    "I’m here to help with SyteLine Prospect-to-Cash. What would you like to discuss?",
                )
                if intent == IntentLabel.CHITCHAT
                else answers.get(intent, "How can I help with SyteLine?")
            ),
            decision_trace=_decision_trace(state),
        )
        log_event(logger, "orchestration_response_ready", request_id=state["request_id"], route=result.route)
        return {"result": result}

    @staticmethod
    def _fast_qa_node(state: ChatWorkflowState) -> dict:
        permission = resolve_permission(state["user"], "READ", "qa", request_id=state["request_id"])
        if not permission.allowed:
            result = WorkflowResult(
                route="BLOCKED",
                answer=None,
                reason=permission.reason,
                decision_trace=_decision_trace(state),
            )
            return {"result": result}

        log_event(logger, "fast_qa_search_started", request_id=state["request_id"])
        match = get_qa_index().search(state["transformed"].expanded_query)
        log_event(
            logger,
            "fast_qa_search_completed",
            request_id=state["request_id"],
            route=match.route,
            score=round(match.score, 4),
            candidates=len(match.candidates),
        )

        if match.route == "FAST_QA_RESPONSE" and match.record:
            return {
                "result": WorkflowResult(
                    route=match.route,
                    answer=match.record.answer,
                    source=match.record.qa_id,
                    score=match.score,
                    decision_trace=_decision_trace(state),
                )
            }

        if match.route == "CLARIFY":
            options = "; ".join(record.canonical_question for record, _ in match.candidates)
            return {
                "result": WorkflowResult(
                    route="CLARIFY",
                    answer=f"I found a few possible matches — did you mean: {options}?",
                    score=match.score,
                    decision_trace=_decision_trace(state),
                )
            }

        return {"selected_route": RouteLabel.MARKDOWN_RAG}

    @staticmethod
    def _after_fast_qa(state: ChatWorkflowState) -> str:
        return "done" if state.get("result") else "rag"

    @staticmethod
    def _rag_node(state: ChatWorkflowState) -> dict:
        permission = resolve_permission(
            state["user"], "READ", "markdown_rag", request_id=state["request_id"]
        )
        if not permission.allowed:
            return {
                "result": WorkflowResult(
                    route="BLOCKED",
                    answer=None,
                    reason=permission.reason,
                    decision_trace=_decision_trace(state),
                )
            }

        log_event(logger, "rag_search_started", request_id=state["request_id"])
        rag_result = get_rag_index().search(state["transformed"].expanded_query)
        log_event(
            logger,
            "rag_search_completed",
            request_id=state["request_id"],
            has_evidence=rag_result.has_evidence,
            chunks=len(rag_result.chunks),
        )

        if not rag_result.has_evidence:
            return {
                "result": WorkflowResult(
                    route="NO_ANSWER",
                    answer="I don’t have enough approved information to answer that yet.",
                    decision_trace=_decision_trace(state),
                )
            }

        log_event(
            logger,
            "answer_generation_started",
            request_id=state["request_id"],
            evidence_chunks=len(rag_result.chunks),
        )
        try:
            answer = generate_answer(state["query"], rag_result.chunks)
        except Exception:
            logger.exception("event=answer_generation_failed request_id=%s", state["request_id"])
            raise

        sources = [f"{chunk.source_file} — {chunk.full_context_path}" for chunk in rag_result.chunks]
        return {
            "result": WorkflowResult(
                route="MARKDOWN_RAG_RESPONSE",
                answer=answer,
                sources=sources,
                score=rag_result.scores[0] if rag_result.scores else 0.0,
                decision_trace=_decision_trace(state),
            )
        }

    @staticmethod
    def _capability_pending_node(state: ChatWorkflowState) -> dict:
        route = state["selected_route"]
        messages = {
            RouteLabel.LIVE_DATA: (
                "I recognized this as a live SyteLine data request. Live IDO/API access is not connected yet, "
                "so I did not answer it from documents or model memory."
            ),
            RouteLabel.RAG_IDO: (
                "This request needs both approved documentation and live SyteLine data. The live-data part "
                "arrives in Phase 4, so no partial or potentially misleading answer was generated."
            ),
            RouteLabel.NAVIGATION: (
                "I recognized this as a SyteLine navigation request. Navigation execution is not connected "
                "yet; no form or record was opened."
            ),
            RouteLabel.ACTION: (
                "I recognized this as a transaction request. The current proof of concept is read-only, "
                "so no SyteLine change was made."
            ),
            RouteLabel.LLM_REASONING: (
                "I recognized this as an advanced analysis request. That controlled reasoning route is not "
                "enabled yet, so I did not generate an unsupported answer."
            ),
        }
        result = WorkflowResult(
            route="CAPABILITY_PENDING",
            answer=messages.get(route, "This route is not available yet."),
            reason=f"phase_4_or_later:{route.value}",
            decision_trace=_decision_trace(state),
        )
        log_event(
            logger,
            "orchestration_capability_pending",
            request_id=state["request_id"],
            route=route.value,
        )
        return {"result": result}

    def run(self, query: str, context, user) -> WorkflowResult:
        state = self.graph.invoke(
            {
                "request_id": context.request_id,
                "query": query,
                "context": context,
                "user": user,
            }
        )
        result = state.get("result")
        if result is None:
            raise RuntimeError("Orchestration completed without a result")
        log_event(
            logger,
            "orchestration_completed",
            request_id=context.request_id,
            route=result.route,
            reason=result.reason or "none",
        )
        return result


_orchestrator: ChatOrchestrator | None = None


def get_chat_orchestrator() -> ChatOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChatOrchestrator()
    return _orchestrator
