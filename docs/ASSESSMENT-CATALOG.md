# Controlled assessment catalog

`backend/app/assessments/catalog.py` defines stable catalog IDs, versions, canonical
skills, domains, initial active state, and truthful provenance. Python and SQL each
have 10 original application-authored questions. Java and Critical Thinking retain
their five original questions unchanged. These quizzes are formative evidence, not
standardized or psychometrically validated examinations.

Integration helper: `get_controlled_catalog_metadata(assessment, skill_name=None)`
returns a dictionary (`catalog_id`, `version`, `skill_name`, `title`, `domain`,
`is_active`, `provenance`) or `None` for unknown content. Pass the canonical skill
name explicitly to avoid relationship loading. No answers are included. Domains:
`PROGRAMMING`, `REASONING`, `DATABASES`. Database active state takes precedence.

## Append-only version policy

Published identity/version, skill, title, description, difficulty, ordered questions,
options, answer keys and explanations are immutable. Corrections require appending
a higher version to both manifest and bank while retaining the old definition.
Do not edit/delete historical rows or rewrite attempt foreign keys. Explicit
administrative retirement may change `is_active`; re-seeding preserves it.

The existing schema has no metadata column: controlled metadata lives in the
versioned manifest, while version/active state use existing database fields. New
assessment UUIDs derive deterministically from catalog ID/version; legacy UUIDs
are preserved. Runtime lookup requires exact skill/title/version. The conservative
seeder refuses multiple assessments for the same skill/version or a conflicting
title rather than guessing which historical row to adopt.

Use `seed_technical_assessments` with a clean dedicated SQLAlchemy session. It
validates the full bank, checks every existing version for exact content equality,
and only then appends missing rows in one transaction. Failure rolls back. A
PostgreSQL transaction advisory lock serializes cooperating seeders. It does not
prevent unrelated direct SQL writers; the schema has no catalog uniqueness index.

Missing Python/SQL skills are created under exact canonical names. Case/whitespace
variants and duplicates are refused for manual resolution, never merged. Missing
canonical Java/Critical Thinking skills are also created to support their preserved
assessments on installations that lack them. No O*NET mappings, user evidence, competency
equivalences or recommendations are created or changed.

Run catalog checks from the repository root:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.tests.test_assessment_catalog -v
```

## Verified local seed (2026-10-10)

The configured database was confirmed as local and `development`. Eleven catalog
unittests passed using the existing `.venv` with no installations. Tests exercise
real SQLAlchemy persistence in isolated SQLite (JSONB compiled as JSON); the actual
PostgreSQL seed and repeat run also succeeded.

| Entity | Before | After |
| --- | ---: | ---: |
| Assessments | 1 | 4 |
| Questions | 5 | 30 |
| Attempts | 6 | 6 |
| Skills | 21 | 22 |
| O*NET skill mappings | 0 | 0 |

The first seed created three assessments and 25 questions, preserved the existing
Java assessment, and created the missing Critical Thinking canonical skill.
Python/SQL skills already existed. Repeating the seed skipped all four assessments
and created zero rows. Readback confirmed active v1 assessments with question counts
Java 5, Critical Thinking 5, Python 10, SQL 10. An initial preflight identified the
missing Critical Thinking skill and rolled back without writes; canonical bootstrap
support was then added and tested before the successful seed.
