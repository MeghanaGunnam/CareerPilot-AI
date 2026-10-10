"""Exact-match, read-only certification recommendation boundaries."""
import asyncio
import copy
import json
import os
import unittest
import uuid
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "certification-unit-tests")

from fastapi import HTTPException
from backend.app.auth.dependencies import get_current_user
from backend.app.certification_recommendations import router, service
from backend.app.certification_recommendations.catalog import CATALOG
from backend.app.certification_recommendations.schemas import CertificationRecommendationsResponse
from backend.app.core.database import get_db
from backend.app.main import app


def analysis(missing=(), weak=(), strong=()):
    return {"technology_analysis": {
        "missing_evidence": [{"technology": name} for name in missing],
        "evidence_needs_strengthening": [{"technology": name} for name in weak],
        "strong_evidence": [{"technology": name} for name in strong],
    }}


def http_get(query_string=b""):
    """Exercise the real ASGI app without an optional HTTP client dependency."""
    messages = []
    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}
    async def send(message):
        messages.append(message)
    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1", "method": "GET", "scheme": "http",
        "path": "/api/v1/certification-recommendations", "raw_path": b"/api/v1/certification-recommendations",
        "query_string": query_string, "root_path": "", "headers": [],
        "client": ("127.0.0.1", 12345), "server": ("test", 80),
    }
    asyncio.run(app(scope, receive, send))
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, json.loads(body)


