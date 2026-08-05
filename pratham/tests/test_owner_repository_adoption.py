import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _manifest(name: str) -> dict:
    return json.loads((ROOT / "contracts" / "production" / name).read_text())


def test_render_blueprint_runs_product_owner_repositories_directly() -> None:
    blueprint = (ROOT / "render.yaml").read_text(encoding="utf-8")

    expected_owner_services = {
        "pratham-uniguru-owner-runtime": "VJY123VJY/uniguru_ai",
        "pratham-samruddhi-owner-runtime": (
            "great1239/mitra-owner-samruddhi-runtime"
        ),
        "pratham-sl-validator-owner-runtime": (
            "great1239/mitra-owner-sl-validator"
        ),
    }
    for service, repository in expected_owner_services.items():
        assert f"name: {service}" in blueprint
        assert f"repo: https://github.com/{repository}" in blueprint


def test_owner_targets_are_active_after_health_and_dispatch_validation() -> None:
    targets = {
        "product-samruddhi-uniguru.json": (
            "https://pratham-uniguru-owner-runtime.onrender.com"
        ),
        "product-samruddhi-trade-bot.json": (
            "https://pratham-samruddhi-owner-runtime.onrender.com"
        ),
    }
    for filename, target in targets.items():
        manifest = _manifest(filename)
        assert manifest["metadata"]["owner_runtime_target"] == target
        assert manifest["metadata"]["recovery_runtime"] is False
        assert manifest["base_url"] == target


def test_stock_display_uses_owner_market_data_capability() -> None:
    manifest = _manifest("product-samruddhi-trade-bot.json")
    capability = manifest["capabilities"][0]
    intent = capability["intents"][0]

    assert capability["capability_id"] == "market-data"
    assert intent["intent_id"] == "samruddhi.tradebot.fetch_data"
    assert intent["dispatch"]["endpoint"] == "/tools/fetch_data"


def test_active_setu_manifest_tracks_current_owner_repository_head() -> None:
    manifest = _manifest("product-setu-ai-crm.json")

    assert manifest["metadata"]["source_repository"] == (
        "https://github.com/blackholeinfiverse51/ai-crm"
    )
    assert manifest["metadata"]["source_repository_head"] == (
        "e09f560c0488b4e8e17e58a1d7a84337b09c2018"
    )
    assert manifest["base_url"] == "https://pratham-setu-ai-crm.onrender.com"
