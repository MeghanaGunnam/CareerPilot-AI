import copy
import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

from backend.app.career_twin.progress import compare_snapshots, recorded_counts
from backend.tests.synthetic_db import synthetic_database


class ProgressSemanticsTests(unittest.TestCase):
    def test_no_history_single_history_and_explicit_zero(self):
        self.assertTrue(all(row["change"] is None for row in compare_snapshots(None, None)))
        one = NS(schema_version="1.0", state_data={"skills": []})
        self.assertEqual(recorded_counts(one), {"skill_records": 0, "evidence_entries": 0, "assessment_evidence_entries": 0})
        self.assertTrue(all(row["change"] is None for row in compare_snapshots(one, None)))

    def test_missing_fields_unknown_schema_and_malformed_history_not_zero(self):
        for payload in ({}, {"skills": None}, {"skills": ["invalid"]}):
            self.assertTrue(all(value is None for value in recorded_counts(NS(schema_version="1.0", state_data=payload)).values()))
        partial = recorded_counts(NS(schema_version="1.0", state_data={"skills": [{"name": "Python"}]}))
        self.assertEqual(partial["skill_records"], 1)
        self.assertIsNone(partial["evidence_entries"])
        unknown = NS(schema_version="future", state_data={"skills": []})
        self.assertTrue(all(value is None for value in recorded_counts(unknown).values()))
        self.assertTrue(all(row["change"] is None for row in compare_snapshots(unknown, NS(schema_version="1.0", state_data={"skills": []}))))

    def test_recorded_changes_can_decrease_and_never_reconstruct_scores(self):
        old = NS(schema_version="1.0", state_data={"skills": [{"evidence": [{"source_type": "RESUME"}, {"source_type": "ASSESSMENT", "evidence_strength": 0}]}]})
        new = NS(schema_version="1.0", state_data={"skills": [{"evidence": [{"source_type": "ASSESSMENT", "evidence_strength": 0}]}]})
        original = copy.deepcopy(old.state_data)
        self.assertEqual([row["change"] for row in compare_snapshots(new, old)], [0, -1, 0])
        self.assertEqual(old.state_data, original)
        self.assertNotIn("technology_coverage", recorded_counts(new))


