import importlib.util
import os
from pathlib import Path
import unittest
import uuid

from pydantic import ValidationError
from backend.app.applications.schemas import ApplicationCreate, ApplicationUpdate
from backend.tests.synthetic_db import synthetic_database


class ApplicationInputTests(unittest.TestCase):
    def test_create_validation_and_partial_update(self):
        valid = {"company": "Example", "job_title": "Engineer"}
        self.assertEqual(ApplicationCreate(**valid).status, "SAVED")
        self.assertEqual(ApplicationUpdate(notes=None).model_dump(exclude_unset=True), {"notes": None})
        for values in ({"company": " "}, {"job_title": "x\ny"}, {"status": "HIRED"}, {"job_url": "file:///tmp"}, {"notes": "a\0b"}, {"user_id": str(uuid.uuid4())}):
            with self.subTest(values=values), self.assertRaises(ValidationError):
                ApplicationCreate(**{**valid, **values})
        for field in ("company", "job_title", "status"):
            with self.assertRaises(ValidationError):
                ApplicationUpdate(**{field: None})


@unittest.skipUnless(os.getenv("CAREERPILOT_POSTGRES_TEST") == "1", "opt-in PostgreSQL integration")
class ApplicationsPostgresTests(unittest.TestCase):
    def test_migration_crud_ownership_filtering_links_and_cascades(self):
        from alembic.migration import MigrationContext
        from alembic.operations import Operations
        from sqlalchemy import delete, inspect, select
        from backend.app.applications.models import Application
        from backend.app.auth.models import User
        from backend.app.jobs.models import JDAnalysis
        migration_path = Path(__file__).resolve().parents[1] / "alembic/versions/b8d4e0f3c7a2_create_applications.py"
        spec = importlib.util.spec_from_file_location("application_migration", migration_path)
        migration = importlib.util.module_from_spec(spec); spec.loader.exec_module(migration)
        self.assertEqual(migration.down_revision, "a7c3d9e2b6f1")
        with synthetic_database(exclude={"applications"}) as (db, users, call, connection):
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
            self.assertIn("applications", inspect(connection).get_table_names())
            root = "/api/v1/applications"
            jd = call(method="POST", payload={"title": "JD", "source_text": "Python required."})[1]
            for method, path, payload in (("GET", root, None), ("POST", root, {"company": "Example", "job_title": "Role"}), ("GET", root + "/" + str(uuid.uuid4()), None)):
                self.assertEqual(call(user=None, method=method, path=path, payload=payload)[0], 401)
            status, first = call(method="POST", path=root, payload={"company": "Example", "job_title": "Role", "jd_analysis_id": jd["id"], "location": "Remote"})
            self.assertEqual(status, 201, first)
            path = root + "/" + first["id"]
            self.assertEqual(first["status"], "SAVED")
            db.expire_all()
            self.assertEqual(call(path=path), (200, first))
            before_time = first["updated_at"]
            status, updated = call(method="PATCH", path=path, payload={"status": "APPLIED", "applied_date": "2026-10-10", "notes": "Sent application"})
            self.assertEqual(status, 200)
            self.assertEqual(updated["created_at"], first["created_at"])
            self.assertGreaterEqual(updated["updated_at"], before_time)
            self.assertEqual(updated["company"], "Example")
            self.assertEqual(updated["applied_date"], "2026-10-10")
            for method, payload in (("GET", None), ("PATCH", {"notes": "intrusion"}), ("PATCH", {"status": "OFFER"}), ("DELETE", None)):
                self.assertEqual(call(user=1, method=method, path=path, payload=payload), call(user=1, method=method, path=root + "/" + str(uuid.uuid4()), payload=payload))
                self.assertEqual(call(user=1, method=method, path=path, payload=payload)[0], 404)
            self.assertEqual(call(user=1, path=root)[1]["total"], 0)
            foreign_link = {"company": "Other", "job_title": "Other", "jd_analysis_id": jd["id"]}
            self.assertEqual(call(user=1, method="POST", path=root, payload=foreign_link)[0], 404)
            self.assertEqual(call(method="POST", path=root, payload={**foreign_link, "jd_analysis_id": str(uuid.uuid4())})[0], 404)
            other = call(user=1, method="POST", path=root, payload={"company": "Other", "job_title": "No JD"})[1]
            self.assertIsNone(other["jd_analysis_id"])
            self.assertEqual(call(user=1, method="PATCH", path=root + "/" + other["id"], payload={"jd_analysis_id": jd["id"]})[0], 404)
            for status in ("ASSESSMENT", "INTERVIEW", "OFFER", "REJECTED", "WITHDRAWN", "APPLIED"):
                self.assertEqual(call(method="PATCH", path=path, payload={"status": status})[1]["status"], status)
            call(method="POST", path=root, payload={"company": "Example2", "job_title": "Role2"})
            pages = [call(path=root, query=f"limit=1&offset={offset}".encode())[1] for offset in (0, 1)]
            self.assertEqual([page["total"] for page in pages], [2, 2])
            self.assertNotEqual(pages[0]["items"][0]["id"], pages[1]["items"][0]["id"])
            self.assertEqual(call(path=root, query=b"status=APPLIED")[1]["total"], 1)
            for query in (b"status=HIRED", b"limit=0", b"offset=-1"):
                self.assertEqual(call(path=root, query=query)[0], 422)
            self.assertEqual(call(method="PATCH", path=path, payload={"status": "HIRED"})[0], 422)
            self.assertEqual(call(method="PATCH", path=path, payload={"jd_analysis_id": None, "notes": None})[1]["jd_analysis_id"], None)
            self.assertEqual(call(method="PATCH", path=path, payload={"jd_analysis_id": jd["id"]})[0], 200)
            db.execute(delete(JDAnalysis).where(JDAnalysis.id == uuid.UUID(jd["id"]))); db.commit(); db.expire_all()
            self.assertIsNone(call(path=path)[1]["jd_analysis_id"])
            self.assertEqual(call(method="DELETE", path=path)[0], 204)
            self.assertEqual(call(path=path)[0], 404)
            db.execute(delete(User).where(User.id == users[0].id)); db.commit()
            self.assertEqual(len(db.scalars(select(Application)).all()), 1)
            self.assertEqual(call(user=1, path=root)[1]["items"][0]["id"], other["id"])
            db.rollback()
            with Operations.context(MigrationContext.configure(connection)):
                migration.downgrade()
            self.assertNotIn("applications", inspect(connection).get_table_names())
