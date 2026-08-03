from __future__ import annotations

import json

import httpx
from fastapi.testclient import TestClient

import integration_services.prana as prana_service
from integration_services.insightflow_bridge import create_app as create_insightflow
from integration_services.karma import DEFAULT_GENESIS_HASH, create_app as create_karma
from integration_services.prana import create_app as create_prana
from integration_services.raj import create_app as create_raj
from integration_services.common import runtime_secret


def test_owner_runtime_accepts_legacy_product_secret_alias(monkeypatch) -> None:
    monkeypatch.delenv("MITRA_PRODUCT_SETU_API_KEY", raising=False)
    monkeypatch.setenv("SETU_API_KEY", "setu-owner-secret")

    assert runtime_secret("MITRA_PRODUCT_SETU_API_KEY") == "setu-owner-secret"


def test_karma_persists_chain_and_detects_replay(tmp_path) -> None:
    client = TestClient(
        create_karma(
            database_path=tmp_path / "karma.db",
            genesis_hash=DEFAULT_GENESIS_HASH,
        )
    )
    health = client.get("/health").json()
    assert health["storage_backend"] == "sqlite"
    assert health["durable"] is False
    event = {
        "payload": {"value": 1},
        "previous_hash": DEFAULT_GENESIS_HASH,
        "event_id": "event-1",
    }
    appended = client.post("/integrity/append", json=event).json()
    assert appended["status"] == "appended"
    assert len(appended["current_hash"]) == 64

    replay = client.post("/integrity/append", json=event).json()
    assert replay["status"] == "replay_detected"
    assert replay["current_hash"] == appended["current_hash"]

    violation = client.post(
        "/integrity/append-bucket-artifact",
        json={
            "artifact_id": "artifact-bad",
            "trace_id": "trace-bad",
            "parent_hash": DEFAULT_GENESIS_HASH,
        },
    ).json()
    assert violation["status"] == "append_violation"

    artifact = {
        "artifact_id": "artifact-1",
        "trace_id": "trace-1",
        "parent_hash": appended["current_hash"],
        "payload": {"truth": True},
    }
    stored = client.post(
        "/integrity/append-bucket-artifact",
        json=artifact,
    ).json()
    assert stored["status"] == "appended"
    assert stored["trace_id"] == "trace-1"
    entry = client.get("/integrity/entries/artifact-1").json()
    assert entry["payload"] == artifact


def test_prana_forwards_identical_bytes_and_preserves_trace() -> None:
    observed: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request.content)
        payload = json.loads(request.content)
        if request.url.path == "/karma":
            import hashlib

            return httpx.Response(
                200,
                json={
                    "status": "accepted",
                    "trace_id": payload["trace_id"],
                    "received_sha256": hashlib.sha256(request.content).hexdigest(),
                },
            )
        return httpx.Response(
            200,
            json={"status": "accepted", "trace_id": payload["trace_id"]},
        )

    app = create_prana(
        strict_target_url="https://insight.test/karma",
        core_target_url="https://insight.test/core",
        target_api_key="bridge-key",
        transport=httpx.MockTransport(handler),
    )
    client = TestClient(app)
    raw = b'{"artifact_id":"a-1","trace_id":"trace-1"}'
    strict = client.post(
        "/forward/karma-strict",
        content=raw,
        headers={"Content-Type": "application/json"},
    )
    assert strict.status_code == 200
    assert strict.headers["x-prana-strict-bytes-equal"] == "true"
    assert observed[0] == raw

    core_body = b'{"trace_id":"trace-1","source_system":"Mitra"}'
    core = client.post(
        "/forward/core",
        content=core_body,
        headers={"Content-Type": "application/json"},
    )
    assert core.status_code == 200
    assert core.json()["trace_id"] == "trace-1"
    assert observed[1] == core_body


