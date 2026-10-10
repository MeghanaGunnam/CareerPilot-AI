# Career assumptions and assessment checkpoint

## Latest assessment-phase checkpoint

The sections below describe the earlier checkpoint; this section supersedes its
open catalog/testing/lint items. Certification work has not begun.

- Controlled Java v1 (5), Critical Thinking v1 (5), Python v1 (10), SQL v1 (10)
  are seeded and active. Repeat seed creates nothing. Existing attempts remain.
- Catalog IDs, domains, provenance, deterministic version IDs for new entries,
  validation and seed-time drift refusal are documented in ASSESSMENT-CATALOG.md.
- Authenticated recommendations/me resolves the primary goal server-side; the
  frontend uses it. Python/SQL require exact normalized in-demand software
  signals, not loose substring matches or invented competency equivalences.
- Submission evidence includes structured assessment/version/attempt/skill/score
  and timestamp provenance. Score remains assessment performance.
- History routes and user scoping are retained.
- Evidence-page effect now handles async completion and unmount cancellation;
  the lint rule remains enabled.
- Verification: 29 unittest cases ran successfully (28 passed, one opt-in
  PostgreSQL integration skipped); the PostgreSQL integration ran separately
  and passed. It uses a synthetic transaction-local schema and rolls back.
- Backend compileall, OpenAPI generation, TypeScript, full lint, production
  build and diff-check passed. Migration current/head remain f4a2b7c9d1e3.
- No migration, dependency installation, commit or push in this phase.

Limitations: seed policy does not prevent arbitrary direct SQL edits; snapshot
creation and submission still commit separately; no authenticated browser E2E
test. No Machine Learning assessment or psychometric validation is claimed.

## Scope and findings

The working tree was clean at entry. The existing database and migration head
were both `f4a2b7c9d1e3`. No reset, commit, push, or migration was performed.

Tracked source search (excluding the O*NET dataset) for Machine Learning Engineer,
Data Scientist(s), and 15-2051.00 found only two occurrences:

- `frontend/src/app/onboarding/CareerGoalStep.tsx`: input placeholder.
- `frontend/src/components/onboarding/CareerGoalStep.tsx`: input placeholder.

Both are illustrative text, not stored defaults or recommendation logic. They
were retained. O*NET dataset occurrences represent occupational knowledge, not
application defaults; individual dataset rows and private database goals were
not enumerated in this audit.

The career resolver matches the supplied SOC code exactly. Assessment
recommendations select requirements for the supplied career ID and measurement
state for the authenticated user. Existing roadmap generation uses the user's
primary career goal. No replacement hard-coded role was introduced.

## Implemented assessment extension

- Authenticated, paginated `GET /api/v1/assessments/attempts`.
- Ownership-scoped `GET /api/v1/assessments/attempts/{attempt_id}`.
- Catalog question counts and latest current-user attempt.
- Shared persisted-result serialization for submission and result retrieval.
- Existing `/assessment` page now displays history and reopens saved results.
- Confirmation and synchronous click guard for submission; input/exit controls
  are disabled during submission.
- Scores are labeled as assessment scores, never universal proficiency.

No schema migration is necessary for this extension.

## Verification

- Project virtual environment unittest suite: 9 tests passed.
- Tests exercise mocked sessions, ownership SQL predicates, route dependencies,
  pagination, response serialization, and inactive-assessment history.
- Backend compileall passed.
- Next.js production build passed.
- TypeScript check passed.
- Full lint failed at the existing evidence page hook rule, line 228.
- No authenticated browser flow or live cross-user HTTP test was performed.

Installed package metadata reports FastAPI 0.142.2 and Starlette 1.7.0.
Starlette's declared full extra includes both httpx2 and httpx. This explains
the earlier TestClient error; it must not be treated as proof that installing
an arbitrary similarly named package is appropriate. No package was installed.

## Open work before certification recommendations

1. Add controlled Python/SQL and other justified assessment bank entries;
   validate option keys, question positions, and version policy before seeding.
2. Enforce append-only assessment/question version policy: current history reads
   title/version/explanations from related rows and could change if edited in place.
3. Extend recommendations beyond explicit competency mappings to justified
   technology-signal matches. Add tests demonstrating different careers and
   current evidence produce different recommendations. That behavior has not
   yet been runtime verified.
4. Add full submission/evidence/snapshot integration tests. The click guard is
   not server-side idempotency for ambiguous network retries.
5. Fix evidence-page lint without disabling rules, then repeat all checks.
6. Report the completed prerequisite audit before implementing certifications.

The overall V1 and the full assessment architecture expansion are not complete.
