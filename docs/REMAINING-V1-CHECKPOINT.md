# Remaining CareerPilot V1 checkpoint

## Last verified phase: G — Dashboard & Navigation Integration

Phase A remains complete and preserved. Phase B backend persistence, ownership,
extraction, API/frontend contract, deployed migration, and checks are verified.
Phases F and G verified below. Stop here: no deployment or research evaluation.
This is an engineering checkpoint, NOT a production-readiness or research-validation claim.
No commits, pushes, resets, cleans, dependency changes, or frontend rewrites were
performed during this completion pass. Existing Phase A/B working-tree changes
were preserved. The Phase B migration was already applied when this pass began.

## Phase A architecture (preserved)

Read-only `backend/app/certification_recommendations` reuses authenticated primary
goal -> mapped O*NET career -> existing ACIF gap analysis and Career Twin snapshot.
Earned certifications remain in the existing student profile model and service.
No recommendation state, evidence, proficiency, or roadmap records are written.

Seven curated catalogue entries: PCAP, Oracle Java SE 17 Developer, Oracle
Database SQL, CKA, Azure Fundamentals, AWS Cloud Practitioner, Power BI Data
Analyst Associate. Skills are editorial coverage mappings, not full syllabi.
Five official pages were retrieved; two Oracle pages returned HTTP 403 and have
explicit limited-verification metadata. Prices, prerequisites, validity and
availability are not asserted. The catalogue must be periodically reviewed.

Ranking: exact ACIF-normalized technology matches against missing/weak evidence
gaps; missing count descending, total matched count descending, stable key
ascending. Priority is display rank, not readiness or employment probability.
Earned suppression requires normalized exact name/provider or explicit aliases.
No fuzzy guessing and no fabricated renewal recommendations.

## Phase A API / UI

- Authenticated GET `/api/v1/certification-recommendations`.
- Returns target role separately from occupational anchor, snapshot/model
  versions, methodology, ranked recommendations, gaps, reasons, official links,
  source provenance, interpretation.
- Missing goal/mapping/twin returns 404; no matches returns 200 with empty list.
- New `/certifications` is explicitly Recommended Certifications. Earned
  certifications link to existing `/profile`.
- Dashboard entry visible on mobile/desktop.
- UI includes loading/error/retry/empty/authentication states, request cleanup,
  external HTTPS provider allowlist and source-verification caveats.

## Phase A original verification receipt

Using `.venv/Scripts/python.exe`:
- `-m unittest discover -s backend/tests`: 40 cases, 38 passed, 2 opt-in skipped.
- With `CAREERPILOT_POSTGRES_TEST=1`, certification PostgreSQL test: passed.
  Synthetic schema rolled back; proves separate user suppression, changed
  primary goal, SELECT-only recommendation service, no evidence/roadmap writes.
- `-m compileall -q backend/app`: passed.
- Alembic heads/current: both f4a2b7c9d1e3, single head.
- Direct ASGI authentication/response tests included; no TestClient dependency
  installation or paid services required.

Frontend `npx tsc --noEmit`, `npm run lint`, `npm run build`: passed.
Build warns about an unrelated D:/pnpm-lock.yaml outside the repository.
No authenticated browser E2E flow was performed.

## Phase A files (preserved)

- backend/app/main.py
- backend/app/certification_recommendations/__init__.py
- backend/app/certification_recommendations/catalog.py
- backend/app/certification_recommendations/schemas.py
- backend/app/certification_recommendations/service.py
- backend/app/certification_recommendations/router.py
- backend/tests/test_certification_recommendations.py
- backend/tests/test_certification_recommendations_postgres.py
- frontend/src/app/certifications/page.tsx
- frontend/src/lib/api/certification-recommendations.ts
- frontend/src/app/dashboard/page.tsx
- docs/REMAINING-V1-CHECKPOINT.md

## Phase A remaining limitations

Certification suggestions use ACIF technology gaps, not independent learned
ranking or direct roadmap/GPS scoring. No unsupported recommendations for
unknown technologies. Catalogue currency and Oracle page verification remain
limited. No full end-to-end browser acceptance claim. Existing project privacy,
authentication production-hardening, and assessment transaction limitations
remain as documented in prior checkpoints.

## Phase B architecture and persistence

Inspection confirmed that the frontend was built against an actual existing
backend contract, not an anticipated one. `backend/app/jobs` already contained
models, schemas, extractor, service, router, and associated tests/migration.
The completion pass retained that architecture and fixed technology quote
context so negation is visible alongside normalized interpretations.

- `JDAnalysis` / `jd_analyses`: UUID, authenticated `user_id`, `title`, optional
  `company`/`source_url`, exact `source_text`, `created_at`, `extractor_version`,
  `requirement_count`, and `truncated`.
- `Requirement` / `jd_requirements`: parent analysis FK, stable position,
  inferred group, literal quote, source offsets, evidence type, optional
  normalized name and interpretation type. Unique `(analysis_id, position)`.
- PostgreSQL constraints bound source length (30,000 code points), requirements
  (100), positions, spans, quote lengths, groups and interpretation pairs.
- Parent and child persist in one transaction. Records are immutable through
  this API; no update/delete endpoints or unnecessary `updated_at` field.
