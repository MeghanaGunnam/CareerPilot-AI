"""Literal extraction and authenticated API boundaries, without an HTTP dependency."""
import asyncio
import json
import unittest
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace as NS
from unittest.mock import Mock, patch

from fastapi import HTTPException
from pydantic import ValidationError

from backend.app.auth.dependencies import get_current_user
from backend.app.core.database import get_db
from backend.app.jobs import router, service
from backend.app.jobs.extractor import EXTRACTOR_VERSION, extract_requirements
from backend.app.jobs.schemas import JDAnalysisCreate, MAX_REQUIREMENTS
from backend.app.main import app


def request(method="GET", path="/api/v1/jobs/analyses", payload=None, query=b"", headers=()):
    messages = []
    body = json.dumps(payload).encode() if payload is not None else b""
    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}
    async def send(message):
        messages.append(message)
    scope = {
        "type": "http", "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1", "method": method, "scheme": "http", "path": path,
        "raw_path": path.encode(), "query_string": query, "root_path": "",
        "headers": [(b"content-type", b"application/json"), *headers],
        "client": ("127.0.0.1", 12345), "server": ("test", 80),
    }
    asyncio.run(app(scope, receive, send))
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    response_body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, json.loads(response_body) if response_body else None


class JobExtractionTests(unittest.TestCase):
    def test_exact_shared_aliases_longest_first_and_no_substring_fabrication(self):
        source = "Oracle Java, React.js, postgres, RESTful APIs, Node js, SQL, JavaScript"
        rows, truncated = extract_requirements(source)
        self.assertEqual([r.normalized_name for r in rows], ["java", "react", "postgresql", "rest api", "node.js", "sql", "javascript"])
        self.assertTrue(all(row.quote == source for row in rows))
        self.assertFalse(truncated)
        self.assertEqual(extract_requirements("NoSQL MySQL JavaScript PostgreSQL Pythonic TypeScripted gitlab" )[0][0].normalized_name, "nosql")
        names = [r.normalized_name for r in extract_requirements("NoSQL MySQL JavaScript PostgreSQL Pythonic TypeScripted gitlab")[0]]
        self.assertNotIn("sql", names)
        self.assertNotIn("java", names)
        self.assertNotIn("python", names)
        self.assertNotIn("git", names)
        self.assertEqual(extract_requirements("UnlistedTool 9000")[0], [])
        self.assertEqual(extract_requirements("ſql GİT Kubernetes éPythoné")[0], [])

    def test_preferred_marker_does_not_spread_to_a_different_sentence(self):
        rows, _ = extract_requirements("Python is required. Docker is preferred. Node.js is used.")
        self.assertEqual([(r.normalized_name, r.group) for r in rows if r.normalized_name],
                         [("python", "technology"), ("docker", "preferred"), ("node.js", "technology")])

    def test_normalized_mentions_retain_negation_and_internal_whitespace(self):
        for clause in (
            "Python experience is not required.",
            "No Python or Java knowledge is required.",
            "Python  experience\tis not required.",
            "Docker is optional, not mandatory.",
            "We do not use React.js.",
            "Python is not preferred.",
        ):
            source = "  🚀 Role\r\n  " + clause + "\r\n"
            with self.subTest(clause=clause):
                rows, truncated = extract_requirements(source)
                normalized = [row for row in rows if row.normalized_name]
                self.assertTrue(normalized)
                self.assertFalse(truncated)
                for row in normalized:
                    self.assertEqual(row.quote, clause)
                    self.assertEqual(source[row.source_start:row.source_end], clause)
                    self.assertEqual(row.interpretation_type, "NORMALIZED_INTERPRETATION")
                self.assertEqual(rows, extract_requirements(source)[0])

    def test_empty_unsupported_text_and_repeat_mentions_do_not_fabricate(self):
        for source in ("", " \r\n", "Friendly team with flexible hours.", "QuantumUnlistedTool"):
            self.assertEqual(extract_requirements(source), ([], False))
        rows, _ = extract_requirements("Python, python and PYTHON are not required.")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].quote, "Python, python and PYTHON are not required.")
        self.assertEqual(rows[0].normalized_name, "python")

    def test_groups_original_unicode_spans_and_honest_interpretations(self):
        source = "  🚀 Engineer\r\n3+ years of experience\r\nBachelor’s degree\nResponsibilities:\nBuild REST APIs\nPreferred qualifications:\nDocker\nRequirements:\nPython is not required.\n"
        rows, _ = extract_requirements(source)
        self.assertEqual({r.group for r in rows}, {"technology", "experience", "education", "responsibility", "preferred"})
        for row in rows:
            self.assertEqual(source[row.source_start:row.source_end], row.quote)
            self.assertTrue(row.quote)
            self.assertEqual(row.evidence_type, "FACT_FROM_JD")
            self.assertFalse(hasattr(row, "mandatory"))
            if row.normalized_name:
                self.assertEqual(row.interpretation_type, "NORMALIZED_INTERPRETATION")
        python = next(r for r in rows if r.normalized_name == "python")
        self.assertEqual(python.group, "technology")
        self.assertEqual(next(r for r in rows if r.normalized_name == "docker").group, "preferred")
        self.assertEqual(rows, extract_requirements(source)[0])

    def test_preferred_scope_ends_at_unknown_heading_and_length_cap_is_visible(self):
        rows, _ = extract_requirements("Preferred:\nPython\nCompensation:\nSQL")
        self.assertEqual(next(r.group for r in rows if r.normalized_name == "sql"), "technology")
        rows, truncated = extract_requirements("Python\n" * 120)
        self.assertEqual(len(rows), MAX_REQUIREMENTS)
        self.assertTrue(truncated)
        self.assertFalse(extract_requirements("Python\n" * 100)[1])

    def test_input_rejects_blank_oversized_controls_and_non_http_urls(self):
        for invalid in (
            {"title": " "}, {"title": "a" * 201}, {"title": "a\nb"},
            {"company": " "}, {"company": "x" * 201},
            {"source_text": " \r\n "}, {"source_text": "x" * 30001}, {"source_text": "a\x00b"},
            {"source_url": "javascript:alert(1)"}, {"source_url": "file:///tmp/jd"},
            {"source_url": "ftp://example.com"}, {"source_url": "not-a-url"},
            {"user_id": str(uuid.uuid4())},
        ):
            with self.subTest(invalid=invalid), self.assertRaises(ValidationError):
                JDAnalysisCreate.model_validate({"title": "Role", "source_text": "Python", **invalid})
        source = "  Python\r\n "
        value = JDAnalysisCreate(title=" Role ", source_text=source, source_url="https://example.invalid/job")
        self.assertEqual(value.source_text, source)
        self.assertEqual(value.title, "Role")