def test_prana_retries_transient_forward_gateway_failure(monkeypatch) -> None:
    monkeypatch.setenv("PRANA_FORWARD_ATTEMPTS", "2")
    attempts = 0

    async def no_sleep(_delay: float) -> None:
        return None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(502, text="cold upstream")
        payload = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "status": "accepted",
                "trace_id": payload["trace_id"],
            },
        )

    monkeypatch.setattr(prana_service.asyncio, "sleep", no_sleep)
    app = create_prana(
        strict_target_url="https://insight.test/karma",
        core_target_url="https://insight.test/core",
        transport=httpx.MockTransport(handler),
    )
    response = TestClient(app).post(
        "/forward/core",
        content=b'{"trace_id":"trace-retry","source_system":"Mitra"}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json()["trace_id"] == "trace-retry"
    assert attempts == 2


def test_raj_dispatches_selected_manifest_without_product_branch(monkeypatch) -> None:
    monkeypatch.delenv("RAJ_TANTRA_TRANSPORT", raising=False)
    monkeypatch.setenv(
        "RAJ_TANTRA_EXECUTION_URL",
        "https://obsolete-external-tantra.test",
    )
    monkeypatch.setenv("RAJ_ENDPOINT_OVERRIDES_JSON", "{}")
    observed: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["url"] = str(request.url)
        observed["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"status": "ok", "predictions": [{"symbol": "TCS.NS"}]},
        )

    app = create_raj(transport=httpx.MockTransport(handler))
    client = TestClient(app)
    capability_contract = {
        "product": {"base_url": "https://product.test"},
        "intent": {
            "intent_id": "product.predict",
            "dispatch": {
                "mode": "http",
                "endpoint": "/tools/predict",
                "timeout_seconds": 5,
                "options": {"request_body": "payload"},
            },
            "response_schema": {
                "type": "object",
                "required": ["status", "predictions"],
            },
        },
        "input": {
            "payload": {
                "symbols": ["TCS.NS"],
                "horizon": "short",
                "raj_workflow": {"action_type": "task"},
            }
        },
    }
    response = client.post(
        "/api/workflow/execute",
        json={
            "trace_id": "trace-raj-1",
            "decision": "workflow",
            "data": {
                "workflow_type": "workflow",
                "payload": {
                    "action_type": "task",
                    "mitra_context": {
                        "capability_contract": capability_contract
                    },
                },
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["execution_result"]["success"] is True
    assert body["raj"]["orchestration_mode"] == "in-chain-tantra-runtime"
    assert body["tantra"] == {
        "authority": "execution-boundary-only",
        "boundary_contract": "raj-to-tantra-execution.v1",
        "completed_at": body["tantra"]["completed_at"],
        "request_sha256": body["tantra"]["request_sha256"],
        "response_sha256": body["tantra"]["response_sha256"],
        "started_at": body["tantra"]["started_at"],
        "trace_id": "trace-raj-1",
        "transport": "in-process",
    }
    health = client.get("/healthz").json()
    assert health["execution_mode"] == "in-chain-tantra-runtime"
    assert health["tantra_configured"] is True
    assert health["tantra_transport"] == "in-process"
    assert observed == {
        "url": "https://product.test/tools/predict",
        "payload": {"horizon": "short", "symbols": ["TCS.NS"]},
    }


def test_raj_returns_typed_product_error_for_conditional_diagnosis(
    monkeypatch,
) -> None:
    monkeypatch.delenv("RAJ_TANTRA_EXECUTION_URL", raising=False)
    monkeypatch.setenv("RAJ_ENDPOINT_OVERRIDES_JSON", "{}")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            422,
            json={"detail": "symbols is required"},
        )

    app = create_raj(transport=httpx.MockTransport(handler))
    client = TestClient(app)
    response = client.post(
        "/api/workflow/execute",
        json={
            "trace_id": "trace-raj-product-error",
            "decision": "workflow",
            "data": {
                "workflow_type": "workflow",
                "payload": {
                    "action_type": "task",
                    "mitra_context": {
                        "capability_contract": {
                            "product": {"base_url": "https://product.test"},
                            "intent": {
                                "intent_id": "product.predict",
                                "dispatch": {
                                    "mode": "http",
                                    "endpoint": "/tools/predict",
                                    "options": {"request_body": "payload"},
                                },
                            },
                            "input": {
                                "payload": {
                                    "raj_workflow": {
                                        "action_type": "task"
                                    }
                                }
                            },
                        }
                    },
                },
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "product_error"
    assert body["trace_id"] == "trace-raj-product-error"
    assert body["execution_result"]["success"] is False
    assert body["execution_result"]["http_status"] == 422
    assert body["execution_result"]["error"]["type"] == (
        "product_rejected_workflow"
    )


def test_raj_honors_published_envelope_and_secret_header(monkeypatch) -> None:
    monkeypatch.delenv("RAJ_TANTRA_EXECUTION_URL", raising=False)
    monkeypatch.setenv("SETU_TEST_API_KEY", "setu-secret")
    observed = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["headers"] = dict(request.headers)
        observed["payload"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "success": True,
                "trace_id": "trace-envelope",
                "data": {},
            },
        )

    app = create_raj(transport=httpx.MockTransport(handler))
    client = TestClient(app)
    response = client.post(
        "/api/workflow/execute",
        json={
            "trace_id": "trace-envelope",
            "decision": "workflow",
            "data": {
                "workflow_type": "workflow",
                "payload": {
                    "action_type": "task",
                    "mitra_context": {
                        "execution_id": "eco-envelope",
                        "capability_contract": {
                            "product": {
                                "product_id": "setu-ai-crm",
                                "base_url": "https://product.test",
                            },
                            "capability": {"capability_id": "crm-operations"},
                            "intent": {
                                "intent_id": "setu.operations.summary",
                                "dispatch": {
                                    "mode": "http",
                                    "endpoint": "/api/mitra/execute",
                                    "options": {
                                        "request_body": "envelope",
                                        "secret_headers": {
                                            "X-SETU-API-Key": "SETU_TEST_API_KEY"
                                        },
                                    },
                                },
                            },
                            "input": {
                                "payload": {
                                    "query": "show operations",
                                    "raj_workflow": {"action_type": "task"},
                                }
                            },
                        },
                    },
                },
            },
        },
    )

    assert response.status_code == 200
    assert observed["headers"]["x-setu-api-key"] == "setu-secret"
    assert observed["payload"] == {
        "dispatch_id": "eco-envelope",
        "correlation_id": "trace-envelope",
        "product_id": "setu-ai-crm",
        "capability_id": "crm-operations",
        "intent_id": "setu.operations.summary",
        "payload": {"query": "show operations"},
    }


def test_raj_embeds_tantra_boundary_and_calls_capability_runtime(
    monkeypatch,
) -> None:
    monkeypatch.delenv("RAJ_TANTRA_TRANSPORT", raising=False)
    monkeypatch.setenv(
        "RAJ_CAPABILITY_RUNTIME_URL",
        "https://runtime.test",
    )
    observed: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["calls"] = observed.get("calls", 0) + 1
        observed["url"] = str(request.url)
        observed["payload"] = json.loads(request.content)
        if observed["calls"] == 1:
            return httpx.Response(503, json={"detail": "runtime starting"})
        return httpx.Response(
            200,
            json={
                "execution_id": "ucr-exec-1",
                "capability_id": "mitra-remote-product-v1",
                "state": "completed",
                "duration_seconds": 0.01,
                "outputs": {
                    "status": "success",
                    "trace_id": "trace-in-chain",
                    "runtime": {
                        "service": "kanishk-universal-capability-runtime"
                    },
                    "execution_result": {"success": True},
                },
                "error": None,
                "retry_count": 0,
                "runtime": {
                    "service": "kanishk-universal-capability-runtime"
                },
            },
        )

    app = create_raj(transport=httpx.MockTransport(handler))
    response = TestClient(app).post(
        "/api/workflow/execute",
        json={
            "trace_id": "trace-in-chain",
            "decision": "workflow",
            "data": {
                "workflow_type": "workflow",
                "payload": {
                    "action_type": "task",
                    "mitra_context": {
                        "execution_id": "eco-in-chain",
                        "capability_contract": {
                            "product": {
                                "product_id": "trade-bot",
                                "base_url": "https://product.test",
                            },
                            "capability": {
                                "capability_id": "market-prediction"
                            },
                            "intent": {
                                "intent_id": "trade.predict",
                                "dispatch": {
                                    "mode": "http",
                                    "endpoint": "/tools/predict",
                                },
                            },
                            "input": {"payload": {"symbols": ["AAPL"]}},
                        },
                    },
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert observed["url"] == (
        "https://runtime.test/api/capabilities/"
        "mitra-remote-product-v1/execute"
    )
    assert observed["payload"]["inputs"]["trace_id"] == "trace-in-chain"
    assert observed["payload"]["metadata"] == {
        "source": "raj",
        "trace_id": "trace-in-chain",
    }
    assert body["raj"]["orchestration_mode"] == "in-chain-tantra-runtime"
    assert body["tantra"]["transport"] == "in-process"
    assert body["runtime"]["service"] == (
        "kanishk-universal-capability-runtime"
    )
    assert body["canonical_runtime_execution"]["execution_id"] == (
        "ucr-exec-1"
    )
    assert observed["calls"] == 2
    assert [
        attempt["http_status"]
        for attempt in body["canonical_runtime_execution"][
            "transport_attempts"
        ]
    ] == [503, 200]


def test_insightflow_bridge_registers_dataset_and_provenance(monkeypatch) -> None:
    monkeypatch.setenv("INSIGHTFLOW_BRIDGE_API_KEY", "bridge-key")
    requests: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append((request.method, request.url.path))
        if request.method == "GET" and "/canonical/" in request.url.path:
            return httpx.Response(404, json={"detail": "not found"})
        if request.method == "POST" and request.url.path.endswith("/datasets/"):
            return httpx.Response(201, json={"id": "dataset-1"})
        if request.method == "POST" and request.url.path.endswith("/provenance"):
            return httpx.Response(201, json={"id": "provenance-1"})
        if request.method == "GET" and request.url.path == "/health":
            return httpx.Response(200, json={"status": "healthy"})
        return httpx.Response(500, json={"detail": "unexpected request"})

    app = create_insightflow(
        registry_base_url="https://registry.test",
        registry_api_key="registry-key",
        transport=httpx.MockTransport(handler),
    )
    client = TestClient(app)
    response = client.post(
        "/ingest/execution",
        json={
            "event_type": "mitra.tantra.execution.completed.v1",
            "trace_id": "trace-insight-1",
            "execution_id": "execution-1",
            "payload": {"karma_hash": "abc"},
        },
        headers={"X-API-Key": "bridge-key"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "trace_id": "trace-insight-1",
        "received_sha256": response.json()["received_sha256"],
        "dataset_id": "dataset-1",
        "provenance_id": "provenance-1",
        "stage": "execution",
    }
    assert requests == [
        ("GET", "/api/v1/datasets/canonical/BHIV-DS-MITRA-RUNTIME-001"),
        ("POST", "/api/v1/datasets/"),
        ("POST", "/api/v1/datasets/dataset-1/provenance"),
    ]


def test_insightflow_karma_ingest_only_verifies_strict_bytes(
    monkeypatch,
) -> None:
    monkeypatch.setenv("INSIGHTFLOW_BRIDGE_API_KEY", "bridge-key")
    registry_calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        registry_calls.append(request)
        return httpx.Response(500)

    app = create_insightflow(
        registry_base_url="https://registry.test",
        registry_api_key="registry-key",
        transport=httpx.MockTransport(handler),
    )
    client = TestClient(app)
    raw = (
        b'{"artifact_id":"artifact-1","payload":{"large":"value"},'
        b'"trace_id":"trace-strict"}'
    )
    response = client.post(
        "/ingest/karma",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "bridge-key",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "accepted",
        "trace_id": "trace-strict",
        "received_sha256": response.json()["received_sha256"],
        "stage": "karma-strict",
        "storage": "deferred-to-execution-telemetry",
    }
    assert registry_calls == []


def test_insightflow_core_ingest_only_verifies_trace_identity(
    monkeypatch,
) -> None:
    monkeypatch.setenv("INSIGHTFLOW_BRIDGE_API_KEY", "bridge-key")
    registry_calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        registry_calls.append(request)
        return httpx.Response(500)

    app = create_insightflow(
        registry_base_url="https://registry.test",
        registry_api_key="registry-key",
        transport=httpx.MockTransport(handler),
    )
    client = TestClient(app)
    raw = b'{"source_system":"Mitra","trace_id":"trace-core"}'
    response = client.post(
        "/ingest/core",
        content=raw,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "bridge-key",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "status": "accepted",
        "trace_id": "trace-core",
        "received_sha256": response.json()["received_sha256"],
        "stage": "prana-core",
        "storage": "deferred-to-execution-telemetry",
    }
    assert registry_calls == []
