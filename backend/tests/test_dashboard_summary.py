import os
import unittest
from unittest.mock import Mock

from backend.tests.synthetic_db import synthetic_database


@unittest.skipUnless(os.getenv("CAREERPILOT_POSTGRES_TEST") == "1", "opt-in PostgreSQL integration")
class DashboardSummaryPostgresTests(unittest.TestCase):
    def test_new_student_private_summaries_no_provider_and_read_only(self):
        from sqlalchemy import event
        from backend.app.main import app
        from backend.app.assistant.provider import get_assistant_provider
        from backend.app.resumes.models import Resume
        path = "/api/v1/dashboard/summary"
        with synthetic_database() as (db, users, call, connection):
            app.dependency_overrides[get_assistant_provider] = lambda: None
            self.assertEqual(call(user=None, path=path)[0], 401)
            status, empty = call(path=path)
            self.assertEqual(status, 200, empty)
            self.assertEqual(empty["resume_count"], 0)
            self.assertEqual(empty["completed_assessment_attempts"], 0)
            self.assertEqual(empty["application_total"], 0)
            self.assertIsNone(empty["latest_jd"])
            self.assertIsNone(empty["latest_alignment"])
            self.assertEqual(empty["certification_status"], "UNAVAILABLE")
            self.assertEqual(empty["progress"]["message"], "Not enough history yet.")
            self.assertEqual(empty["assistant"]["provider_status"], "ASSISTANT_NOT_CONFIGURED")
            jd = call(method="POST", payload={"title": "Owned JD A", "source_text": "Python required."})[1]
            call(user=1, method="POST", payload={"title": "PRIVATE_OTHER_JD", "source_text": "Java required."})
            for user, status in ((0, "INTERVIEW"), (0, "APPLIED"), (1, "OFFER")):
                call(user=user, method="POST", path="/api/v1/applications", payload={"company": "Synthetic", "job_title": "Role", "status": status})
            db.add(Resume(user_id=users[1].id, title="PRIVATE_OTHER_RESUME")); db.commit(); db.connection()
            statements = []
            def capture(conn, cursor, statement, parameters, context, executemany):
                statements.append(statement.strip().split()[0].upper())
            event.listen(connection, "before_cursor_execute", capture)
            try:
                status, summary = call(path=path, query=f"user_id={users[1].id}".encode())
                self.assertEqual(status, 200, summary)
                self.assertEqual(summary["application_total"], 2)
                self.assertEqual(summary["application_status_counts"]["INTERVIEW"], 1)
                self.assertEqual(summary["application_status_counts"]["OFFER"], 0)
                self.assertEqual(summary["latest_jd"]["id"], jd["id"])
                self.assertIsNone(summary["latest_alignment"]["value"])
                self.assertEqual(summary["resume_count"], 0)
                self.assertNotIn("PRIVATE_OTHER", str(summary))
                other = call(user=1, path=path)[1]
                self.assertEqual(other["resume_count"], 1)
                self.assertEqual(other["application_total"], 1)
                configured = Mock()
                app.dependency_overrides[get_assistant_provider] = lambda: configured
                self.assertEqual(call(path=path)[1]["assistant"]["provider_status"], "READY")
                configured.generate.assert_not_called()
                self.assertEqual(set(statements), {"SELECT"})
                self.assertFalse(db.new or db.dirty or db.deleted)
            finally:
                event.remove(connection, "before_cursor_execute", capture)
