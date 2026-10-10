# CareerPilot AI Assistant — optional structured grounding

The application works without an LLM provider. With no configuration, authenticated
`GET /api/v1/assistant/status` and `POST /api/v1/assistant/chat` return
`ASSISTANT_NOT_CONFIGURED`. ACIF and all other modules remain independent.

## Optional provider configuration

Configure these in the existing private backend environment, never source files:

- `ASSISTANT_PROVIDER=openai_compatible`
- `ASSISTANT_BASE_URL`: an operator-approved HTTPS API base ending at the API
  root (typically `/v1`). `/chat/completions` is appended. No URL comes from users.
- `ASSISTANT_MODEL`: the model identifier supported by that endpoint.
- `ASSISTANT_API_KEY`: your credential, provided through private environment or
  secret management. Never commit it or paste it into application source.
- `ASSISTANT_TIMEOUT_SECONDS`: optional, default 20; requests bounded to 1–60s.

The adapter uses the chat-completions JSON-response interface and the Python
standard library. There is no vendor SDK dependency. HTTPS, fixed operator
configuration, redirect refusal, response size limits and generic errors bound
the integration. Provider connectivity is not tested at application startup.
Review provider data-handling terms before enabling it; it receives a student's
question and bounded summaries only after explicit consent on that request.

## Accurate scope and privacy

This is a **Grounded LLM Assistant using CareerPilot structured context**, not
semantic RAG. No vector corpus, embedding model, private embeddings or semantic
retrieval exists in this version. pgvector infrastructure alone does not imply RAG.

The initial claim-control mode is `CONSTRAINED_SOURCE_SELECTION`: a provider
selects relevant source IDs, and the backend renders their exact server-authored
statements. Free-form provider prose, new recommendations, tools, and writes are
rejected. A valid citation ID proves membership in supplied context, not the
relevance of the provider's selection; relevance still needs evaluation later.

Statements preserve FACT, MODEL_OUTPUT and PERSONALIZED_RECOMMENDATION. Selection
metadata is LLM_EXPLANATION_SELECTION, never a new fact. Missing context remains
unavailable. Raw resumes, JD bodies, application notes, profile contact details,
provider internals, and hidden chain-of-thought are not sent or stored.

All optional resource IDs are checked against the authenticated owner, even when
the provider is absent. The frontend cannot provide a user ID. Questions are
independent/stateless; the visible page conversation is not persisted and is not
implicitly resent. No Redis conversation/context cache or new tables are added.

Tests use an injected deterministic fake provider; runtime configuration cannot
activate that fake. No automated test requires an external LLM or paid API.