- User deletion cascades through analyses to requirements. No Career Twin,
  evidence profile, assessment, certification or roadmap records are created.
- No location/employment type added: current input contract is intentionally
  `title`, `company?`, `source_url?`, `source_text` only.

## Phase B extraction and evidence semantics

- Deterministic extractor `jd-literal-v2`; no LLM, paid API, or URL fetching.
- Reuses resume `SKILL_ALIASES` and ACIF `TECHNOLOGY_ALIASES` /
  `normalize_technology_name`; no competing canonical skill dictionary.
- Bounded longest-alias matching avoids substring matches such as Pythonic ->
  Python or JavaScript -> Java. Unknown technology names are not guessed.
- Group heuristics cover technology, experience, education, responsibility and
  preferred. These labels are interpretations, NOT mandatory-status facts.
- `FACT_FROM_JD` applies only to literal source quotes. Normalized names use
  `NORMALIZED_INTERPRETATION`, retaining the existing API enum spelling.
- New normalized technology rows quote the surrounding clause instead of only
  the alias. `Python experience is not required.` remains that exact quote;
  neither the quote nor canonical name asserts that Python is required.
- Source offsets are zero-based Unicode code points with an exclusive end.
  Original CRLF, emoji, internal spaces/tabs and full JD text are preserved.
- Duplicate normalized mentions in one clause are collapsed. Truncation is
  explicit; counts describe extracted records, not unique required skills.
- GET returns persisted extraction/version, never regenerated output. Existing
  `jd-literal-v1` records are not rewritten by the v2 change.

## Phase B API, ownership and frontend contract

- POST `/api/v1/jobs/analyses` -> 201 `JDAnalysisResponse`.
- GET `/api/v1/jobs/analyses?limit=10&offset=0` ->
  `{items, total, limit, offset}`. Server default limit 20, range 1–100;
  frontend requests 10. Newest first, UUID descending tie-breaker.
- GET `/api/v1/jobs/analyses/{analysis_id}` -> stored detail plus original JD.
- All routes require the existing bearer authentication dependency. Owner is
  taken exclusively from the authenticated user, never request body/query.
- SQL list/count/detail predicates enforce ownership. Foreign and nonexistent
  UUIDs return the same 404 payload. Missing/invalid auth returns 401;
  inactive users receive 403; malformed fields/UUIDs/pagination return 422.
- POST rejects extra fields, including injected `user_id` or `location`.
- `/job-match` and `frontend/src/lib/api/jobs.ts` were compared against actual
  schemas/OpenAPI and PostgreSQL-backed ASGI responses. Create/history/detail,
  nullability, pagination, enums, and validation/auth statuses align.
- Completed frontend preserved: loading/submission/error/retry/empty/auth
  states, stale-load cancellation, saved history, literal quotes and original
  JD. Explicit extraction-only messaging; no candidate matching or scores.

### POST uncertainty / idempotency

No shared request-idempotency pattern exists in the current application.
Each successful POST creates a distinct immutable analysis. A response lost
after commit can leave the record saved. Repeating identical input produces
identical semantic extraction but a different record UUID. This is tested.
The frontend retains its warning to refresh history before retrying uncertain
submissions. No silent content deduplication or automatic POST retry added.

## Phase B migration receipt

- Existing forward migration:
  `backend/alembic/versions/a7c3d9e2b6f1_create_jd_analyses.py`.
- Chain: `f4a2b7c9d1e3` -> `a7c3d9e2b6f1`.
- Before this completion pass: current = `a7c3d9e2b6f1 (head)`;
  heads = `a7c3d9e2b6f1 (head)`.
- After verification: same current and single head. Already applied; no
  redundant migration, reapplication or edits to applied migrations.
- Read-only inspection verifies deployed JD column types/nullability,
  constraints, indexes, parent FKs, cascades and unique positions against models.
- The existing migration upgrade and downgrade both ran successfully only in
  a synthetic PostgreSQL schema within a rolled-back outer transaction.
  Synthetic schema cleanup is asserted; production data was not deleted.

## Phase B verification receipt

All Python checks used `D:\CareerPilot-AI\.venv\Scripts\python.exe` from
the repository root. No dependencies or paid services were added.

- `-m compileall -q backend`: passed.
- `-m unittest backend.tests.test_jobs -v`: 12 tests passed.
- `-m unittest discover -s backend/tests -v`: 54 discovered, 50 passed,
  four PostgreSQL opt-in cases skipped as designed.
- With `CAREERPILOT_POSTGRES_TEST=1`, explicit modules
  `backend.tests.test_jobs_postgres`,
  `backend.tests.test_certification_recommendations_postgres`, and
  `backend.tests.test_assessment_postgres_pipeline`: four cases passed.
- Combined discovery with configuration initialized before discovery: all
  54 passed, zero skips. Exact PowerShell reproduction:

```powershell
$env:CAREERPILOT_POSTGRES_TEST='1'
.\.venv\Scripts\python.exe -c "import unittest; from backend.app.core.database import engine; suite = unittest.defaultTestLoader.discover('backend/tests'); result = unittest.TextTestRunner(verbosity=2).run(suite); engine.dispose(); raise SystemExit(0 if result.wasSuccessful() else 1)"
```

