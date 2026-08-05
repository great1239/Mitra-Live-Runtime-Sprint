from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient


OWNER_RUNTIME = os.environ.get("KANISHK_OWNER_RUNTIME_PATH")
if not OWNER_RUNTIME or not Path(OWNER_RUNTIME).is_dir():
    pytest.skip(
        "KANISHK_OWNER_RUNTIME_PATH is required for owner-runtime tests",
        allow_module_level=True,
    )
sys.path.insert(0, OWNER_RUNTIME)
os.environ.setdefault("MITRA_DATA_DIR", str(Path(OWNER_RUNTIME) / ".test-data"))

from integration_services.kanishk_runtime_adapter import create_app


def _request(capability_id: str = "market-prediction") -> dict:
    return {
        "inputs": {
            "trace_id": "trace-owner-capability",
            "action_type": "task",
            "capability_contract": {
                "product": {
                    "product_id": "samruddhi-trade-bot",
                    "product_version": "4.0.0",
                    "base_url": "https://product.test",
                },
                "capability": {
                    "capability_id": capability_id,
                    "description": "Owner stock market prediction capability",
                    "metadata": {
                        "source_repository": (
                            "https://github.com/harshapawar136/"
                            "trade-bot-main"
                        )
                    },
                },
                "intent": {
                    "intent_id": "samruddhi.tradebot.predict",
                    "dispatch": {
                        "endpoint": "/tools/predict",
                        "options": {"request_body": "payload"},
                    },
                    "response_schema": {
                        "type": "object",
                        "required": ["status", "predictions"],
                    },
                },
                "input": {"payload": {"symbols": ["AAPL"]}},
            },
        },
        "metadata": {"source": "raj"},
    }


def test_ucr_registers_and_executes_manifest_owner_capability(monkeypatch) -> None:
    monkeypatch.setenv("CAPABILITY_RUNTIME_API_KEY", "owner-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/tools/predict"
        assert json.loads(request.content) == {"symbols": ["AAPL"]}
        return httpx.Response(
            200,
            json={"status": "ok", "predictions": [{"symbol": "AAPL"}]},
        )

    client = TestClient(create_app(transport=httpx.MockTransport(handler)))
    response = client.post(
        "/api/capabilities/market-prediction/execute",
        json=_request(),
        headers={"X-API-Key": "owner-key"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["capability_id"] == "market-prediction"
    capabilities = client.get("/api/capabilities").json()
    assert [item["capability_id"] for item in capabilities] == [
        "market-prediction"
    ]
    assert capabilities[0]["metadata"] == {
        "attachment_source": "mitra-product-manifest",
        "intent_id": "samruddhi.tradebot.predict",
        "product_id": "samruddhi-trade-bot",
        "source_repository": (
            "https://github.com/harshapawar136/trade-bot-main"
        ),
    }


def test_ucr_rejects_capability_id_not_declared_by_manifest(monkeypatch) -> None:
    monkeypatch.setenv("CAPABILITY_RUNTIME_API_KEY", "owner-key")
    client = TestClient(
        create_app(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(500)
            )
        )
    )

    response = client.post(
        "/api/capabilities/invented-capability/execute",
        json=_request("market-prediction"),
        headers={"X-API-Key": "owner-key"},
    )

    assert response.status_code == 409
    assert "established manifest capability_id" in response.json()["detail"]


def test_ucr_rejects_capability_owner_collision(monkeypatch) -> None:
    monkeypatch.setenv("CAPABILITY_RUNTIME_API_KEY", "owner-key")
    client = TestClient(
        create_app(
            transport=httpx.MockTransport(
                lambda request: httpx.Response(
                    200,
                    json={"status": "ok", "predictions": []},
                )
            )
        )
    )
    headers = {"X-API-Key": "owner-key"}
    assert client.post(
        "/api/capabilities/market-prediction/execute",
        json=_request(),
        headers=headers,
    ).status_code == 200

    conflicting = _request()
    contract = conflicting["inputs"]["capability_contract"]
    contract["product"]["product_id"] = "different-product"
    contract["capability"]["metadata"]["source_repository"] = (
        "https://github.com/example/different-product"
    )
    response = client.post(
        "/api/capabilities/market-prediction/execute",
        json=conflicting,
        headers=headers,
    )

    assert response.status_code == 409
    assert "different owner capability" in response.json()["detail"]