class JobsAPITests(unittest.TestCase):
    def setUp(self):
        self.saved = app.dependency_overrides.copy()
        self.db = Mock()
        self.user_id = uuid.uuid4()
        app.dependency_overrides[get_db] = lambda: self.db

    def tearDown(self):
        app.dependency_overrides.clear()
        app.dependency_overrides.update(self.saved)

    def authenticate(self):
        app.dependency_overrides[get_current_user] = lambda: NS(id=self.user_id)

    def test_all_routes_require_authentication(self):
        for method, path, payload in (("GET", "/api/v1/jobs/analyses", None),
                                      ("POST", "/api/v1/jobs/analyses", {"title": "Role", "source_text": "Python"}),
                                      ("GET", f"/api/v1/jobs/analyses/{uuid.uuid4()}", None)):
            self.assertEqual(request(method, path, payload)[0], 401)
        self.db.add.assert_not_called()

    def test_create_and_list_typed_contract_and_authenticated_owner(self):
        self.authenticate()
        response = {"id": str(uuid.uuid4()), "title": "Role", "company": None, "source_url": None,
                    "source_text": "Unknown", "requirements": [], "created_at": datetime.now(timezone.utc).isoformat(),
                    "extractor_version": EXTRACTOR_VERSION, "requirement_count": 0, "truncated": False}
        with patch.object(router, "create_analysis", return_value=response) as create:
            status, body = request("POST", payload={"title": "Role", "source_text": "Unknown"})
            self.assertEqual(status, 201)
            self.assertEqual(body["requirements"], [])
            self.assertEqual(body["extractor_version"], EXTRACTOR_VERSION)
            self.assertEqual(create.call_args.kwargs["user_id"], self.user_id)
        with patch.object(router, "list_analyses", return_value={"items": [], "total": 0, "limit": 20, "offset": 0}) as listing:
            self.assertEqual(request(query=f"user_id={uuid.uuid4()}".encode())[0], 200)
            self.assertEqual(listing.call_args.kwargs["user_id"], self.user_id)

    def test_invalid_api_inputs_and_safe_missing_response(self):
        self.authenticate()
        for payload in ({"title": "", "source_text": "Python"}, {"title": "Role", "source_text": " "},
                        {"title": "Role", "source_text": "Python", "source_url": "ftp://example.com"},
                        {"title": "Role", "source_text": "Python", "user_id": str(uuid.uuid4())},
                        {"title": "Role", "source_text": "Python", "location": "Unsupported field"}):
            self.assertEqual(request("POST", payload=payload)[0], 422)
        for query in (b"limit=0", b"limit=101", b"offset=-1"):
            self.assertEqual(request(query=query)[0], 422)
        self.assertEqual(request(path="/api/v1/jobs/analyses/not-a-uuid")[0], 422)
        self.db.scalar.return_value = None
        status, body = request(path=f"/api/v1/jobs/analyses/{uuid.uuid4()}")
        self.assertEqual((status, body), (404, {"detail": "Job description analysis not found."}))
        self.assertIn(self.user_id, self.db.scalar.call_args.args[0].compile().params.values())
        self.db.add.assert_not_called()

    def test_openapi_matches_frontend_shapes_and_no_mutation_routes(self):
        document = app.openapi()
        paths = document["paths"]
        root = "/api/v1/jobs/analyses"
        self.assertEqual(set(paths[root]), {"get", "post"})
        self.assertEqual(set(paths[root + "/{analysis_id}"]), {"get"})
        schemas = document["components"]["schemas"]
        self.assertEqual(set(schemas["JDAnalysisCreate"]["properties"]),
                         {"title", "company", "source_url", "source_text"})
        self.assertFalse(schemas["JDAnalysisCreate"]["additionalProperties"])
        summary = {"id", "title", "company", "source_url", "created_at", "extractor_version", "requirement_count", "truncated"}
        self.assertEqual(set(schemas["JDAnalysisSummary"]["properties"]), summary)
        self.assertEqual(set(schemas["JDAnalysisResponse"]["properties"]), summary | {"source_text", "requirements"})
        self.assertEqual(set(schemas["JDAnalysisList"]["properties"]), {"items", "total", "limit", "offset"})
        self.assertEqual(set(schemas["RequirementResponse"]["properties"]),
                         {"id", "position", "group", "quote", "source_start", "source_end", "evidence_type", "normalized_name", "interpretation_type"})
        for path in (root, root + "/{analysis_id}"):
            for operation in paths[path].values():
                self.assertEqual(operation["security"], [{"HTTPBearer": []}])

    def test_failed_commit_rolls_back_and_child_parent_saved_atomically(self):
        self.db.commit.side_effect = RuntimeError("database unavailable")
        with self.assertRaises(RuntimeError):
            service.create_analysis(self.db, self.user_id, JDAnalysisCreate(title="Role", source_text="Python"))
        self.db.rollback.assert_called_once()
        analysis = self.db.add.call_args.args[0]
        self.assertEqual(analysis.requirement_count, 1)
        self.assertEqual(analysis.requirements[0].analysis, analysis)


if __name__ == "__main__":
    unittest.main()