The ordinary opt-in combined discovery command initially failed its four DB
cases because older unit-test modules install a dummy `DATABASE_URL` at import
time, before application settings initialize. Standalone PostgreSQL modules
work as documented. Pre-initializing application configuration in the command
above avoids that existing import-order issue without exposing credentials or
changing Phase A code. This failure was investigated, not suppressed.

An initial schema-inspection assertion compared generic and PostgreSQL-specific
timestamp strings; the assertion now compiles both types with the same dialect.
The actual deployed timezone-aware column was correct. An earlier separately
ordered PostgreSQL run emitted a pooled-connection ResourceWarning at process
exit; final combined verification closes the engine and had no such warning.

### Phase B test coverage

- Actual bearer decoding/user lookup; missing and invalid bearer 401;
  inactive account 403; successful authenticated POST 201.
- PostgreSQL parent/child persistence, exact POST/GET round trip after session
  expiration, extractor version and original source retention.
- Paged history with stable order, correct owner-scoped total, empty later
  pages, and rejected invalid bounds.
- User B cannot retrieve or list user A's records, even while B owns a separate
  record. Foreign/missing UUID response equality. Unsupported mutations 405.
- Rejected ownership injection, unsupported location, blank/malformed input,
  oversized source, and non-HTTP(S) source URLs.
- Shared canonical normalization, longest aliases, no substring/unmapped
  fabrication, deterministic repeat extraction, visible truncation.
- Negative/optional statements, repeated mentions, Unicode/CRLF provenance,
  literal slices and source offsets. No mandatory flag or mandatory-status inference.
- Service commit failure rolls back; child bounds enforced in PostgreSQL;
  synthetic user deletion cascades without deleting another user's analysis.
- Stored detail reads do not call extraction again.
- OpenAPI operation/security/schema-field checks match the frontend contract.

### Other required checks

- OpenAPI generated using `app.openapi()` and JSON-serialized successfully.
  Confirmed only expected JD operations: collection GET/POST and detail GET.
- `-m alembic current`: `a7c3d9e2b6f1 (head)`.
- `-m alembic heads`: `a7c3d9e2b6f1 (head)`; one head.
- `git diff --check`: passed (existing LF/CRLF conversion warnings only).
- From `frontend`: `npx tsc --noEmit`, `npm run lint`, `npm run build` passed.
  Build includes `/job-match` and `/certifications`; unrelated warning about
  `D:/pnpm-lock.yaml` outside the repository remains unchanged.
- No authenticated browser E2E flow was performed. API integration uses the
  real ASGI app and PostgreSQL with synthetic, rolled-back fixtures.

## Phase B files

Existing Phase B implementation verified and preserved:

- `backend/app/jobs/models.py`
- `backend/app/jobs/schemas.py`
- `backend/app/jobs/router.py`
- `backend/app/main.py` (jobs route registration alongside Phase A)
- `backend/alembic/env.py` (JD model registration)
- `backend/alembic/versions/a7c3d9e2b6f1_create_jd_analyses.py`
- `frontend/src/app/job-match/page.tsx`
- `frontend/src/lib/api/jobs.ts`
- `frontend/src/app/dashboard/page.tsx` (both additive Phase A/B links)

Files changed during this completion pass:

- `backend/app/jobs/extractor.py` — v2 clause-context quotes.
- `backend/app/jobs/service.py` — explicit non-idempotent POST contract docs.
- `backend/tests/test_jobs.py` — source/negation, API/OpenAPI contract tests.
- `backend/tests/test_jobs_postgres.py` — deployed schema, actual bearer auth,
  pagination, persistence, ownership, duplicate POST and rollback checks.
- `docs/REMAINING-V1-CHECKPOINT.md` — this verification receipt.

Git remains intentionally dirty: existing tracked main/Alembic/dashboard edits
plus untracked Phase A/B modules, tests, migration, routes and checkpoint.
Nothing was staged, committed, pushed, reset or cleaned; no secrets or build
outputs were added to version control.

## Phase B limitations and next phase

- Finite vocabulary and conservative line/clause heuristics are not exhaustive
  language understanding. Grouping does not determine whether a mention is
  mandatory, negated, preferred or merely contextual. Original JD remains the
  authority; qualifiers spanning separate clauses/lines require human review.
- No unsupported skill guesses, LLM extraction, arbitrary URL retrieval,
  location, employment type, update/delete UI, or content-based idempotency.
- Existing v1 records remain v1; their technology quotes can be alias-only.
  Original JD/version provenance remains available. No silent backfill.
- Input is capped at 30,000 code points and 100 extracted records, with explicit
  truncation. A zero extraction does not assert that the JD has no requirements.
- No candidate comparison, evidence alignment, hiring/placement probability,
  or aggregate matching score exists in Phase B.
- No browser-level authenticated acceptance claim. Test harness import-order
  caveat and unrelated frontend lockfile warning are recorded above.