@unittest.skipUnless(os.getenv("CAREERPILOT_POSTGRES_TEST") == "1", "opt-in PostgreSQL integration")
class ProgressPostgresTests(unittest.TestCase):
    def test_owned_history_events_roadmap_assessments_paging_and_read_only(self):
        from sqlalchemy import event
        from backend.app.career_twin.models import CareerTwin, CareerTwinEvent, CareerTwinSnapshot
        from backend.app.roadmap.models import RoadmapItem
        from backend.app.students.models import CareerGoal
        from backend.app.skills.models import Skill
        from backend.app.assessments.models import Assessment, AssessmentAttempt
        path = "/api/v1/career-twin/progress"
        now = datetime.now(timezone.utc)
        with synthetic_database() as (db, users, call, connection):
            self.assertEqual(call(user=None, path=path)[0], 401)
            empty = call(path=path)[1]
            self.assertEqual(empty["history_status"], "NOT_ENOUGH_HISTORY")
            self.assertEqual(empty["history_message"], "Not enough history yet.")
            self.assertIsNone(empty["career_twin_id"])
            self.assertEqual(empty["events"], [])
            twins = [CareerTwin(user_id=user.id, current_version=1) for user in users[:2]]
            db.add_all(twins); db.flush()
            first = CareerTwinSnapshot(career_twin_id=twins[0].id, version=1, trigger_type="SYNTHETIC_FIRST", state_data={"skills": []}, created_at=now - timedelta(days=1))
            private = CareerTwinSnapshot(career_twin_id=twins[1].id, version=1, trigger_type="OTHER_USER_PRIVATE", state_data={"skills": [{"evidence": []}]}, created_at=now)
            db.add_all([first, private]); db.commit()
            single = call(path=path)[1]
            self.assertEqual(single["snapshot_total"], 1)
            self.assertEqual(single["history_status"], "NOT_ENOUGH_HISTORY")
            second = CareerTwinSnapshot(career_twin_id=twins[0].id, version=2, trigger_type="SYNTHETIC_SECOND", state_data={"skills": [{"evidence": [{"source_type": "ASSESSMENT", "evidence_strength": 0}]}]}, created_at=now)
            db.add(second)
            for index, twin in enumerate(twins):
                db.add(CareerTwinEvent(career_twin_id=twin.id, event_type="SNAPSHOT_CREATED", source_type="SYNTHETIC", event_data={"snapshot_version": 1}, occurred_at=now - timedelta(days=1)))
                if index == 0:
                    db.add(CareerTwinEvent(career_twin_id=twin.id, event_type="SNAPSHOT_CREATED", source_type="SYNTHETIC", event_data={"snapshot_version": 2}, occurred_at=now))
                goal = CareerGoal(user_id=users[index].id, target_role="Synthetic goal", is_primary=True)
                db.add(goal); db.flush()
                for number, status in enumerate(("NOT_STARTED", "IN_PROGRESS", "COMPLETED", "SKIPPED") if index == 0 else ("COMPLETED",)):
                    db.add(RoadmapItem(user_id=users[index].id, career_goal_id=goal.id, item_key=f"synthetic-{number}", provenance="SYNTHETIC", current_evidence_state="UNKNOWN", reason="Synthetic", recommended_action="Synthetic", evidence_building_action="Synthetic", milestone="Synthetic", status=status, display_order=number, model_version="test", snapshot_version=1))
            skill = Skill(canonical_name="Synthetic progress skill")
            db.add(skill); db.flush()
            assessment = Assessment(skill_id=skill.id, title="Synthetic", difficulty="BEGINNER")
            db.add(assessment); db.flush()
            db.add_all([AssessmentAttempt(user_id=users[0].id, assessment_id=assessment.id, status="COMPLETED", completed_at=now), AssessmentAttempt(user_id=users[1].id, assessment_id=assessment.id, status="COMPLETED", completed_at=now), AssessmentAttempt(user_id=users[0].id, assessment_id=assessment.id, status="IN_PROGRESS")])
            db.commit(); db.connection()
            statements = []
            def capture(conn, cursor, statement, parameters, context, executemany):
                statements.append(statement.strip().split()[0].upper())
            event.listen(connection, "before_cursor_execute", capture)
            try:
                status, result = call(path=path)
                self.assertEqual(status, 200, result)
                self.assertEqual(result["history_status"], "COMPARABLE_HISTORY")
                self.assertEqual([row["change"] for row in result["comparison"]], [1, 1, 1])
                self.assertEqual([snapshot["version"] for snapshot in result["snapshots"]], [2, 1])
                self.assertEqual([entry["snapshot_version"] for entry in result["events"]], [2, 1])
                self.assertEqual(result["roadmap_status_counts"], {"NOT_STARTED": 1, "IN_PROGRESS": 1, "COMPLETED": 1, "SKIPPED": 1})
                self.assertEqual(result["completed_assessment_attempts"], 1)
                self.assertEqual(call(path=path, query=f"user_id={users[1].id}&career_twin_id={twins[1].id}".encode())[1], result)
                other = call(user=1, path=path, query=f"user_id={users[0].id}".encode())[1]
                self.assertEqual(other["career_twin_id"], str(twins[1].id))
                self.assertEqual(other["snapshot_total"], 1)
                self.assertEqual(other["roadmap_total"], 1)
                self.assertEqual(other["event_total"], 1)
                self.assertEqual(call(user=2, path=path)[1]["snapshot_total"], 0)
                page = call(path=path, query=b"limit=1&offset=1&event_offset=1")[1]
                self.assertEqual(page["snapshots"][0]["version"], 1)
                self.assertEqual(page["events"][0]["snapshot_version"], 1)
                self.assertEqual(page["current_snapshot"]["version"], 2)
                for query in (b"limit=0", b"offset=-1", b"event_offset=-1"):
                    self.assertEqual(call(path=path, query=query)[0], 422)
                self.assertNotIn("OTHER_USER_PRIVATE", str(result))
                self.assertEqual(set(statements), {"SELECT"})
                self.assertFalse(db.new or db.dirty or db.deleted)
            finally:
                event.remove(connection, "before_cursor_execute", capture)
