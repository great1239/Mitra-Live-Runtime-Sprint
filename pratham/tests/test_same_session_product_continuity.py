from __future__ import annotations

import json
from pathlib import Path

from mitra_companion.contracts import ProductAttachmentManifest


ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_CONTRACTS = ROOT / "contracts" / "production"


def _production_manifest(name: str) -> ProductAttachmentManifest:
    return ProductAttachmentManifest.model_validate(
        json.loads(
            (PRODUCTION_CONTRACTS / name).read_text(encoding="utf-8")
        )
    )


def _future_manifest() -> ProductAttachmentManifest:
    payload = json.loads(
        (ROOT / "contracts" / "examples" / "product-atlas.json").read_text(
            encoding="utf-8"
        )
    )
    payload["product_id"] = "future-manifest-product"
    payload["display_name"] = "Future Manifest Product"
    return ProductAttachmentManifest.model_validate(payload)


def test_production_products_share_session_context_and_runtime(runtime):
    product_ids = [
        "samruddhi-trade-bot",
        "samruddhi-uniguru",
        "setu-ai-crm",
        "future-manifest-product",
    ]
    for name in (
        "product-samruddhi-trade-bot.json",
        "product-samruddhi-uniguru.json",
        "product-setu-ai-crm.json",
    ):
        runtime.attach(_production_manifest(name))
    runtime.attach(_future_manifest())

    session = runtime.sessions.create(
        actor_id="cross-product-user",
        client_type="standalone",
        workspace_id="shared-bhiv-workspace",
        product_id=product_ids[0],
    )
    session_id = session["session_id"]
    runtime_id = runtime.instance_id
    runtime.context.update(
        session_id=session_id,
        scope="session",
        patch={"conversation_goal": "operate across BHIV products"},
        expected_revision=0,
        replace=True,
    )
    runtime.context.update(
        session_id=session_id,
        scope="workspace",
        patch={"workspace_case": "case-42"},
        expected_revision=0,
        replace=True,
    )

    private_values = {
        "samruddhi-trade-bot": {"selected_symbol": "TMPV"},
        "samruddhi-uniguru": {"learning_topic": "light speed"},
        "setu-ai-crm": {"inventory_filter": "low-stock"},
        "future-manifest-product": {"future_state": "attached"},
    }
    for product_id in product_ids:
        activation = runtime.activate_session_product(
            session_id,
            product_id,
        )
        assert activation["session"]["session_id"] == session_id
        assert activation["runtime_instance_id"] == runtime_id
        loaded_before = activation["context"]["merged"]
        assert loaded_before["conversation_goal"] == (
            "operate across BHIV products"
        )
        assert loaded_before["workspace_case"] == "case-42"
        runtime.context.update(
            session_id=session_id,
            scope="product",
            patch=private_values[product_id],
            expected_revision=0,
            replace=True,
        )

    for product_id in product_ids:
        activation = runtime.activate_session_product(
            session_id,
            product_id,
        )
        merged = activation["context"]["merged"]
        assert activation["session"]["session_id"] == session_id
        assert activation["runtime_instance_id"] == runtime_id
        assert merged["conversation_goal"] == "operate across BHIV products"
        assert merged["workspace_case"] == "case-42"
        assert all(
            merged.get(key) == value
            for key, value in private_values[product_id].items()
        )
        other_keys = {
            key
            for other_product, values in private_values.items()
            if other_product != product_id
            for key in values
        }
        assert not other_keys.intersection(merged)

    final_session = runtime.sessions.get(session_id)
    assert final_session["metadata"]["product_history"] == product_ids