**Historical Phase B handoff: C — Explainable Job Matching.** Superseded below.
Wait for review of this persistence/migration checkpoint. Phase C must reuse
the authenticated user's current Career Twin/evidence, preserve MISSING
EVIDENCE != MISSING SKILL, and must not interpret every normalized JD mention
as a mandatory requirement. Phases D–G remain unimplemented by this batch.

## Phase C — verified checkpoint

- Read-only GET `/api/v1/jobs/analyses/{analysis_id}/match` consumes persisted
  Requirement rows, checks JD ownership first, then uses the latest recorded
  authenticated Career Twin snapshot. No re-extraction or snapshot writes.
- Reuses ACIF `calculate_all_skill_states`, `build_student_skill_index`,
  canonical normalization and `classify_technology_match` (strong >= 0.70).
  No independent skill profile/gap engine. Provenance includes snapshot time,
  version, ACIF version, matching version and original JD requirement record.
- States: EVIDENCE_BACKED_ALIGNMENT, EVIDENCE_NEEDS_STRENGTHENING,
  MISSING_EVIDENCE, NOT_ASSESSED, UNKNOWN_OR_UNMAPPED. Assessment-specific
  measurement is separate from evidence confidence, including measured zero.
- Missing snapshot -> explicit UNAVAILABLE with null alignment; no fabricated
  missing-skill diagnosis. No automatic creation of a Twin.
- Strength is conservative interpretation: explicit required clauses only are
  aggregate eligible; negative, preferred/optional, conditional, conflicting,
  unknown-strength and legacy alias-only requirements are excluded. Surrounding
  paragraph context checks prevent common wrapped negative qualifiers from
  being promoted to mandates. This is not complete linguistic understanding.
- CareerPilot Evidence Alignment = unique eligible strongly evidenced
  technologies / unique eligible mapped technologies. No partial weights;
  unknown criteria are not failures. Null when denominator is zero, no Twin,
  or extraction is truncated. Numerator/denominator and exclusions are returned.
- Actions reuse ACIF evidence actions, existing active assessment records and
  Phase A curated recommendation builder/earned suppression. Navigation links
  to the existing evidence, assessment, certification and roadmap experiences.
  Roadmap generation is deliberately NOT called (its getter writes records).
- Existing `/job-match` extended with opt-in Compare with my Career Twin,
  explanation, source quotes, evidence types, unavailable/error/auth states,
  cleanup and stale-request cancellation. Extraction remains separate.
- No schema migration. Current/head remain `a7c3d9e2b6f1`, single head.

Verification: full discovery with PostgreSQL enabled and configuration preloaded
(same command as Phase B) **58 passed, zero skips**, including source trace,
negative/optional/legacy/truncated cases, deterministic aggregate, measured zero,
same JD/different Twins, same Twin/different JDs, foreign JD 404, and SELECT-only
matching. Synthetic schema rolled back. Backend compilation, OpenAPI route,
Alembic state and diff checks passed. Frontend tsc/lint/build passed. First build
attempt timed out at 120 seconds; no surviving build/lock was found, and retry
with a 300-second timeout succeeded. Existing outside-repo lockfile warning
remains. No authenticated browser E2E claim.

Files: `backend/app/jobs/matching.py`, `matching_schemas.py`, jobs `router.py`;
`backend/tests/test_job_matching.py`, `synthetic_db.py`;
`frontend/src/app/job-match/MatchPanel.tsx`, job-match `page.tsx`,
`frontend/src/lib/api/jobs.ts`, and this checkpoint.

Next exact phase: **D — Application Tracker**. Phase E follows only after D
verification. Assistant/RAG is not part of this run.

## Phase D — verified checkpoint

- New `backend/app/applications`: user-owned Application model, validated create
  and partial-update schemas, service-level ownership checks, authenticated CRUD.
- Fields: owner/UUID, company, role, optional location/employment type/source URL,
  optional owned JD FK, applied date, notes, explicit status, created/updated times.
- Status check constraint: SAVED, APPLIED, ASSESSMENT, INTERVIEW, OFFER, REJECTED,
  WITHDRAWN. Transitions are explicitly user-recorded; no inferred outcome/date.
- POST/GET `/api/v1/applications`; GET/PATCH/DELETE
  `/api/v1/applications/{application_id}`. PATCH supports status and other fields;
  no duplicate status endpoint. List supports status filter and limit/offset.
- Every read/mutation scopes by authenticated owner. Linking/relinking validates
  the JD through Phase B's owned lookup. Foreign/missing application and JD UUIDs
  use safe not-found semantics. User ID is forbidden as an input property.
- JD FK uses SET NULL: deleting a JD through an administrative operation does
  not erase application history. Deleting an application preserves the JD;
  deleting a user cascades their applications. Linking ownership is enforced
  by the service, not by a composite database owner FK; direct SQL writers must
  preserve that invariant. No transfer-of-ownership API exists.
- `/applications` supports create, edit/status, filter, paged history, detail
  load, confirmed delete, optional JD reference and timestamps. `/job-match`
  offers Track this application; owned JD metadata pre-fills without saving.
  Application links reopen `/job-match?analysis=<id>`. Dashboard link added.
- Mutation errors preserve input and advise refreshing before uncertain retry;
  no automatic mutation retry. No job URL fetching or external submissions.

