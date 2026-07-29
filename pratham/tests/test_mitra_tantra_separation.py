from __future__ import annotations

import inspect

from mitra_companion.ecosystem import EcosystemRuntime
from mitra_companion.tantra_runtime import (
    TantraConvergenceRuntime,
    TantraHandoff,
)


def test_mitra_and_tantra_declare_non_overlapping_stage_ownership(runtime):
    status = runtime.ecosystem.status()

    assert status["entity"] == "MITRA"
    assert status["owns_stages"] == [
        "capability-selection",
        "dependency-preflight",
        "raj-execution",
    ]
    assert status["tantra"]["entity"] == "TANTRA"
    assert status["tantra"]["boundary_contract"] == (
        "mitra-to-tantra.post-raj.v1"
    )
    assert not (
        set(status["owns_stages"])
        & set(status["tantra"]["owns_stages"])
    )


def test_mitra_coordinator_cannot_call_post_raj_owner_contracts_directly():
    source = inspect.getsource(EcosystemRuntime)

    for operation in (
        "diagnose_keshav_product_failure",
        "record_ashmit_provenance",
        "persist_bucket",
        "append_karma",
        "forward_prana",
        "emit_insightflow",
        "deposit_central_depository",
    ):
        assert f"self.client.{operation}" not in source

    assert "self.client.execute_raj" in source
    assert "self.tantra.execute" in source


def test_tantra_runtime_owns_post_raj_contract_calls():
    source = inspect.getsource(TantraConvergenceRuntime)

    for operation in (
        "diagnose_keshav_product_failure",
        "record_ashmit_provenance",
        "persist_bucket",
        "append_karma",
        "forward_prana",
        "emit_insightflow",
        "deposit_central_depository",
    ):
        assert f"self.client.{operation}" in source

    assert "self.client.execute_raj" not in source
    assert TantraHandoff.__dataclass_params__.frozen is True
