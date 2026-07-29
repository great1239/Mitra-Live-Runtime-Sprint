from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from urllib.error import HTTPError

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_uniguru_recovery_returns_documented_kosha_result() -> None:
    module = _load(
        "uniguru_recovery",
        ROOT / "product_recovery" / "uniguru" / "api" / "index.py",
    )
    client = TestClient(module.app)
    assert client.get("/health").json()["status"] == "healthy"

    response = client.post(
        "/ask",
        json={"query": "reduce water consumption via drip irrigation"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["domain"] == "Agriculture"
    assert payload["signals"][0]["trace"]["knowledge_id"] == "K_AGRI_002"


def test_trade_bot_recovery_preserves_requested_symbol(monkeypatch) -> None:
    module = _load(
        "trade_bot_recovery",
        ROOT / "product_recovery" / "trade_bot" / "api" / "index.py",
    )
    monkeypatch.setattr(
        module,
        "_fetch_chart",
        lambda symbol, range_value, interval: {
            "meta": {
                "symbol": symbol,
                "currency": "USD",
                "exchangeName": "NMS",
            },
            "indicators": {"quote": [{"close": [100.0, 103.0]}]},
        },
    )
    client = TestClient(module.app)
    assert client.get("/tools/health").json()["status"] == "healthy"

    response = client.post(
        "/tools/predict",
        json={"symbols": ["NVDA"], "horizon": "short"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["metadata"]["requested_symbols"] == ["NVDA"]
    assert payload["predictions"][0]["symbol"] == "NVDA"
    assert payload["predictions"][0]["resolved_symbol"] == "NVDA"
    assert payload["predictions"][0]["action"] == "LONG"


def test_trade_bot_recovery_resolves_provider_symbol_after_404(
    monkeypatch,
) -> None:
    module = _load(
        "trade_bot_recovery_resolution",
        ROOT / "product_recovery" / "trade_bot" / "api" / "index.py",
    )
    requested: list[str] = []

    def fetch(symbol, range_value, interval):
        requested.append(symbol)
        if symbol == "TMPV":
            raise HTTPError("https://finance.test", 404, "missing", {}, None)
        return {
            "meta": {
                "symbol": "TMPV.NS",
                "currency": "INR",
                "exchangeName": "NSI",
            },
            "indicators": {"quote": [{"close": [350.0, 352.0]}]},
        }

    monkeypatch.setattr(module, "_fetch_chart", fetch)
    monkeypatch.setattr(module, "_resolve_symbol", lambda symbol: "TMPV.NS")
    client = TestClient(module.app)
    response = client.post(
        "/tools/predict",
        json={"symbols": ["TMPV"], "horizon": "short"},
    )

    assert response.status_code == 200
    prediction = response.json()["predictions"][0]
    assert requested == ["TMPV", "TMPV.NS"]
    assert prediction["symbol"] == "TMPV"
    assert prediction["resolved_symbol"] == "TMPV.NS"
    assert prediction["currency"] == "INR"
