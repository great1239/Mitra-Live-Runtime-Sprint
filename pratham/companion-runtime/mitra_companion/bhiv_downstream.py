from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Awaitable, Callable
from uuid import uuid4

from .config import RuntimeSettings
from .contracts import EcosystemExecutionRequest
from .errors import EcosystemIntegrationError
from .store import RuntimeStore
from .utils import sha256_json


StageRunner = Callable[
    [str, dict[str, Any], Callable[[], Awaitable[dict[str, Any]]]],
    Awaitable[dict[str, Any]],
]
ReplayRunner = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True, slots=True)
class BHIVDownstreamHandoff:
    """Immutable handoff from capability execution to BHIV services."""

    execution_id: str
    trace_id: str
    artifact_timestamp: str
    request: EcosystemExecutionRequest
    session: dict[str, Any]
    capability_contract: dict[str, Any]
    raj_result: dict[str, Any]

    def summary(self) -> dict[str, Any]:
        return {
            "contract": "capability-to-bhiv-downstream.v1",
            "execution_id": self.execution_id,
            "trace_id": self.trace_id,
            "capability_contract_hash": sha256_json(
                self.capability_contract
            ),
            "raj_result_hash": sha256_json(self.raj_result),
        }


class BHIVDownstreamRuntime:
    """Coordinates published BHIV services after capability execution."""

    boundary_contract = "capability-to-bhiv-downstream.v1"

    def __init__(
        self,
        *,
        settings: RuntimeSettings,
        store: RuntimeStore,
        client: Any,
    ) -> None:
        self.settings = settings
        self.store = store
        self.client = client

    def status(self) -> dict[str, Any]:
        return {
            "entity": "BHIV_DOWNSTREAM",
            "mode": "post-capability-convergence",
            "boundary_contract": self.boundary_contract,
            "owns_stages": [
                "bucket-truth",
                "replay-validation",
                "insightflow-telemetry",
            ],
            "does_not_own": [
                "natural-request",
                "session",
                "capability-selection",
                "raj-execution",
                "product-runtime",
            ],
        }

    async def execute(
        self,
        *,
        handoff: BHIVDownstreamHandoff,
        run_stage: StageRunner,
        replay_prefix: ReplayRunner,
    ) -> dict[str, Any]:
        trace_id = handoff.trace_id
        execution_id = handoff.execution_id
        capability_contract = handoff.capability_contract
        raj_result = handoff.raj_result

        async with self._chain_head_lease(execution_id):
            bucket_result = await run_stage(
                "bucket-truth",
                {
                    "trace_id": trace_id,
                    "execution_id": execution_id,
                    "boundary_contract": self.boundary_contract,
                    "artifact_timestamp": handoff.artifact_timestamp,
                    "raj_result_hash": sha256_json(raj_result),
                },
                lambda: self.client.persist_bucket(
                    trace_id=trace_id,
                    execution_id=execution_id,
                    artifact_timestamp=handoff.artifact_timestamp,
                    capability_contract=capability_contract,
                    raj_result=raj_result,
                ),
            )
        replay_result = await run_stage(
            "replay-validation",
            {
                "trace_id": trace_id,
                "execution_id": execution_id,
                "boundary_contract": self.boundary_contract,
                "bucket_artifact_id": bucket_result["artifact_id"],
                "bucket_artifact_hash": bucket_result["artifact_hash"],
            },
            lambda: replay_prefix(bucket_result),
        )
        insight_result = await run_stage(
            "insightflow-telemetry",
            {
                "trace_id": trace_id,
                "execution_id": execution_id,
                "boundary_contract": self.boundary_contract,
                "raj_result_hash": sha256_json(raj_result),
                "bucket_result_hash": sha256_json(bucket_result),
                "replay_result_hash": sha256_json(replay_result),
            },
            lambda: self.client.emit_insightflow(
                trace_id=trace_id,
                execution_id=execution_id,
                capability_contract=capability_contract,
                raj_result=raj_result,
                bucket_result=bucket_result,
                replay_result=replay_result,
            ),
        )
        return {
            "entity": "BHIV_DOWNSTREAM",
            "boundary": handoff.summary(),
            "results": {
                "bucket": bucket_result,
                "replay": replay_result,
                "insightflow": insight_result,
            },
        }

    def _karma_previous_hash(self, execution_id: str) -> str:
        latest = self.store.latest_completed_ecosystem_stage(
            "karma-integrity",
            exclude_execution_id=execution_id,
        )
        response = latest.get("response") if latest else None
        accepted_hash = (
            response.get("accepted_hash")
            if isinstance(response, dict)
            else None
        )
        if isinstance(accepted_hash, str) and accepted_hash:
            return accepted_hash
        return self.settings.bhiv_karma_previous_hash

    async def _run_integrity_chain(
        self,
        *,
        handoff: BHIVDownstreamHandoff,
        keshav_result: dict[str, Any],
        ashmit_result: dict[str, Any],
        run_stage: StageRunner,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        async with self._chain_head_lease(handoff.execution_id):
            bucket_result = await run_stage(
                "bucket-truth",
                {
                    "trace_id": handoff.trace_id,
                    "execution_id": handoff.execution_id,
                    "boundary_contract": self.boundary_contract,
                    "artifact_timestamp": handoff.artifact_timestamp,
                    "raj_result_hash": sha256_json(handoff.raj_result),
                    "keshav_result_hash": sha256_json(keshav_result),
                    "ashmit_result_hash": sha256_json(ashmit_result),
                },
                lambda: self.client.persist_bucket(
                    trace_id=handoff.trace_id,
                    execution_id=handoff.execution_id,
                    artifact_timestamp=handoff.artifact_timestamp,
                    capability_contract=handoff.capability_contract,
                    raj_result=handoff.raj_result,
                    keshav_result=keshav_result,
                    ashmit_result=ashmit_result,
                ),
            )
            previous_hash = self._karma_previous_hash(
                handoff.execution_id
            )
            karma_result = await run_stage(
                "karma-integrity",
                {
                    "trace_id": handoff.trace_id,
                    "boundary_contract": self.boundary_contract,
                    "bucket_payload": bucket_result["bucket_payload"],
                    "previous_hash": previous_hash,
                },
                lambda: self.client.append_karma(
                    trace_id=handoff.trace_id,
                    bucket_result=bucket_result,
                    previous_hash=previous_hash,
                ),
            )
            return bucket_result, karma_result

    @asynccontextmanager
    async def _chain_head_lease(
        self,
        execution_id: str,
    ) -> AsyncIterator[None]:
        lease_name = "bhiv-downstream-bucket-karma-chain-heads"
        lease_holder = f"{execution_id}:{uuid4().hex}"
        operation_timeout = max(
            1.0,
            self.settings.ecosystem_timeout_seconds,
        )
        deadline = time.monotonic() + (operation_timeout * 2)
        acquired = False
        while time.monotonic() < deadline:
            lease = self.store.claim_runtime_lease(
                lease_name=lease_name,
                instance_id=lease_holder,
                lease_seconds=(operation_timeout * 2) + 1,
            )
            if lease["acquired"]:
                acquired = True
                break
            await asyncio.sleep(0.025)
        if not acquired:
            raise EcosystemIntegrationError(
                "Timed out waiting for a BHIV downstream artifact chain head"
            )
        try:
            yield
        finally:
            self.store.release_runtime_leases(lease_holder)
