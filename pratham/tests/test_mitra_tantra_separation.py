from __future__ import annotations

import inspect

from mitra_companion.ecosystem import EcosystemRuntime
from mitra_companion.bhiv_downstream import (
    BHIVDownstreamHandoff,
    BHIVDownstreamRuntime,
)


def test_mitra_and_tantra_declare_non_overlapping_stage_ownership(runtime):
    status = runtime.ecosystem.status()

    assert status["entity"] == "MITRA"
    assert status["owns_stages"] == [
        "capability-selection",
        "dependency-preflight",
        "raj-execution",
    ]
    assert status["bhiv_downstream"]["entity"] == "BHIV_DOWNSTREAM"
    assert status["bhiv_downstream"]["boundary_contract"] == (
        "capability-to-bhiv-downstream.v1"
    )
    assert not (
        set(status["owns_stages"])
        & set(status["bhiv_downstream"]["owns_stages"])
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
    assert "self.downstream.execute" in source


def test_bhiv_downstream_runtime_owns_post_capability_contract_calls():
    source = inspect.getsource(BHIVDownstreamRuntime)

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
    assert BHIVDownstreamHandoff.__dataclass_params__.frozen is True