class CertificationRecommendationTests(unittest.TestCase):
    def test_career_gap_inputs_change_results_using_exact_canonical_aliases(self):
        for names, expected in (
            (["Python"], ["python-institute-pcap"]),
            (["Structured query language SQL"], ["oracle-database-sql"]),
            (["Oracle Java"], ["oracle-java-se-17-developer"]),
            (["Kubernetes"], ["linux-foundation-cka"]),
            (["NoSQL", "MySQL", "Microsoft SQL Server", "Python tools", "JavaScript"], []),
        ):
            with self.subTest(names=names):
                result = service.build_recommendations(analysis(names), [])
                self.assertEqual([r["key"] for r in result], expected)

    def test_empty_strong_and_broad_competency_inputs_do_not_recommend(self):
        for gaps in ({}, analysis(), analysis(strong=["Python"]),
                     {"competency_requirements": [{"element_name": "Programming", "gap_status": "UNKNOWN"}]}):
            self.assertEqual(service.build_recommendations(gaps, []), [])

    def test_rank_is_deterministic_deduplicated_and_missing_precedes_weak(self):
        first = analysis(["SQL", "Structured query language SQL", "Kubernetes"], ["Python"])
        second = analysis(["Kubernetes", "SQL"], ["Python"])
        result = service.build_recommendations(first, [])
        self.assertEqual(result, service.build_recommendations(second, []))
        self.assertEqual([r["key"] for r in result], ["linux-foundation-cka", "oracle-database-sql", "python-institute-pcap"])
        self.assertEqual([r["priority"] for r in result], [1, 2, 3])
        self.assertEqual(result[1]["gaps"], [{"skill": "sql", "state": "MISSING_EVIDENCE"}])

    def test_duplicate_conflicting_gap_order_is_stable(self):
        result = service.build_recommendations(analysis(["Python"], ["Python"]), [])
        self.assertEqual(result[0]["gaps"], [{"skill": "python", "state": "MISSING_EVIDENCE"}])

    def test_earned_suppression_requires_exact_name_and_provider(self):
        matching = [
            NS(name="  pCaP  ", issuing_organization=" OpenEDG   Python Institute "),
            NS(name="PCAP™ – Certified Associate Python Programmer", issuing_organization="Python Institute"),
        ]
        for earned in matching:
            self.assertEqual(service.build_recommendations(analysis(["Python"]), [earned]), [])
        for name, provider in (
            ("PCAP", "Other Provider"), ("PCAP preparation course", "Python Institute"),
            ("PCPP", "Python Institute"), ("PCAP", ""),
        ):
            self.assertEqual(len(service.build_recommendations(analysis(["Python"]), [NS(name=name, issuing_organization=provider)])), 1)
        java = NS(name="Oracle Certified Professional: Java SE 11 Developer", issuing_organization="Oracle")
        self.assertEqual(len(service.build_recommendations(analysis(["Java"]), [java])), 1)

    def test_catalogue_provenance_is_honest_and_output_does_not_inflate_evidence(self):
        self.assertTrue(6 <= len(CATALOG) <= 8)
        self.assertEqual(len(CATALOG), len({c.key for c in CATALOG}))
        gaps = analysis([skill for cert in CATALOG for skill in cert.skills])
        before = copy.deepcopy(gaps)
        result = service.build_recommendations(gaps, [])
        self.assertEqual(gaps, before)
        self.assertEqual(len(result), len(CATALOG))
        for row in result:
            provenance = row["provenance"]
            self.assertEqual(provenance["source_url"], row["official_url"])
            self.assertEqual(provenance["url_checked_on"], "2026-10-10")
            self.assertIn("not live verified", provenance["limitations"])
            self.assertEqual(provenance["verification_status"], "FETCH_BLOCKED_HTTP_403" if row["provider"] == "Oracle" else "OFFICIAL_PAGE_RETRIEVED")
            self.assertEqual(set(row), {"key", "name", "provider", "category", "relevant_skills", "priority", "reason", "gaps", "official_url", "provenance"})

    def test_service_uses_authenticated_owner_mapping_versions_and_read_only_calls(self):
        user_id, career_id = uuid.uuid4(), uuid.uuid4()
        goal = NS(target_role="Arbitrary user title", onet_soc_code="00-0000.01")
        db = Mock()
        db.scalar.return_value = NS(id=career_id, title="Arbitrary occupation", onet_soc_code=goal.onet_soc_code)
        gap_result = {"snapshot_version": 8, "model_version": "actual-acif", "gap_analysis": analysis(["Python"])}
        with patch.object(service, "get_user_primary_career_goal", return_value=goal) as get_goal, \
             patch.object(service, "get_career_gap_analysis", return_value=gap_result) as get_gaps, \
             patch.object(service, "get_user_certifications", return_value=[]) as get_earned:
            result = service.get_certification_recommendations(db, user_id)
        get_goal.assert_called_once_with(db=db, user_id=user_id)
        get_gaps.assert_called_once_with(db=db, user_id=user_id, career_id=career_id)
        get_earned.assert_called_once_with(db=db, user_id=user_id)
        self.assertEqual(db.scalar.call_args.args[0].compile().params, {"onet_soc_code_1": goal.onet_soc_code})
        self.assertEqual((result["snapshot_version"], result["model_version"]), (8, "actual-acif"))
        self.assertEqual(result["target_role"], goal.target_role)
        self.assertEqual(result["occupational_anchor"]["id"], str(career_id))
        CertificationRecommendationsResponse.model_validate(result)
        for method in ("add", "add_all", "flush", "commit", "delete"):
            getattr(db, method).assert_not_called()

    def test_missing_goal_mapping_and_career_are_404(self):
        for goal, message in ((None, "Primary career goal not found."),
                              (NS(onet_soc_code=None), "Primary career goal has no target career mapping."),
                              (NS(onet_soc_code="00-0000.01"), "Mapped target career not found.")):
            db = Mock()
            db.scalar.return_value = None
            with patch.object(service, "get_user_primary_career_goal", return_value=goal):
                with self.assertRaises(HTTPException) as error:
                    service.get_certification_recommendations(db, uuid.uuid4())
            self.assertEqual((error.exception.status_code, error.exception.detail), (404, message))

    def test_missing_twin_and_snapshot_propagate_clear_acif_404(self):
        from backend.app.acif import service as acif
        db = Mock()
        db.scalar.return_value = NS(id=uuid.uuid4())
        for twin, message in ((None, "Career Twin has not been created yet"), (NS(id=uuid.uuid4()), "does not contain a snapshot")):
            with patch.object(service, "get_user_primary_career_goal", return_value=NS(onet_soc_code="00-0000.01")), \
                 patch.object(acif, "get_career_twin", return_value=twin), \
                 patch.object(acif, "get_latest_snapshot", return_value=None):
                with self.assertRaises(HTTPException) as error:
                    service.get_certification_recommendations(db, uuid.uuid4())
            self.assertEqual(error.exception.status_code, 404)
            self.assertIn(message, error.exception.detail)

    def test_registered_http_route_requires_auth_and_ignores_requested_other_user(self):
        user_id = uuid.uuid4()
        response = {"target_role": "Example", "occupational_anchor": {"id": str(uuid.uuid4()), "title": "Example", "onet_soc_code": "00-0000.01"},
                    "snapshot_version": 1, "model_version": "test", "methodology": service.METHODOLOGY,
                    "recommendations": [], "interpretation": service.INTERPRETATION}
        db = Mock()
        saved = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = lambda: db
        try:
            with patch.object(router, "get_certification_recommendations", return_value=response) as recommend:
                self.assertEqual(http_get()[0], 401)
                recommend.assert_not_called()
                app.dependency_overrides[get_current_user] = lambda: NS(id=user_id)
                status, body = http_get(f"user_id={uuid.uuid4()}".encode())
                self.assertEqual(status, 200)
                self.assertEqual(body, response)
                recommend.assert_called_once_with(db=db, user_id=user_id)
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(saved)


if __name__ == "__main__":
    unittest.main()
