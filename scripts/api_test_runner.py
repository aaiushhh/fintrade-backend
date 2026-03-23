"""
API test runner for FItTrade LMS backend.

Runs against a live FastAPI server, auto-discovers endpoints from OpenAPI,
executes a small suite of test cases per operation, and writes a report.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import string
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _rand_suffix(n: int = 6) -> str:
    return "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(n))


def _safe_filename(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "-", s.strip())
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-") or "report"


def _truncate(text: str, limit: int = 4000) -> str:
    if text is None:
        return ""
    if len(text) <= limit:
        return text
    return text[: limit - 20] + "\n... <truncated> ..."


def _json_dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


@dataclass
class TestCaseResult:
    name: str
    method: str
    path: str
    url: str
    ok: bool
    status_code: Optional[int] = None
    expected: str = ""
    duration_ms: int = 0
    request_headers: Dict[str, str] = field(default_factory=dict)
    request_query: Dict[str, Any] = field(default_factory=dict)
    request_json: Any = None
    response_headers: Dict[str, str] = field(default_factory=dict)
    response_text: str = ""
    error: Optional[str] = None


class OpenAPI:
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec
        self.components = (spec.get("components") or {}).get("schemas") or {}

    def iter_operations(self) -> Iterable[Tuple[str, str, Dict[str, Any]]]:
        paths = self.spec.get("paths") or {}
        for path, item in paths.items():
            for method in ("get", "post", "put", "patch", "delete"):
                op = (item or {}).get(method)
                if op:
                    yield path, method.upper(), op

    def resolve_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            return {}
        ref = schema.get("$ref")
        if ref and ref.startswith("#/components/schemas/"):
            name = ref.split("/")[-1]
            return self.components.get(name) or {}
        if "allOf" in schema and isinstance(schema["allOf"], list):
            merged: Dict[str, Any] = {"type": "object", "properties": {}, "required": []}
            for part in schema["allOf"]:
                part_res = self.resolve_schema(part)
                merged["properties"].update(part_res.get("properties") or {})
                merged["required"] = list(
                    dict.fromkeys((merged.get("required") or []) + (part_res.get("required") or []))
                )
            return merged
        return schema


class ExampleFactory:
    def __init__(self):
        self.email = f"autotest_{int(time.time())}_{_rand_suffix()}@example.com"
        self.password = "securePass123"
        self.full_name = "API Autotest"
        self.phone = "+919876543210"

    def example_for_schema(self, openapi: OpenAPI, schema: Dict[str, Any]) -> Any:
        schema = openapi.resolve_schema(schema or {})

        if "example" in schema:
            return schema["example"]
        if "default" in schema:
            return schema["default"]

        t = schema.get("type")
        fmt = schema.get("format")

        if t == "string":
            if fmt == "email":
                return self.email
            if fmt in ("date-time", "datetime"):
                return _now_utc_iso()
            if "enum" in schema and isinstance(schema["enum"], list) and schema["enum"]:
                return schema["enum"][0]
            # Heuristic for password fields
            return "test"
        if t == "integer":
            return 1
        if t == "number":
            return 1.0
        if t == "boolean":
            return True
        if t == "array":
            items = schema.get("items") or {}
            return [self.example_for_schema(openapi, items)]
        if t == "object" or "properties" in schema:
            props: Dict[str, Any] = schema.get("properties") or {}
            required: List[str] = schema.get("required") or []
            obj: Dict[str, Any] = {}
            for key in required:
                obj[key] = self.example_for_schema(openapi, props.get(key) or {})
            # Add a couple optional fields if small and helpful
            for key in props.keys():
                if key in obj:
                    continue
                if len(obj) >= max(2, len(required) + 2):
                    break
                obj[key] = self.example_for_schema(openapi, props.get(key) or {})
            return obj

        # Fallback for unknown schemas
        if "$ref" in schema:
            return self.example_for_schema(openapi, openapi.resolve_schema(schema))
        return None


def _operation_security_requires_auth(op: Dict[str, Any]) -> bool:
    # If security is omitted, FastAPI may still require auth via dependencies,
    # but OpenAPI typically includes security for OAuth2PasswordBearer.
    security = op.get("security")
    if security is None:
        return False
    if isinstance(security, list) and len(security) == 0:
        return False
    return True


def _choose_success_status(op: Dict[str, Any]) -> str:
    responses = op.get("responses") or {}
    for code in ("200", "201", "204"):
        if code in responses:
            return code
    for code in responses.keys():
        if str(code).startswith("2"):
            return str(code)
    return "2xx"


def _get_request_body_schema(op: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    rb = op.get("requestBody") or {}
    content = rb.get("content") or {}
    app_json = content.get("application/json") or content.get("application/*+json")
    if not app_json:
        return None
    return app_json.get("schema")


def _collect_params(op: Dict[str, Any], where: str) -> List[Dict[str, Any]]:
    params = op.get("parameters") or []
    return [p for p in params if (p.get("in") == where)]


def _path_params(path: str) -> List[str]:
    return re.findall(r"\{([^}]+)\}", path)


class ApiTestRunner:
    def __init__(
        self,
        base_url: str,
        openapi_url: str,
        timeout_s: float,
        verify_tls: bool,
        out_dir: Path,
        admin_email: str,
        admin_password: str,
        seed_student: bool,
        concurrency: int,
    ):
        self.base_url = base_url.rstrip("/")
        self.openapi_url = openapi_url
        self.timeout_s = timeout_s
        self.verify_tls = verify_tls
        self.out_dir = out_dir
        self.admin_email = admin_email
        self.admin_password = admin_password
        self.seed_student = seed_student
        self.concurrency = max(1, concurrency)

        self.example = ExampleFactory()
        self.openapi: Optional[OpenAPI] = None

        self.tokens: Dict[str, str] = {}  # role -> access_token
        self.ids: Dict[str, Any] = {}  # discovered ids (course_id, lecture_id, etc.)

    async def fetch_openapi(self, client: httpx.AsyncClient) -> OpenAPI:
        r = await client.get(self.openapi_url)
        r.raise_for_status()
        return OpenAPI(r.json())

    async def _login(self, client: httpx.AsyncClient, email: str, password: str) -> str:
        r = await client.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
        )
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("Login response missing access_token")
        return token

    async def _register_student(self, client: httpx.AsyncClient) -> str:
        body = {
            "email": self.example.email,
            "full_name": self.example.full_name,
            "phone": self.example.phone,
            "password": self.example.password,
        }
        r = await client.post(f"{self.base_url}/auth/register", json=body)
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError("Register response missing access_token")
        return token

    async def _create_user_via_admin(
        self, client: httpx.AsyncClient, kind: str, email: str, full_name: str, password: str
    ) -> None:
        # kind: "admin" | "faculty" | "distributor"
        if "admin" not in self.tokens:
            # Cannot perform admin-only creation without an admin token
            print(f"[api_test_runner] Skipping create-{kind}: no admin token available")
            return
        if kind == "admin":
            url = f"{self.base_url}/admin/users/create-admin"
            payload = {"email": email, "full_name": full_name, "password": password}
        elif kind == "faculty":
            url = f"{self.base_url}/admin/users/create-faculty"
            payload = {"email": email, "full_name": full_name, "password": password}
        elif kind == "distributor":
            url = f"{self.base_url}/admin/users/create-distributor"
            payload = {
                "email": email,
                "full_name": full_name,
                "password": password,
                "region": "Autotest Region",
                "referral_code": f"AUTO{_rand_suffix(6).upper()}",
                "discount_percentage": 10.0,
            }
        else:
            raise ValueError(f"Unknown kind: {kind}")

        r = await client.post(url, json=payload, headers={"Authorization": f"Bearer {self.tokens['admin']}"})
        # If user already exists, we can ignore
        if r.status_code in (200, 201):
            return
        if r.status_code in (400, 409, 422):
            return
        r.raise_for_status()

    async def seed_tokens(self, client: httpx.AsyncClient) -> None:
        # Admin
        try:
            self.tokens["admin"] = await self._login(client, self.admin_email, self.admin_password)
        except Exception as e:
            # Log but continue so we can still exercise unauthenticated flows
            print(f"[api_test_runner] Failed admin login: {e!r}")

        # Student (register a fresh one unless disabled)
        if self.seed_student:
            try:
                self.tokens["student"] = await self._register_student(client)
            except Exception as e:
                print(f"[api_test_runner] Failed student registration/login: {e!r}")
        else:
            if "admin" in self.tokens:
                self.tokens["student"] = self.tokens["admin"]

        # Faculty + Distributor: create via admin then login, only if admin token is available
        if "admin" in self.tokens:
            faculty_email = f"faculty_autotest_{int(time.time())}_{_rand_suffix()}@platform.com"
            faculty_pass = "secureFaculty123"
            await self._create_user_via_admin(client, "faculty", faculty_email, "Faculty Autotest", faculty_pass)
            try:
                self.tokens["faculty"] = await self._login(client, faculty_email, faculty_pass)
            except Exception as e:
                print(f"[api_test_runner] Failed faculty creation/login: {e!r}")

            dist_email = f"dist_autotest_{int(time.time())}_{_rand_suffix()}@partner.com"
            dist_pass = "secureDist123"
            await self._create_user_via_admin(client, "distributor", dist_email, "Distributor Autotest", dist_pass)
            try:
                self.tokens["distributor"] = await self._login(client, dist_email, dist_pass)
            except Exception as e:
                print(f"[api_test_runner] Failed distributor creation/login: {e!r}")

    async def discover_ids(self, client: httpx.AsyncClient) -> None:
        if "admin" in self.tokens:
            admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            try:
                # 1. Course
                rc = await client.post(f"{self.base_url}/admin/courses", json={"title": "autocourse", "is_published": True}, headers=admin_headers)
                if rc.status_code == 201:
                    self.ids["course_id"] = rc.json().get("id")
                
                # 2. Module
                if self.ids.get("course_id"):
                    rm = await client.post(f"{self.base_url}/admin/modules", json={"course_id": self.ids["course_id"], "title": "automod", "order": 1}, headers=admin_headers)
                    if rm.status_code == 201:
                        self.ids["module_id"] = rm.json().get("id")
                
                # 3. Exam
                if self.ids.get("course_id"):
                    re_ = await client.post(f"{self.base_url}/admin/exams/create", json={"course_id": self.ids["course_id"], "title": "autoexam", "duration_minutes": 60, "passing_score": 50}, headers=admin_headers)
                    if re_.status_code == 201:
                        self.ids["exam_id"] = re_.json().get("id")

                # 4. Lecture
                if self.ids.get("course_id"):
                    rl = await client.post(f"{self.base_url}/admin/lectures", json={"course_id": self.ids["course_id"], "title": "autolect", "scheduled_at": "2029-01-01T10:00:00Z", "meeting_link": "https://meet.google.com/abc"}, headers=admin_headers)
                    if rl.status_code == 201:
                        self.ids["lecture_id"] = rl.json().get("id")

                # 5. Lesson
                if self.ids.get("module_id"):
                    rles = await client.post(f"{self.base_url}/admin/lessons", json={"module_id": self.ids["module_id"], "title": "autolesson", "content_type": "text"}, headers=admin_headers)
                    if rles.status_code == 201:
                        self.ids["lesson_id"] = rles.json().get("id")
                        
                # 6. Attempt ID
                if self.ids.get("exam_id"):
                    # Need student token to start exam
                    student_token = self.tokens.get("student")
                    if student_token:
                        # Add a dummy question via admin so the exam has one valid question
                        await client.post(f"{self.base_url}/admin/exams/questions?exam_id={self.ids['exam_id']}", json=[{"question_text": "Q1", "options": [{"option_text": "A", "is_correct": True}]}], headers=admin_headers)
                        
                        rsa = await client.post(f"{self.base_url}/exams/start?exam_id={self.ids['exam_id']}", headers={"Authorization": f"Bearer {student_token}"})
                        if rsa.status_code == 200:
                            self.ids["attempt_id"] = rsa.json().get("attempt_id")
                            
                            # Get questions to pull active valid question & option IDs
                            rq = await client.get(f"{self.base_url}/exams/questions?exam_id={self.ids['exam_id']}", headers={"Authorization": f"Bearer {student_token}"})
                            if rq.status_code == 200 and len(rq.json()) > 0:
                                self.ids["question_id"] = rq.json()[0].get("id")
                                if rq.json()[0].get("options"):
                                    self.ids["selected_option_id"] = rq.json()[0]["options"][0].get("id")
            except Exception as e:
                print(f"Pre-seed failed: {e}")

        # Seed Faculty module for upload_lesson
        if "faculty" in self.tokens and "admin" in self.tokens:
            fac_headers = {"Authorization": f"Bearer {self.tokens['faculty']}"}
            admin_headers = {"Authorization": f"Bearer {self.tokens['admin']}"}
            try:
                fac_me = await client.get(f"{self.base_url}/auth/me", headers=fac_headers)
                fac_id = fac_me.json().get("id") if fac_me.status_code == 200 else None
                payload = {"title": "faccourse", "is_published": True}
                if fac_id:
                    payload["instructor_id"] = fac_id
                rcf = await client.post(f"{self.base_url}/admin/courses", json=payload, headers=admin_headers)
                if rcf.status_code == 201:
                    fac_cid = rcf.json().get("id")
                    
                    # Instead of hitting admin/modules, let's just use the faculty_module_id later.
                    # Wait, admin/modules creates the module.
                    rmf = await client.post(f"{self.base_url}/admin/modules", json={"course_id": fac_cid, "title": "facmod", "order": 1}, headers=admin_headers)
                    if rmf.status_code == 201:
                        self.ids["faculty_module_id"] = rmf.json().get("id")
                        self.ids["faculty_course_id"] = fac_cid
            except Exception:
                pass


        # Still discover offer if possible
        if "student" in self.tokens:
            try:
                r = await client.get(
                    f"{self.base_url}/offers",
                    headers={"Authorization": f"Bearer {self.tokens['student']}"},
                )
                if r.status_code == 200 and isinstance(r.json(), list) and r.json():
                    self.ids["offer_code"] = r.json()[0].get("code")
            except Exception:
                pass


    def _pick_token_for_path(self, path: str) -> Optional[str]:
        p = path.lower()
        if p.startswith("/admin"):
            return self.tokens.get("admin")
        if p.startswith("/faculty"):
            return self.tokens.get("faculty") or self.tokens.get("admin")
        if p.startswith("/distributor"):
            return self.tokens.get("distributor") or self.tokens.get("admin")
        return self.tokens.get("student") or self.tokens.get("admin")

    def _fill_path(self, path: str) -> str:
        # Fill known ids; fallback to 1
        for name in _path_params(path):
            val = self.ids.get(name)
            if val is None:
                # Common naming variants
                if name.endswith("_id") and name in self.ids:
                    val = self.ids[name]
                else:
                    val = 1
            path = path.replace("{" + name + "}", str(val))
        return path

    def _build_query(self, openapi: OpenAPI, op: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for p in _collect_params(op, "query"):
            name = p.get("name")
            if not name:
                continue
            schema = p.get("schema") or {}
            # Prefer discovered IDs for known params
            if name in self.ids:
                out[name] = self.ids[name]
            elif name.endswith("_id") and name in self.ids:
                out[name] = self.ids[name]
            else:
                out[name] = self.example.example_for_schema(openapi, schema)
        return out

    def _build_json_body(self, openapi: OpenAPI, op: Dict[str, Any]) -> Any:
        schema = _get_request_body_schema(op)
        if not schema:
            return None
        body = self.example.example_for_schema(openapi, schema)
        # A couple targeted overrides for auth endpoints to keep them deterministic
        op_id = (op.get("operationId") or "").lower()
        if "/auth/register" in (op.get("tags") or []) or "register" in op_id:
            if isinstance(body, dict):
                import time, random
                body["email"] = f"new_student_{int(time.time())}_{random.randint(1000, 9999)}@example.com"
                body["password"] = "securePass123"
                body.setdefault("full_name", self.example.full_name)
                body.setdefault("phone", self.example.phone)
        if "login" in op_id and isinstance(body, dict):
            # Prefer admin login for stability if schema matches
            if "email" in body and "password" in body:
                body["email"] = self.admin_email
                body["password"] = self.admin_password
                
        if isinstance(body, dict):
            for key in ["attempt_id", "question_id", "selected_option_id"]:
                if key in body and key in self.ids:
                    body[key] = self.ids[key]
                
            # If the endpoint requires module_id and it's faculty upload, use faculty_module_id
            if "/faculty/lessons/upload" in str(op.get("tags") or []) or "upload" in op_id.lower() or "lesson" in op_id.lower():
                if "module_id" in body and "faculty_module_id" in self.ids:
                    body["module_id"] = self.ids["faculty_module_id"]
        if "create" in op_id and isinstance(body, dict) and "password" in body:
            body["password"] = "securePass123"
            if "email" in body:
                import time, random
                body["email"] = f"new_admin_{int(time.time())}_{random.randint(1000, 9999)}@example.com"
            if "referral_code" in body:
                import time, random
                body["referral_code"] = f"AUTO_{int(time.time())}_{random.randint(1000, 9999)}"
        if "create_course" in op_id and isinstance(body, dict):
            body["is_published"] = True
        
        # Randomize offer code
        if "create_offer" in op_id and isinstance(body, dict) and "code" in body:
            import time, random
            body["code"] = f"OFR_{int(time.time())}_{random.randint(1000, 9999)}"
        # Offer apply: use discovered code if present
        if isinstance(body, dict) and "offer_code" in body and self.ids.get("offer_code"):
            body["offer_code"] = self.ids["offer_code"]
            
        if isinstance(body, dict):
            if "course_id" in body and self.ids.get("course_id"):
                body["course_id"] = self.ids["course_id"]
            if "exam_id" in body and self.ids.get("exam_id"):
                body["exam_id"] = self.ids["exam_id"]
            if "lecture_id" in body and self.ids.get("lecture_id"):
                body["lecture_id"] = self.ids["lecture_id"]
            if "module_id" in body:
                if ("upload" in op_id.lower() or "faculty" in op_id.lower()) and self.ids.get("faculty_module_id"):
                    body["module_id"] = self.ids["faculty_module_id"]
                elif self.ids.get("module_id"):
                    body["module_id"] = self.ids["module_id"]

        return body

    async def _request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        json_body: Any,
    ) -> httpx.Response:
        return await client.request(method, url, headers=headers, params=params, json=json_body)

    async def run(self) -> Tuple[List[TestCaseResult], Dict[str, Any]]:
        limits = httpx.Limits(max_connections=self.concurrency, max_keepalive_connections=self.concurrency)
        timeout = httpx.Timeout(self.timeout_s)
        async with httpx.AsyncClient(
            timeout=timeout,
            verify=self.verify_tls,
            limits=limits,
            headers={"User-Agent": "fittrade-api-autotest/1.0"},
        ) as client:
            self.openapi = await self.fetch_openapi(client)
            await self.seed_tokens(client)
            await self.discover_ids(client)

            results: List[TestCaseResult] = []
            sem = asyncio.Semaphore(self.concurrency)

            async def run_case(
                *,
                name: str,
                method: str,
                path: str,
                op: Dict[str, Any],
                include_auth: bool,
                force_invalid_body: bool,
            ) -> None:
                async with sem:
                    openapi = self.openapi
                    assert openapi is not None

                    filled_path = self._fill_path(path)
                    url = f"{self.base_url}{filled_path}"

                    token = self._pick_token_for_path(path) if include_auth else None
                    headers: Dict[str, str] = {}
                    if token:
                        headers["Authorization"] = f"Bearer {token}"

                    params = self._build_query(openapi, op)
                    json_body = self._build_json_body(openapi, op)
                    if force_invalid_body and json_body is not None:
                        json_body = {"__invalid__": True}

                    expected_success = _choose_success_status(op)
                    expected_desc = (
                        f"expected {expected_success}"
                        if include_auth or not _operation_security_requires_auth(op)
                        else "expected 401/403"
                    )

                    start = time.perf_counter()
                    tc = TestCaseResult(
                        name=name,
                        method=method,
                        path=path,
                        url=url,
                        ok=False,
                        expected=expected_desc,
                        request_headers=headers.copy(),
                        request_query=params.copy(),
                        request_json=json_body,
                    )
                    try:
                        r = await self._request(
                            client,
                            method,
                            url,
                            headers=headers,
                            params=params,
                            json_body=json_body,
                        )
                        tc.status_code = r.status_code
                        tc.response_headers = {k: v for k, v in r.headers.items()}
                        tc.response_text = _truncate(r.text)

                        # Determine pass/fail
                        if include_auth or not _operation_security_requires_auth(op):
                            if "exams/start" in path:
                                tc.ok = r.status_code in (200, 409)
                            elif "exams/result" in path:
                                tc.ok = r.status_code in (200, 404)
                            else:
                                tc.ok = 200 <= r.status_code < 300
                        else:
                            tc.ok = r.status_code in (401, 403)

                        if force_invalid_body and json_body is not None:
                            tc.expected = "expected 4xx (validation error)"
                            tc.ok = 400 <= r.status_code < 500
                    except Exception as e:
                        tc.error = repr(e)
                        tc.ok = False
                    finally:
                        tc.duration_ms = int((time.perf_counter() - start) * 1000)
                        results.append(tc)

            tasks: List[asyncio.Task[None]] = []
            for path, method, op in self.openapi.iter_operations():
                # Skip OpenAPI/Swagger endpoints themselves if exposed
                if path in ("/openapi.json", "/docs", "/redoc", "/auth/logout"):
                    continue

                requires_auth = _operation_security_requires_auth(op)
                op_name = op.get("summary") or op.get("operationId") or f"{method} {path}"
                op_name = str(op_name)

                # Happy path (auth included when needed)
                tasks.append(
                    asyncio.create_task(
                        run_case(
                            name=f"{op_name} (happy)",
                            method=method,
                            path=path,
                            op=op,
                            include_auth=True if requires_auth else True,
                            force_invalid_body=False,
                        )
                    )
                )

                # Negative: missing auth when required
                if requires_auth:
                    tasks.append(
                        asyncio.create_task(
                            run_case(
                                name=f"{op_name} (no-auth)",
                                method=method,
                                path=path,
                                op=op,
                                include_auth=False,
                                force_invalid_body=False,
                            )
                        )
                    )

                # Negative: invalid body for JSON-body operations
                if _get_request_body_schema(op) is not None:
                    tasks.append(
                        asyncio.create_task(
                            run_case(
                                name=f"{op_name} (invalid-body)",
                                method=method,
                                path=path,
                                op=op,
                                include_auth=True if requires_auth else True,
                                force_invalid_body=True,
                            )
                        )
                    )

            await asyncio.gather(*tasks)

            summary = self._summarize(results)
            return results, summary

    def _summarize(self, results: List[TestCaseResult]) -> Dict[str, Any]:
        total = len(results)
        passed = sum(1 for r in results if r.ok)
        failed = total - passed
        by_status: Dict[str, int] = {}
        for r in results:
            code = str(r.status_code) if r.status_code is not None else "error"
            by_status[code] = by_status.get(code, 0) + 1
        return {
            "base_url": self.base_url,
            "openapi_url": self.openapi_url,
            "generated_at": _now_utc_iso(),
            "total_cases": total,
            "passed": passed,
            "failed": failed,
            "by_status": dict(sorted(by_status.items(), key=lambda kv: kv[0])),
            "discovered_ids": self.ids,
            "available_tokens": sorted(self.tokens.keys()),
        }


def render_markdown(summary: Dict[str, Any], results: List[TestCaseResult]) -> str:
    lines: List[str] = []
    lines.append("# API Test Report — FItTrade LMS")
    lines.append("")
    lines.append(f"- Generated at: `{summary['generated_at']}`")
    lines.append(f"- Base URL: `{summary['base_url']}`")
    lines.append(f"- OpenAPI: `{summary['openapi_url']}`")
    lines.append(f"- Total cases: **{summary['total_cases']}** | Passed: **{summary['passed']}** | Failed: **{summary['failed']}**")
    lines.append("")
    lines.append("## Status code distribution")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|---:|---:|")
    for code, count in summary["by_status"].items():
        lines.append(f"| {code} | {count} |")
    lines.append("")
    lines.append("## Test cases")
    lines.append("")
    lines.append("| Result | Method | Path | Case | Status | Duration (ms) | Expected |")
    lines.append("|---|---|---|---|---:|---:|---|")
    for r in sorted(results, key=lambda x: (x.path, x.method, x.name)):
        res = "PASS" if r.ok else "FAIL"
        status = r.status_code if r.status_code is not None else "error"
        case = r.name.replace("|", " ")
        lines.append(
            f"| {res} | `{r.method}` | `{r.path}` | {case} | {status} | {r.duration_ms} | {r.expected} |"
        )
    lines.append("")
    lines.append("## Details")
    lines.append("")
    for r in sorted(results, key=lambda x: (x.path, x.method, x.name)):
        lines.append(f"### {('PASS' if r.ok else 'FAIL')} — {r.method} {r.path} — {r.name}")
        lines.append("")
        lines.append(f"- URL: `{r.url}`")
        lines.append(f"- Expected: {r.expected}")
        lines.append(f"- Status: `{r.status_code}`" if r.status_code is not None else "- Status: `error`")
        lines.append(f"- Duration: `{r.duration_ms}ms`")
        if r.error:
            lines.append(f"- Error: `{_truncate(r.error, 2000)}`")
        lines.append("")
        if r.request_query:
            lines.append("Request query:")
            lines.append("")
            lines.append("```json")
            lines.append(_json_dumps(r.request_query))
            lines.append("```")
            lines.append("")
        if r.request_json is not None:
            lines.append("Request JSON:")
            lines.append("")
            lines.append("```json")
            lines.append(_json_dumps(r.request_json))
            lines.append("```")
            lines.append("")
        lines.append("Response (truncated):")
        lines.append("")
        lines.append("```")
        lines.append(_truncate(r.response_text))
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def render_html(md_text: str) -> str:
    # No external deps: minimal markdown-ish HTML.
    esc = (
        md_text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    # Super light formatting: headings + code fences
    html_lines: List[str] = []
    html_lines.append("<!doctype html>")
    html_lines.append("<html><head><meta charset='utf-8'/>")
    html_lines.append("<meta name='viewport' content='width=device-width, initial-scale=1'/>")
    html_lines.append("<title>API Test Report</title>")
    html_lines.append(
        "<style>body{font-family:ui-sans-serif,system-ui,Segoe UI,Roboto,Arial;padding:24px;max-width:1100px;margin:0 auto;}"
        "pre{background:#0b1020;color:#e6edf3;padding:12px;border-radius:8px;overflow:auto;}"
        "code{font-family:ui-monospace,SFMono-Regular,Consolas,Menlo,monospace;}"
        "h1,h2,h3{margin-top:28px} table{border-collapse:collapse;width:100%;} td,th{border:1px solid #ddd;padding:6px;}"
        "th{background:#f6f8fa;text-align:left}</style>"
    )
    html_lines.append("</head><body>")
    in_pre = False
    for line in esc.splitlines():
        if line.strip() == "```":
            if not in_pre:
                html_lines.append("<pre><code>")
                in_pre = True
            else:
                html_lines.append("</code></pre>")
                in_pre = False
            continue
        if in_pre:
            html_lines.append(line)
            continue
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("- "):
            # naive list rendering
            html_lines.append(f"<p>{line}</p>")
        else:
            html_lines.append(f"<p>{line}</p>" if line.strip() else "<br/>")
    if in_pre:
        html_lines.append("</code></pre>")
    html_lines.append("</body></html>")
    return "\n".join(html_lines)


def build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run API tests against all FastAPI endpoints via OpenAPI.")
    p.add_argument("--base-url", default=os.getenv("LMS_BASE_URL", "http://localhost:8000"))
    p.add_argument("--openapi-url", default=os.getenv("LMS_OPENAPI_URL", "http://localhost:8000/openapi.json"))
    p.add_argument("--timeout", type=float, default=float(os.getenv("LMS_HTTP_TIMEOUT", "25")))
    p.add_argument("--verify-tls", action="store_true", default=False)
    p.add_argument("--out-dir", default=os.getenv("LMS_TEST_OUT_DIR", "test-reports"))
    p.add_argument("--admin-email", default=os.getenv("LMS_ADMIN_EMAIL", "admin@platform.com"))
    p.add_argument("--admin-password", default=os.getenv("LMS_ADMIN_PASSWORD", "admin123!"))
    p.add_argument("--no-seed-student", action="store_true", help="Do not register a new student; reuse admin token.")
    p.add_argument("--concurrency", type=int, default=int(os.getenv("LMS_TEST_CONCURRENCY", "8")))
    return p


async def _amain(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    runner = ApiTestRunner(
        base_url=args.base_url,
        openapi_url=args.openapi_url,
        timeout_s=args.timeout,
        verify_tls=args.verify_tls,
        out_dir=out_dir,
        admin_email=args.admin_email,
        admin_password=args.admin_password,
        seed_student=(not args.no_seed_student),
        concurrency=args.concurrency,
    )

    results, summary = await runner.run()
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_name = _safe_filename(f"api-test-report-{stamp}")
    md_path = out_dir / f"{base_name}.md"
    html_path = out_dir / f"{base_name}.html"
    json_path = out_dir / f"{base_name}.json"

    md = render_markdown(summary, results)
    md_path.write_text(md, encoding="utf-8")
    html_path.write_text(render_html(md), encoding="utf-8")
    json_path.write_text(_json_dumps({"summary": summary, "results": [r.__dict__ for r in results]}), encoding="utf-8")

    print(f"Wrote:\n- {md_path}\n- {html_path}\n- {json_path}")
    print(f"Passed {summary['passed']}/{summary['total_cases']} cases")
    return 0 if summary["failed"] == 0 else 2


def main() -> int:
    parser = build_argparser()
    args = parser.parse_args()
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())