Migration receipt:
- Before creation: current/head `a7c3d9e2b6f1`, one head.
- NEW `backend/alembic/versions/b8d4e0f3c7a2_create_applications.py`.
- `alembic upgrade head` applied `a7c3d9e2b6f1` -> `b8d4e0f3c7a2`.
- After: current/head `b8d4e0f3c7a2`, one head. Applied migrations untouched.
- Upgrade/downgrade and cascade behavior also verified in a rolled-back
  synthetic schema. Existing development data was preserved.

Verification: **60 tests passed, zero skips** in full preloaded PostgreSQL-enabled
discovery. Covers CRUD, all statuses, timestamps, empty/no-JD applications,
pagination/filtering, malformed input, missing links, cross-user link creation
and updates, and foreign read/update/status/delete attempts. Backend compilation,
OpenAPI routes and `git diff --check` passed. Frontend `npx tsc --noEmit`,
`npm run lint`, `npm run build` passed. An earlier parallel lint attempt hit its
120-second tool timeout; the final sequential 300-second check passed. Existing
outside-repo lockfile warning remains; no browser E2E claim.

Files: applications backend package; main/Alembic registration; new migration;
`backend/tests/test_applications.py`; shared synthetic fixture and Phase B test
fixture updated to handle the dependent table/204 responses; frontend
`src/lib/api/applications.ts`, `src/app/applications/page.tsx`, job-match page,
dashboard link, and this checkpoint.

Next exact phase: **E — Career Twin Progress Tracking**. Reuse actual snapshots,
events and recorded roadmap statuses; never synthesize historical metrics.

## Phase E — verified checkpoint

- New read-only GET `/api/v1/career-twin/progress`, implemented inside the
  existing Career Twin package. No second Twin, historical store, or migration.
- Authenticated owner resolves the existing Twin before selecting snapshots
  and events. Request-supplied user/Twin IDs cannot select another user's data.
- Paged snapshot summaries and event timeline: `limit` (1–100), `offset`,
  `event_offset`; newest recorded snapshot version/event timestamp first.
- Latest two recorded snapshots are compared independently of history paging.
  Returns current recorded value, previous recorded value and actual change.
- Defensible historical metrics are counts of skill entries, evidence entries
  and assessment-evidence entries stored in compatible schema 1.0 snapshots.
  Negative changes are shown honestly; counts are not proficiency measurements.
- Missing/malformed historical fields and unknown schemas return null, not
  zero. Zero/one snapshot or no comparable fields -> "Not enough history yet."
- No reconstructed historical ACIF technology coverage, evidence strength or
  competency coverage: these historical metrics were not captured in snapshots.
- Events are actual persisted CareerTwinEvent rows. Only stored event fields
  and a valid stored snapshot-version reference are shown; nothing fabricated.
- Roadmap section aggregates actual persisted statuses across the user's goals,
  including NOT_STARTED/IN_PROGRESS/COMPLETED/SKIPPED. It does not call roadmap
  generation or infer completion. Unknown recorded statuses stay separate.
- Assessment activity is a clearly labeled CURRENT count of attempts marked
  COMPLETED with a recorded completed_at. It is not a historical score/series.
- `/progress`: latest comparison table, paged snapshot history, paged event
  timeline, current roadmap statuses and assessment activity. Auth/loading/
  empty/unavailable/error/retry states and request cancellation included.
- Dashboard entry added without redesign. Phase F/AI Assistant not started.

Phase E tests cover zero/single/multiple snapshots, incomplete/unknown schema,
actual increases/decreases, no invented coverage scores, event order, independent
pagination, current roadmap statuses, assessment count, user isolation, ignored
foreign owner/Twin query parameters, and SELECT-only behavior. Synthetic fixtures
and schemas roll back. No production student records were inspected for testing.

## Final C–E verification receipt

Using repository `.venv/Scripts/python.exe`:

- `-m compileall -q backend`: passed.
- Standard `-m unittest discover -s backend/tests`: 64 discovered, 57 passed,
  7 opt-in PostgreSQL cases skipped as designed.
- Full PostgreSQL-enabled discovery with application configuration initialized
  before older unit-test import defaults: **64 passed, zero skips**. This includes
  all seven PostgreSQL cases (applications, assessments, certifications, matching,
  two JD cases, progress). Use the exact preloaded command from Phase B above.
- OpenAPI generated/JSON-serialized; new match/application/progress operation
  sets and bearer-security definitions asserted successfully.
- `alembic current` and `alembic heads`: **b8d4e0f3c7a2 (head)**, single head.
- `git diff --check`: passed; existing Windows LF/CRLF warnings remain.
- Frontend `npx tsc --noEmit`, `npm run lint`, `npm run build`: passed, including
  `/job-match`, `/applications`, `/progress` and preserved Phase A routes.
- Existing outside-repository `D:/pnpm-lock.yaml` build warning remains.
- No browser-level authenticated E2E was performed; claims are limited to real
  ASGI/PostgreSQL integration, contract/type checks and production compilation.

### C–E implementation files

