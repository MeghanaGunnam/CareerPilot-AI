"""Opt-in synthetic PostgreSQL schema; all fixtures and DDL roll back.

Run alone with CAREERPILOT_POSTGRES_TEST=1 using configured DATABASE_URL.
"""
import copy
import os
import unittest
import uuid


@unittest.skipUnless(os.getenv("CAREERPILOT_POSTGRES_TEST") == "1", "opt-in PostgreSQL integration")
class CertificationPostgresTests(unittest.TestCase):
    def test_dynamic_goals_user_scoping_and_no_persisted_evidence_or_roadmap_changes(self):
        from sqlalchemy import event, func, select, text
        from sqlalchemy.orm import Session
        from backend.app.core.database import Base, engine
        from backend.app.main import app  # Register all application model relationships.
        from backend.app.auth.models import User
        from backend.app.students.models import CareerGoal, Certification
        from backend.app.careers.models import Career, CareerSoftwareRequirement
        from backend.app.career_twin.models import CareerTwin, CareerTwinSnapshot
        from backend.app.skills.models import SkillEvidence
        from backend.app.roadmap.models import RoadmapItem
        from backend.app.certification_recommendations.service import get_certification_recommendations

        self.assertEqual(engine.dialect.name, "postgresql")
        schema = "certification_test_" + uuid.uuid4().hex
        with engine.connect() as connection:
            outer = connection.begin()
            try:
                connection.execute(text(f'CREATE SCHEMA "{schema}"'))
                connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
                Base.metadata.create_all(connection)
                with Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False) as db:
                    users = [User(email=f"synthetic-cert-{i}@example.invalid", password_hash="not-a-password") for i in range(2)]
                    careers = [Career(onet_soc_code=f"00-0000.0{i}", title=f"Unrelated occupation {i}") for i in range(2)]
                    db.add_all(users + careers)
                    db.flush()
                    goals, snapshots = [], []
                    for index, user in enumerate(users):
                        goal = CareerGoal(user_id=user.id, target_role="User chosen label", onet_soc_code=careers[0].onet_soc_code, is_primary=True)
                        twin = CareerTwin(user_id=user.id, current_version=3)
                        db.add_all([goal, twin])
                        db.flush()
                        snapshot = CareerTwinSnapshot(career_twin_id=twin.id, version=3, trigger_type="SYNTHETIC_TEST", state_data={"skills": []})
                        db.add(snapshot)
                        goals.append(goal)
                        snapshots.append(snapshot)
                    for career, skill in zip(careers, ["Python", "Structured query language SQL"]):
                        db.add(CareerSoftwareRequirement(career_id=career.id, element_id="synthetic", element_name="Synthetic software", workplace_example=skill, in_demand=True))
                    db.add(Certification(user_id=users[0].id, name="PCAP", issuing_organization="OpenEDG Python Institute"))
                    db.commit()
                    original = [copy.deepcopy(s.state_data) for s in snapshots]
                    db.connection()  # Establish the test savepoint before observing service SQL.
                    statements = []
                    def capture(conn, cursor, statement, parameters, context, executemany):
                        statements.append(statement.lstrip().split()[0].upper())
                    event.listen(connection, "before_cursor_execute", capture)
                    try:
                        first = get_certification_recommendations(db, users[0].id)
                        second = get_certification_recommendations(db, users[1].id)
                        self.assertEqual(first["recommendations"], [])
                        self.assertEqual([r["key"] for r in second["recommendations"]], ["python-institute-pcap"])
                        self.assertEqual(second["snapshot_version"], 3)
                        self.assertTrue(statements)
                        self.assertTrue(all(s == "SELECT" for s in statements), statements)
                    finally:
                        event.remove(connection, "before_cursor_execute", capture)
                    goals[1].onet_soc_code = careers[1].onet_soc_code
                    db.commit()
                    changed = get_certification_recommendations(db, users[1].id)
                    self.assertEqual([r["key"] for r in changed["recommendations"]], ["oracle-database-sql"])
                    self.assertEqual(changed["occupational_anchor"]["id"], str(careers[1].id))
                    for model in (SkillEvidence, RoadmapItem):
                        self.assertEqual(db.scalar(select(func.count()).select_from(model)), 0)
                    self.assertEqual(db.scalar(select(func.count()).select_from(CareerTwinSnapshot)), 2)
                    for snapshot, before in zip(snapshots, original):
                        db.refresh(snapshot)
                        self.assertEqual(snapshot.state_data, before)
                    self.assertFalse(db.new or db.dirty or db.deleted)
            finally:
                outer.rollback()
            self.assertIsNone(connection.scalar(text("SELECT to_regnamespace(:schema)"), {"schema": schema}))


if __name__ == "__main__":
    unittest.main()
