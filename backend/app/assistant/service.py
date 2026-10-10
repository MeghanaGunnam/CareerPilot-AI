from sqlalchemy.orm import Session

from backend.app.assistant.context import build_context, resolve_topic, validate_references
from backend.app.assistant.provider import AssistantProvider, build_messages
from backend.app.assistant.schemas import AssistantRequest, AssistantResponse, AssistantStatus, ProviderSelection

LIMITATIONS = [
    "Grounded LLM Assistant using CareerPilot structured context; semantic RAG is not implemented.",
    "The provider selects existing source statements. Unrestricted LLM prose and tool actions are disabled.",
    "Evidence is not proficiency; missing evidence is not missing skill. No employment probability is inferred.",
    "This request is stateless. Earlier visible messages are not sent as conversation history.",
]


def provider_status(provider: AssistantProvider | None) -> AssistantStatus:
    return AssistantStatus(provider_status="READY" if provider else "ASSISTANT_NOT_CONFIGURED",
                           message="Provider configured; connectivity is checked only when you submit a consented question." if provider else "CareerPilot AI Assistant is not configured yet.")


def chat(db: Session, user_id, request: AssistantRequest, provider: AssistantProvider | None) -> AssistantResponse:
    validate_references(db, user_id, request)
    topic = resolve_topic(request)
    status = provider_status(provider)
    base = {**status.model_dump(), "answer": None, "grounding_status": "UNAVAILABLE", "topic": topic, "limitations": LIMITATIONS}
    if provider is None:
        return AssistantResponse(**base)
    if not request.allow_provider_processing:
        return AssistantResponse(**{**base, "provider_status": "CONSENT_REQUIRED", "message": "Confirm that this question and limited relevant summaries may be sent to the configured provider."})
    topic, sources, limitations = build_context(db, user_id, request)
    base.update(topic=topic, limitations=LIMITATIONS + limitations)
    if not sources:
        return AssistantResponse(**{**base, "grounding_status": "INSUFFICIENT_CONTEXT", "message": "Relevant CareerPilot information is not available yet."})
    try:
        selection = ProviderSelection.model_validate(provider.generate(build_messages(request.message, sources)))
        by_id = {source.id: source for source in sources}
        if len(set(selection.source_ids)) != len(selection.source_ids) or any(source_id not in by_id for source_id in selection.source_ids):
            raise ValueError("Invalid source selection")
        chosen = [by_id[source_id] for source_id in selection.source_ids]
    except Exception:
        # Never return/log upstream payloads, private context or provider internals.
        return AssistantResponse(**{**base, "provider_status": "PROVIDER_UNAVAILABLE", "message": "The assistant provider could not return a valid grounded response. Try again later; core CareerPilot features remain available."})
    if not chosen:
        return AssistantResponse(**{**base, "grounding_status": "INSUFFICIENT_CONTEXT", "message": "The available structured context does not answer this question. Try a more specific question or another topic."})
    return AssistantResponse(**{**base, "answer": "\n\n".join(source.text for source in chosen),
                                "grounding_status": "GROUNDED_SELECTION", "message": "Response assembled from cited CareerPilot statements.",
                                "context_sources": chosen, "recommended_actions": [source for source in chosen if source.kind == "PERSONALIZED_RECOMMENDATION"],
                                "explanation_provenance": "LLM_EXPLANATION_SELECTION"})