- `backend/app/jobs/matching.py`, `matching_schemas.py`, `router.py`
- `backend/app/applications/__init__.py`, `models.py`, `schemas.py`, `service.py`, `router.py`
- `backend/app/career_twin/progress.py`, `progress_schemas.py`, `router.py`
- `backend/app/main.py`, `backend/alembic/env.py`
- `backend/alembic/versions/b8d4e0f3c7a2_create_applications.py`
- `backend/tests/synthetic_db.py`, `test_job_matching.py`, `test_applications.py`, `test_progress.py`
- `backend/tests/test_jobs.py`, `test_jobs_postgres.py` (fixture compatibility only in C–E)
- `frontend/src/lib/api/jobs.ts`, `applications.ts`, `progress.ts`
- `frontend/src/app/job-match/page.tsx`, `MatchPanel.tsx`
- `frontend/src/app/applications/page.tsx`, `frontend/src/app/progress/page.tsx`
- `frontend/src/app/dashboard/page.tsx`
- `docs/REMAINING-V1-CHECKPOINT.md`

### Security audit and remaining limits

- New private resources enforce server-side ownership; no frontend filtering
  substitutes for authorization. Matching checks the saved JD owner first.
  Application get/update/status/delete and JD linking are owner-scoped.
  Progress reads only the authenticated Twin and owner-scoped roadmap/attempts.
- No extra evidence/profile/roadmap engines; matching and progress write nothing.
  Source quotes remain facts, normalization/strength interpretations remain
  separate, and assessment measurements remain assessment-specific.
- Matching uses the latest RECORDED Twin snapshot, not unsaved changes. Strength
  inference is conservative; many realistic descriptions yield unavailable
  aggregate alignment. It is not an employment probability or full suitability
  judgment. Unknown education/experience-duration/responsibility mapping remains
  explicit; no fabricated measurement of those dimensions.
- Suggested actions link to existing workflows; they do not enroll, certify,
  auto-complete roadmap items or guarantee catalogue applicability. Certification
  recommendations page remains goal-based, as explained in the action labels.
- Applications do not integrate with employers. Duplicate POSTs are possible
  after uncertain network responses; no request-idempotency infrastructure.
- Historical progress is limited to fields actually recorded; no continuous
  tracking or retroactive ACIF history. Current totals are labeled separately.
- No applied migrations edited; previous A/B changes remain. Working tree is
  intentionally dirty with tracked edits and untracked A–E code/test/docs files.
  Nothing staged/committed/pushed/reset/cleaned. No secrets/build outputs staged.

**Next exact phase: F — CareerPilot AI Assistant / RAG.** Not started. Stop here
for review; final navigation Phase G and V1 completion remain outstanding.

## Proposed Phase F architecture (recorded before implementation)

Entry verification: Git working tree clean; Alembic current/head both
`b8d4e0f3c7a2`, one head. Preserve the existing CareerPilot AI and ACIF — Adaptive
Career Intelligence Framework modules and naming.

- Stateless, authenticated assistant with optional owned JD/application UUIDs.
  No conversation tables or migration; visible messages live only in the page.
- Structured grounding first. Docker provides pgvector/PostgreSQL 17 and Redis,
  but no embedding model/vector columns/semantic corpus or application retrieval
  pipeline was found. No embeddings, vectorization, Redis context cache, or claim
  of semantic RAG. Structured records remain in their existing owner-scoped stores.
- Topic selection retrieves bounded relevant summaries using existing profile,
  goal/O*NET/RIASEC, ACIF, assessment, recommendation, JD match, applications,
  progress and persisted-roadmap queries. Never call the mutating roadmap getter,
  create a snapshot, run What-If as real evidence, or load all private records.
- Provider-neutral interface plus optional OpenAI-compatible HTTPS adapter using
  stdlib HTTP; settings-only credentials/model/endpoint. No added dependencies.
  Missing/invalid provider configuration yields ASSISTANT_NOT_CONFIGURED without
  breaking core startup. Deterministic fake provider exists for tests only.
- Strong initial claim boundary: provider selects relevant source IDs from
  server-authored fact/model/recommendation statements, not unrestricted prose.
  The server validates selection and renders only exact grounded statements.
  This constrained explanation mode cannot introduce new LLM factual claims;
  it is intentionally less expressive than free-form generation. LLM selection
  provenance stays separate from FACT/MODEL_OUTPUT/PERSONALIZED_RECOMMENDATION.
- Instructions are a fixed system message; question and retrieved summaries
  are JSON in a separate untrusted-data message. No tools/actions delegated to
  the provider. Raw resumes, JD bodies, application notes and profile contact
  details are omitted. External processing requires explicit request consent.
- Auth/foreign-resource/claim-control/provider-failure/injection tests use fake
  providers and synthetic PostgreSQL fixtures; no external or paid API calls.
- Phase F must pass backend, database/security and frontend checks before G.
  Phase G will add coherent navigation and compact current-state dashboard
  summaries, preserving existing intelligence and semantic distinctions.

## Phase F — verified checkpoint

Implemented the proposed stateless structured-grounding assistant. This is not
semantic RAG and does not claim research validation or unrestricted generation.

- Authenticated GET `/api/v1/assistant/status`, POST `/api/v1/assistant/chat`.
- Request: bounded message, explicit/automatic topic, optional owned JD/application
  IDs, explicit provider-processing consent. Extra fields (including user_id)
  rejected. All references ownership-checked even when unconfigured.
