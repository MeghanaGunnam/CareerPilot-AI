"""Opt-in: migration, real ASGI persistence and ownership in a rolled-back schema."""
import importlib.util
import os
from pathlib import Path
import unittest
import uuid
from unittest.mock import patch


@unittest.skipUnless(os.getenv("CAREERPILOT_POSTGRES_TEST") == "1", "opt-in PostgreSQL integration")
class JobsPostgresTests(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        from backend.app.core.database import engine
        engine.dispose()

    def test_applied_jd_schema_matches_models(self):
        """Read schema metadata only; no private application rows are inspected."""
        from sqlalchemy import CheckConstraint, inspect
        from backend.app.core.database import engine
        from backend.app.jobs.models import JDAnalysis, Requirement

        inspector = inspect(engine)
        for model in (JDAnalysis, Requirement):
            table = model.__table__
            columns = {column["name"]: column for column in inspector.get_columns(table.name)}
            self.assertEqual(set(columns), set(table.columns.keys()))
            for column in table.columns:
                self.assertEqual(columns[column.name]["nullable"], column.nullable)
                self.assertEqual(str(columns[column.name]["type"].compile(engine.dialect)), str(column.type.compile(engine.dialect)))
            actual_checks = {constraint["name"] for constraint in inspector.get_check_constraints(table.name)}
            expected_checks = {constraint.name for constraint in table.constraints if isinstance(constraint, CheckConstraint)}
            self.assertEqual(actual_checks, expected_checks)
            foreign_keys = inspector.get_foreign_keys(table.name)
            self.assertEqual(len(foreign_keys), 1)
            self.assertEqual(foreign_keys[0]["options"].get("ondelete"), "CASCADE")
            expected_parent = ("users", "user_id") if table.name == "jd_analyses" else ("jd_analyses", "analysis_id")
            self.assertEqual(foreign_keys[0]["referred_table"], expected_parent[0])
            self.assertEqual(foreign_keys[0]["constrained_columns"], [expected_parent[1]])
            self.assertEqual({index["name"] for index in inspector.get_indexes(table.name) if not index.get("duplicates_constraint")}, {index.name for index in table.indexes})
        self.assertIn(["analysis_id", "position"], [constraint["column_names"] for constraint in inspector.get_unique_constraints("jd_requirements")])

    def test_migration_api_persistence_isolation_constraints_and_cascade(self):
        from alembic.migration import MigrationContext
        from alembic.operations import Operations
        from sqlalchemy import delete, func, inspect, select, text
        from sqlalchemy.exc import IntegrityError
        from sqlalchemy.orm import Session
        from backend.app.auth.models import User
        from backend.app.auth.dependencies import get_current_user
        from backend.app.auth.security import create_access_token
        from backend.app.core.database import Base, engine, get_db
        from backend.app.jobs.models import JDAnalysis, Requirement
        from backend.app.jobs.extractor import EXTRACTOR_VERSION
        from backend.app.main import app
        from backend.tests.test_jobs import request as api_request

        self.assertEqual(engine.dialect.name, "postgresql")
        schema = "jobs_test_" + uuid.uuid4().hex
        path = Path(__file__).resolve().parents[1] / "alembic/versions/a7c3d9e2b6f1_create_jd_analyses.py"
        spec = importlib.util.spec_from_file_location("jd_migration", path)
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        self.assertEqual(migration.down_revision, "f4a2b7c9d1e3")
        saved = app.dependency_overrides.copy()
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                Base.metadata.create_all(connection, tables=[t for t in Base.metadata.sorted_tables if t.name not in {"jd_analyses", "jd_requirements", "applications"}])
                with Operations.context(MigrationContext.configure(connection)):
                    migration.upgrade()
                self.assertIn("jd_requirements", inspect(connection).get_table_names(schema=schema))
                with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
                    users = [User(email=f"jobs-{i}@example.invalid", password_hash="synthetic") for i in range(2)]
                    db.add_all(users)
                    db.commit()
                    app.dependency_overrides[get_db] = lambda: db
                    app.dependency_overrides.pop(get_current_user, None)
                    # Exercise the real Bearer decoder and authenticated DB lookup.
                    # Tokens exist only in memory and are never printed or saved.
                    tokens = [create_access_token(user.id)[0] for user in users]
                    current_user = 0
                    def request(*args, **kwargs):
                        return api_request(*args, headers=[(b"authorization", f"Bearer {tokens[current_user]}".encode())], **kwargs)

                    self.assertEqual(api_request()[0], 401)
                    self.assertEqual(api_request(headers=[(b"authorization", b"Bearer invalid")])[0], 401)
                    source = "  🚀 Role\r\nPython experience is not required.\r\n3+ years experience\nBachelor’s degree\nResponsibilities:\nBuild APIs\nPreferred:\nDocker\n"
                    status, created = request("POST", payload={"title": " Example ", "company": "Synthetic", "source_text": source, "source_url": "https://example.invalid/job"})
                    self.assertEqual(status, 201, created)
                    analysis_id = created["id"]
                    detail_path = f"/api/v1/jobs/analyses/{analysis_id}"
                    db.expire_all()
                    status, loaded = request(path=detail_path)
                    self.assertEqual(status, 200, loaded)
                    self.assertEqual(created, loaded)
                    self.assertEqual(loaded["source_text"], source)
                    self.assertEqual(loaded["extractor_version"], EXTRACTOR_VERSION)
                    python = next(row for row in loaded["requirements"] if row["normalized_name"] == "python")
                    self.assertEqual(python["quote"], "Python experience is not required.")
                    self.assertEqual(python["interpretation_type"], "NORMALIZED_INTERPRETATION")
                    with patch("backend.app.jobs.service.extract_requirements", side_effect=AssertionError("Reads must not re-extract")):
                        self.assertEqual(request(path=detail_path), (200, loaded))
                    self.assertEqual({r["group"] for r in loaded["requirements"]}, {"technology", "experience", "education", "responsibility", "preferred"})
                    for row in loaded["requirements"]:
                        self.assertEqual(source[row["source_start"]:row["source_end"]], row["quote"])
                    self.assertEqual(db.scalar(select(func.count()).select_from(Requirement)), created["requirement_count"])
                    status, listing = request()
                    self.assertEqual((status, listing["total"], len(listing["items"])), (200, 1, 1))
                    self.assertNotIn("source_text", listing["items"][0])
                    self.assertEqual(request(query=b"limit=1&offset=1")[1]["items"], [])

                    # POST is deliberately non-idempotent: identical inputs create
                    # separate records, but extracted semantic content is stable.
                    status, repeated = request("POST", payload={"title": " Example ", "company": "Synthetic", "source_text": source, "source_url": "https://example.invalid/job"})
                    self.assertEqual(status, 201)
                    self.assertNotEqual(repeated["id"], analysis_id)
                    semantic = lambda rows: [{key: value for key, value in row.items() if key != "id"} for row in rows]
                    self.assertEqual(semantic(repeated["requirements"]), semantic(created["requirements"]))
                    pages = [request(query=f"limit=1&offset={offset}".encode())[1] for offset in (0, 1)]
                    self.assertEqual([page["total"] for page in pages], [2, 2])
                    self.assertEqual([page["offset"] for page in pages], [0, 1])
                    self.assertEqual({page["items"][0]["id"] for page in pages}, {analysis_id, repeated["id"]})
                    self.assertEqual(request(query=b"limit=1&offset=2")[1]["items"], [])
                    self.assertEqual(request(query=b"limit=1&offset=0")[1], pages[0])

                    current_user = 1
                    self.assertEqual(request()[1]["total"], 0)
                    foreign = request(path=detail_path)
                    missing = request(path=f"/api/v1/jobs/analyses/{uuid.uuid4()}")
                    self.assertEqual(foreign, missing)
                    self.assertEqual(foreign[0], 404)
                    self.assertEqual(api_request(path=detail_path)[0], 401)
                    for method in ("PUT", "PATCH", "DELETE"):
                        self.assertEqual(request(method, path=detail_path)[0], 405)
                    status, unsupported = request("POST", payload={"title": "Other role", "source_text": "UnlistedTool 9000"})
                    self.assertEqual(status, 201)
                    self.assertEqual(unsupported["requirements"], [])
                    self.assertEqual(unsupported["requirement_count"], 0)
                    self.assertEqual([item["id"] for item in request()[1]["items"]], [unsupported["id"]])
                    users[1].is_active = False
                    db.commit()
                    self.assertEqual(request()[0], 403)
                    self.assertEqual(request(path=detail_path)[0], 403)
                    self.assertEqual(request("POST", payload={"title": "Blocked", "source_text": "Python"})[0], 403)
                    users[1].is_active = True
                    db.commit()
                    for payload in ({"title": "Role", "source_text": " "}, {"title": "Role", "source_text": "x" * 30001},
                                    {"title": "Role", "source_text": "Python", "source_url": "file:///tmp"}):
                        self.assertEqual(request("POST", payload=payload)[0], 422)
                    self.assertEqual(db.scalar(select(func.count()).select_from(JDAnalysis)), 3)
                    # PostgreSQL rejects invalid child spans without corrupting saved data.
                    with self.assertRaises(IntegrityError):
                        with db.begin_nested():
                            db.add(Requirement(analysis_id=uuid.UUID(analysis_id), position=99, group="technology", quote="bad", source_start=5, source_end=2, evidence_type="FACT_FROM_JD"))
                            db.flush()
                    db.execute(delete(User).where(User.id == users[0].id))
                    db.commit()
                    self.assertEqual(db.scalar(select(func.count()).select_from(JDAnalysis)), 1)
                    self.assertEqual(db.scalar(select(func.count()).select_from(Requirement)), 0)
                    self.assertEqual(request(path=f"/api/v1/jobs/analyses/{unsupported['id']}")[0], 200)
                    db.execute(delete(User).where(User.id == users[1].id))
                    db.commit()
                    self.assertEqual(db.scalar(select(func.count()).select_from(JDAnalysis)), 0)
                with Operations.context(MigrationContext.configure(connection)):
                    migration.downgrade()
                self.assertNotIn("jd_analyses", inspect(connection).get_table_names(schema=schema))
            finally:
                app.dependency_overrides.clear()
                app.dependency_overrides.update(saved)
                outer.rollback()
            self.assertIsNone(connection.scalar(text("SELECT to_regnamespace(:schema)"), {"schema": schema}))


if __name__ == "__main__":
    unittest.main()
