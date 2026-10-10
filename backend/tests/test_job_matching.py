import copy
import os
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace as NS
from unittest.mock import patch

from backend.app.acif.engine import calculate_all_skill_states
from backend.app.jobs.matching import compare_requirements
from backend.tests.synthetic_db import synthetic_database

NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)


def analysis_for(clauses, version="jd-literal-v2", truncated=False):
    text = "\n\n".join(quote for quote, canonical in clauses)
    rows, start = [], 0
    for position, (quote, canonical) in enumerate(clauses):
        rows.append(NS(id=uuid.uuid4(), position=position, group="technology", quote=quote,
                       source_start=start, source_end=start + len(quote), normalized_name=canonical,
                       evidence_type="FACT_FROM_JD", interpretation_type="NORMALIZED_INTERPRETATION" if canonical else None))
        start += len(quote) + 2
    return NS(id=uuid.uuid4(), source_text=text, requirements=rows, extractor_version=version, truncated=truncated)


def skill(name, sources):
    return {"skill_id": str(uuid.uuid4()), "name": name, "evidence": [
        {"id": str(uuid.uuid4()), "source_type": source, "evidence_status": "VERIFIED", "observed_at": NOW.isoformat(), "evidence_strength": strength}
        for source, strength in sources
    ]}


class JobMatchingTests(unittest.TestCase):
    def test_states_measurement_and_explainable_deduplicated_aggregate(self):
        analysis = analysis_for([("Python is required.", "python"), ("Python is essential.", "python"), ("SQL is required.", "sql"), ("Java is mandatory.", "java"), ("Degree required.", None)])
        states = calculate_all_skill_states({"skills": [skill("Python", [("PROJECT", 1), ("EXPERIENCE", 1)]), skill("SQL", [("ASSESSMENT", 0)])]}, now=NOW)
        rows, alignment = compare_requirements(analysis, states, True)
        self.assertEqual([row["state"] for row in rows], ["EVIDENCE_BACKED_ALIGNMENT", "EVIDENCE_BACKED_ALIGNMENT", "EVIDENCE_NEEDS_STRENGTHENING", "MISSING_EVIDENCE", "UNKNOWN_OR_UNMAPPED"])
        self.assertEqual((alignment["numerator"], alignment["denominator"], alignment["value"]), (1, 3, 1 / 3))
        self.assertEqual(rows[0]["evidence"]["measurement_status"], "NOT_ASSESSED")
        self.assertEqual(rows[2]["evidence"]["assessment_measurement"], 0)
        self.assertEqual(rows[2]["evidence"]["source_types"], ["ASSESSMENT"])
        self.assertEqual(rows[0]["requirement"].quote, "Python is required.")
        self.assertEqual(compare_requirements(analysis, states, True), (rows, alignment))

    def test_negative_optional_uncertain_legacy_truncated_and_no_snapshot(self):
        for quote in ("Python is not required.", "No Python is needed.", "Python is optional.", "Python preferred.", "Python experience.", "Python or Java is required.", "Python must be known if applicable."):
            rows, alignment = compare_requirements(analysis_for([(quote, "python")]), [], True)
            self.assertIsNone(alignment["value"], quote)
            self.assertFalse(rows[0]["included_in_alignment"])
        for analysis in (analysis_for([("Python required.", "python")], version="jd-literal-v1"), analysis_for([("Python required.", "python")], truncated=True)):
            self.assertIsNone(compare_requirements(analysis, [], True)[1]["value"])
        rows, alignment = compare_requirements(analysis_for([("Python required.", "python")]), [], False)
        self.assertEqual(rows[0]["state"], "NOT_ASSESSED")
        self.assertIsNone(alignment["value"])

    def test_conflicting_mentions_invalid_provenance_and_missing_recorded_evidence(self):
        analysis = analysis_for([("Python required.", "python"), ("Python not required.", "python")])
        self.assertIsNone(compare_requirements(analysis, [], True)[1]["value"])
        analysis.requirements[0].source_end = 1
        self.assertEqual(compare_requirements(analysis, [], True)[0][0]["state"], "UNKNOWN_OR_UNMAPPED")
        states = calculate_all_skill_states({"skills": [skill("Java", [])]}, now=NOW)
        self.assertEqual(compare_requirements(analysis_for([("Java required.", "java")]), states, True)[0][0]["state"], "MISSING_EVIDENCE")