- Topic-based bounded retrieval uses existing services; maximum 12 statements /
  7,000 statement characters, with per-topic smaller record limits. Profile
  contact details, raw resumes/JDs, application notes, and previous conversation
  messages are not sent. No embeddings, Redis cache, or conversation persistence.
- FACT / MODEL_OUTPUT / PERSONALIZED_RECOMMENDATION source categories remain
  explicit. Provider selection is labeled LLM_EXPLANATION_SELECTION. Provider
  may return only up to eight unique known source IDs; unknown IDs, extra prose,
  duplicate IDs and malformed outputs are rejected. Answers render the exact
  selected server-authored statements. This prevents new generated factual claims
  but does not prove selection relevance; evaluation remains future work.
- Fixed system instructions and separately JSON-encoded untrusted question/context.
  No provider tools, actions, business-logic decisions or private data writes.
- Provider-neutral interface, optional stdlib OpenAI-compatible HTTPS adapter,
  no redirects/proxies, bounded timeout/response size, generic safe failures.
  Deterministic fake is injectable for tests only, never runtime-configurable.
- Optional environment configuration documented in `docs/ASSISTANT-CONFIGURATION.md`.
  No credentials/config files read or changed. No added dependencies.
- No provider => ASSISTANT_NOT_CONFIGURED, no context/provider call; core startup
  and services unaffected. Consent absent => CONSENT_REQUIRED. Missing context
  => INSUFFICIENT_CONTEXT. Provider/validation failure => PROVIDER_UNAVAILABLE,
  with no provider payload or private context exposed in errors.
- `/assistant`: starter prompts, question/topic selection, optional owned IDs,
  consent checkbox, loading/error/auth/not-configured/empty states, source links,
  limitations, and page-local message display capped at ten responses. Stateless
  question semantics are explicit. Request cleanup; no automatic paid retries.

Verification before Phase G: assistant tests **6 passed**; full configured-before-
discovery PostgreSQL-enabled suite **70 passed, zero skips**, including all eight
PostgreSQL cases. Tests cover foreign JD/application IDs (including no-provider),
current-user private goals/applications/evidence, omitted resume/notes payloads,
prompt-injection-like data, exact fact rendering, fake-provider determinism,
bounded context, malformed/extra provider claims, safe provider failures,
authentication, no consent/no context, and SELECT-only assistant retrieval.
External provider transport was mocked; no paid/external LLM calls were made.

Backend compilation, OpenAPI security assertions, Alembic current/heads and
`git diff --check` passed. Frontend tsc/lint/build passed with `/assistant`.
No migration: current/head still `b8d4e0f3c7a2`, one head. Existing outside-repo
lockfile/Windows line-ending warnings remain; no browser E2E claim.

Files: `backend/app/assistant/`, optional settings in `backend/app/core/config.py`,
main router registration, `backend/tests/test_assistant.py`,
`frontend/src/lib/api/assistant.ts`, `frontend/src/app/assistant/page.tsx`,
`docs/ASSISTANT-CONFIGURATION.md`, and this checkpoint.

Next: Phase G — dashboard/navigation integration only. No deployment or research
evaluation in this batch.

## Phase G — verified checkpoint

- Shared `AppNavigation` and one canonical destination registry connect all eleven
  major modules. Desktop wrapping links and a native expandable mobile menu use
  the same registry. Nested assessment routes stay under Assessments; existing
  `/evidence` remains accessible and maps to Skills & Evidence in navigation.
  No duplicate pages/routes created. Public login/register pages omit app nav.
- Root metadata now names CareerPilot AI and ACIF — Adaptive Career Intelligence
  Framework rather than starter-template text.
- Dashboard's existing target role / O*NET anchor, ACIF dimensions, gaps, Minimum
  Action Path, Career GPS and What-If sections remain authoritative and intact.
  Duplicate dashboard-only navigation was replaced by the shared navigation.
- Authenticated GET `/api/v1/dashboard/summary` composes read-only existing
  service results with owner-scoped aggregate queries. It returns compact current
  roadmap statuses, up to two certification recommendations, latest JD/current
  recorded-Twin alignment, real application status counts, recorded progress,
  resume/assessment onboarding signals and assistant configuration status.
- No new intelligence formulas, evidence writes, roadmap generation, provider
  calls, models or migrations. Dashboard does not test provider connectivity.
- `ModuleSummary` presents six concise cards with links to deeper module pages.
  Missing goals, mappings or Twin snapshots now show setup guidance and usable
  module summaries instead of an unusable error/blank dashboard. Unknown
  alignment/recommendations remain unavailable, not misleading zero scores.
- Empty states link to resume upload, assessment, JD analysis, application
  tracking, progress and unconfigured assistant. Network errors retain navigation
  and an independent summary retry. Dashboard async state is guarded on unmount.
- Saved JD offers a contextual assistant link with the owned JD ID; ownership
  is still checked server-side. No automatic provider submission occurs.

### Terminology audit

- Existing runtime dashboard uses authenticated target role and O*NET anchor;
  no Machine Learning Engineer/Data Scientists/15-2051.00 constant was found in
  the audited runtime dashboard/navigation. Existing onboarding example
  placeholders were intentionally retained as examples, not runtime data.
- Removed verification-timestamp inference from the Skills assessment badge.
  An actual ASSESSMENT evidence source with a measurement is required, including
  a valid measured zero. Resume strength alone does not imply assessment.
- Skills/Evidence cards now label the value as an assessment-derived estimate
  with an explicit assessment-specific, not universal-proficiency qualifier.
- Kept target role vs anchor, interests vs readiness, evidence vs proficiency,
  missing evidence vs missing skill, recommendation vs earned certification,
  and What-If vs prediction distinctions. JD alignment remains evidence alignment,
  never employment probability. No broad rewrite of correct existing UI.

## Final F–G verification receipt

All Python checks used `D:\CareerPilot-AI\.venv\Scripts\python.exe`.

- Backend compilation: `-m compileall -q backend` passed.
- Standard discovery: `-m unittest discover -s backend/tests`: **71 discovered,
  62 passed, 9 PostgreSQL opt-in cases skipped** as intended.
- Full PostgreSQL-enabled preloaded discovery (command recorded in Phase B):
  **71 passed, zero skips**, including all nine PostgreSQL cases.
- Assistant's six tests cover auth, no-provider/consent/context states, validated
  fake-provider generation, bounded current-user retrieval, foreign JD/app refs,
  real stored facts, privacy exclusions, injection-like strings, SELECT-only
  retrieval, malformed provider claims and sanitized failures. No paid APIs.
- Dashboard PostgreSQL test covers new-student empty states, other-user query
  manipulation, real status counts, latest owned JD, nullable alignment, private
  resume isolation, no-provider mode, no provider generation, and SELECT-only SQL.
- OpenAPI generated and JSON-serialized. Bearer security asserted on all **20**
  operations across assistant, dashboard, jobs, applications, Career Twin,
  resumes and skills. Existing assessment ownership tests also passed.
- Alembic current/heads: **b8d4e0f3c7a2 (head)**, one head, unchanged throughout
  this batch. No schema revision was added or applied to development data.
  Existing migration tests ran only within rolled-back synthetic schemas.
- `git diff --check`: passed. Existing LF/CRLF warnings remain.
- `node --test tests/navigation.test.mjs` from frontend: **4 passed**. Tests check
  all eleven unique existing routes, active nested/legacy navigation, assessment
  evidence semantics including zero, and absence of hard-coded test careers.
- Frontend `npx tsc --noEmit`, `npm run lint`, `npm run build`: all passed.
  Production build includes `/assistant` and all existing module routes.
- No existing browser/E2E framework was found, and none was installed. No
  authenticated browser acceptance claim. Tests are real ASGI/PostgreSQL,
  lightweight navigation/semantic tests, types/lint and production build.
- Existing outside-repository `D:/pnpm-lock.yaml` build warning remains.

### Files changed in this batch

- `backend/app/assistant/`: context, provider, schemas, service, router, package.
- `backend/app/dashboard/`: read-only summary schemas/service/router/package.
- `backend/app/core/config.py`, `backend/app/main.py`.
- `backend/tests/test_assistant.py`, `backend/tests/test_dashboard_summary.py`.
- `frontend/src/app/assistant/page.tsx`.
- `frontend/src/app/dashboard/ModuleSummary.tsx`, dashboard `page.tsx`.
- `frontend/src/components/AppNavigation.tsx`, `frontend/src/lib/navigation.ts`.
- `frontend/src/lib/api/assistant.ts`, `frontend/src/lib/api/dashboard.ts`.
- `frontend/src/lib/evidence-display.ts`, skills/evidence pages.
- `frontend/src/app/layout.tsx`, job-match page (contextual assistant entry).
- `frontend/tests/navigation.test.mjs`.
- `docs/ASSISTANT-CONFIGURATION.md`, `docs/REMAINING-V1-CHECKPOINT.md`.

### Remaining limits / handoff

- Assistant is intentionally constrained source selection, not unrestricted
  LLM-written advice. Factual membership is enforced; relevance/answer quality
  is not research-validated. Unsupported questions may remain unanswered.
- Structured grounding only. No semantic RAG, embedding corpus, vector search,
  conversation persistence, provider tool use, or automatic private-data writes.
- No live external-provider acceptance test; adapter transport is mocked.
  Operator must review data-handling terms, configure an approved HTTPS endpoint,
  model and secret privately, and test it before enabling student use.
- Rate limiting, quotas, operational monitoring, provider retention policies,
  broader privacy/accessibility review and browser-level end-to-end testing are
  still hardening work. Existing ACIF/assessment/Twin limitations remain.
- Entry Git state was clean; final tree contains only unstaged modifications
  and untracked F/G files. No commits, pushes, resets, cleans, staging, dependency
  installs, secret-file edits or applied-migration edits were performed.

**Next engineering phase: Security & Privacy Hardening + Full-System Testing.**
Stop after G. Do not claim production readiness, research validation, assistant
accuracy metrics or semantic RAG. Deployment/evaluation/report writing were not
started in this batch.