@unittest.skipUnless(os.getenv("CAREERPILOT_POSTGRES_TEST") == "1", "opt-in PostgreSQL integration")
class JobMatchingPostgresTests(unittest.TestCase):
    def test_auth_ownership_dynamism_provenance_actions_and_read_only(self):
        from sqlalchemy import event
        from backend.app.career_twin.models import CareerTwin, CareerTwinSnapshot
        from backend.app.assessments.models import Assessment
        from backend.app.skills.models import Skill
        with synthetic_database() as (db, users, call, connection):
            states = [{"skills": [skill("Python", [("PROJECT", 1), ("EXPERIENCE", 1)])]}, {"skills": [skill("Python", [("RESUME", 1)])]}]
            for index in range(2):
                twin = CareerTwin(user_id=users[index].id, current_version=1)
                db.add(twin); db.flush()
                db.add(CareerTwinSnapshot(career_twin_id=twin.id, version=1, trigger_type="SYNTHETIC", state_data=states[index]))
            db.commit()
            analyses = [call(user=index, method="POST", payload={"title": "Same JD", "source_text": "Python is required."})[1] for index in range(2)]
            java = call(method="POST", payload={"title": "Different JD", "source_text": "Java is required."})[1]
            unavailable = call(user=2, method="POST", payload={"title": "No twin", "source_text": "Python is required."})[1]
            path = lambda analysis: f"/api/v1/jobs/analyses/{analysis['id']}/match"
            self.assertEqual(call(user=None, path=path(analyses[0]))[0], 401)
            self.assertEqual(call(user=1, path=path(analyses[0])), call(user=1, path=f"/api/v1/jobs/analyses/{uuid.uuid4()}/match"))
            self.assertEqual(call(user=1, path=path(analyses[0]))[0], 404)
            self.assertEqual(call(user=2, path=path(unavailable))[1]["status"], "UNAVAILABLE")
            statements = []
            def capture(conn, cursor, statement, parameters, context, executemany):
                statements.append(statement.strip().split()[0].upper())
            db.connection()
            event.listen(connection, "before_cursor_execute", capture)
            original = copy.deepcopy(states)
            try:
                with patch("backend.app.jobs.service.extract_requirements", side_effect=AssertionError("No re-extraction")), patch("backend.app.jobs.matching.datetime") as clock:
                    clock.now.return_value = NOW
                    first = call(path=path(analyses[0]))
                    second = call(user=1, path=path(analyses[1]))
                    different = call(path=path(java))
                    self.assertEqual(first[0], 200)
                    self.assertEqual(first[1]["requirements"][0]["state"], "EVIDENCE_BACKED_ALIGNMENT")
                    self.assertEqual(second[1]["requirements"][0]["state"], "EVIDENCE_NEEDS_STRENGTHENING")
                    self.assertEqual(different[1]["requirements"][0]["state"], "MISSING_EVIDENCE")
                    self.assertEqual(first[1]["requirements"][0]["requirement"], analyses[0]["requirements"][0])
                    self.assertEqual(call(path=path(analyses[0])), first)
                    self.assertTrue(second[1]["requirements"][0]["actions"])
                self.assertTrue(statements)
                self.assertEqual(set(statements), {"SELECT"})
                self.assertEqual(states, original)
                self.assertFalse(db.new or db.dirty or db.deleted)
            finally:
                event.remove(connection, "before_cursor_execute", capture)
