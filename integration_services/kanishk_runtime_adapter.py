"""Bind MITRA product contracts to Kanishk's canonical execution fabric."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from jsonschema import ValidationError, validate
from pydantic import BaseModel

from mitra_runtime.bucket import BucketStore
from mitra_runtime.engine import ExecutionContext, ExecutionEngine
from mitra_runtime.events import EventBus
from mitra_runtime.health import HealthMonitor
from mitra_runtime.lifecycle import LifecycleManager
from mitra_runtime.models import CapabilityDescriptor, ExecutionMode, RetryPolicy
from mitra_runtime.registry import CapabilityRegistry

from .common import (
    canonical_bytes,
    require_api_key,
    runtime_secret,
    sha256_bytes,
    utc_now,
)


OWNER_REPOSITORY = (
    "https://github.com/blackholeinfiverse107-creator/"
    "Mitra-runtime_execution_fabric"
)
OWNER_COMMIT = "74a5efdd4d3c079d415903c4e151250bf4642f57"
REMOTE_DISPATCH_CAPABILITY = "mitra-remote-product-v1"


class ExecuteRequest(BaseModel):
    inputs: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


def _effective_base_url(requested_base_url: str) -> str:
    try:
        overrides = json.loads(
            os.environ.get("CAPABILITY_ENDPOINT_OVERRIDES_JSON", "{}")
        )
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "CAPABILITY_ENDPOINT_OVERRIDES_JSON must be valid JSON"
        ) from exc
    if not isinstance(overrides, dict):
        raise RuntimeError("CAPABILITY_ENDPOINT_OVERRIDES_JSON must be an object")
    normalized = requested_base_url.rstrip("/")
    effective = overrides.get(normalized, normalized)
    if not isinstance(effective, str):
        raise RuntimeError("Capability endpoint overrides must be strings")
    return effective.rstrip("/")


def create_app(
    *, transport: httpx.BaseTransport | None = None
) -> FastAPI:
    registry = CapabilityRegistry(auto_persist=False)
    events = EventBus(max_history=1000)
    lifecycle = LifecycleManager(strict=True)
    engine = ExecutionEngine(
        registry=registry,
        max_workers=int(os.environ.get("KANISHK_RUNTIME_MAX_WORKERS", "8")),
        queue_size=int(os.environ.get("KANISHK_RUNTIME_QUEUE_SIZE", "100")),
        event_bus=events,
        lifecycle=lifecycle,
    )
    health = HealthMonitor(registry=registry)
    data_dir = Path(os.environ.get("MITRA_DATA_DIR", "/data/kanishk-runtime"))
    data_dir.mkdir(parents=True, exist_ok=True)
    bucket = BucketStore(
        event_bus=events,
        persistence_path=data_dir / "execution_records.jsonl",
    )

    app = FastAPI(
        title="Kanishk Universal Capability Runtime - MITRA Integration",
        version="1.0.0",
        description=(
            "Canonical Kanishk execution fabric with a product-neutral MITRA "
            "remote capability handler."
        ),
    )
    app.state.registry = registry
    app.state.engine = engine
    app.state.lifecycle = lifecycle
    app.state.health = health
    app.state.bucket = bucket
    app.state.transport = transport

    def remote_product_handler(ctx: ExecutionContext) -> dict[str, Any]:
        payload = dict(ctx.inputs or {})
        trace_id = payload.get("trace_id")
        action_type = payload.get("action_type")
        contract = payload.get("capability_contract")
        if not isinstance(trace_id, str) or not trace_id:
            raise ValueError("trace_id is required")
        if not isinstance(action_type, str) or not action_type:
            raise ValueError("action_type is required")
        if not isinstance(contract, dict):
            raise ValueError("capability_contract is required")

        product = contract.get("product") or {}
        capability = contract.get("capability") or {}
        intent = contract.get("intent") or {}
        dispatch = intent.get("dispatch") or {}
        requested_base_url = product.get("base_url")
        endpoint = dispatch.get("endpoint")
        if not isinstance(requested_base_url, str) or not requested_base_url:
            raise ValueError("product base_url is required")
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise ValueError("HTTP dispatch endpoint is required")

        effective_base_url = _effective_base_url(requested_base_url)
        effective_url = urljoin(
            effective_base_url.rstrip("/") + "/", endpoint.lstrip("/")
        )
        if urlparse(effective_url).scheme not in {"http", "https"}:
            raise ValueError("unsupported dispatch URL")

        business_payload = dict(contract.get("input", {}).get("payload") or {})
        business_payload.pop("raj_workflow", None)
        if isinstance(payload.get("arguments"), dict):
            business_payload.update(payload["arguments"])

        options = dispatch.get("options") or {}
        headers = {
            "Content-Type": "application/json",
            "X-Mitra-Trace-ID": trace_id,
        }
        configured_headers = options.get("headers") or {}
        if not isinstance(configured_headers, dict):
            raise ValueError("dispatch headers must be an object")
        headers.update({str(key): str(value) for key, value in configured_headers.items()})
        token_environment = options.get("bearer_token_env")
        if token_environment:
            token = runtime_secret(str(token_environment))
            if not token:
                raise ValueError(
                    f"required product secret is unavailable: {token_environment}"
                )
            headers["Authorization"] = f"Bearer {token}"
        secret_headers = options.get("secret_headers") or {}
        if not isinstance(secret_headers, dict):
            raise ValueError("dispatch secret_headers must be an object")
        for name, environment_name in secret_headers.items():
            value = runtime_secret(str(environment_name))
            if not value:
                raise ValueError(
                    f"required product secret is unavailable: {environment_name}"
                )
            headers[str(name)] = value

        if options.get("request_body", "payload") == "envelope":
            mitra_context = payload.get("mitra_context") or {}
            product_request = {
                "dispatch_id": mitra_context.get("execution_id"),
                "correlation_id": trace_id,
                "product_id": product.get("product_id"),
                "capability_id": capability.get("capability_id"),
                "intent_id": intent.get("intent_id"),
                "payload": business_payload,
            }
        else:
            product_request = business_payload

        started_at = utc_now()
        request_bytes = canonical_bytes(product_request)
        try:
            with httpx.Client(
                transport=app.state.transport,
                timeout=float(dispatch.get("timeout_seconds") or 45),
                follow_redirects=bool(options.get("follow_redirects", False)),
            ) as client:
                response = client.post(
                    effective_url,
                    content=request_bytes,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            return _runtime_output(
                trace_id=trace_id,
                action_type=action_type,
                intent_id=intent.get("intent_id"),
                requested_base_url=requested_base_url,
                effective_url=effective_url,
                request_bytes=request_bytes,
                started_at=started_at,
                error={
                    "type": "product_transport_error",
                    "message": f"product transport failed: {type(exc).__name__}",
                },
            )

        if not 200 <= response.status_code < 300:
            return _runtime_output(
                trace_id=trace_id,
                action_type=action_type,
                intent_id=intent.get("intent_id"),
                requested_base_url=requested_base_url,
                effective_url=effective_url,
                request_bytes=request_bytes,
                started_at=started_at,
                response=response,
                error={
                    "type": "product_rejected_workflow",
                    "message": "product rejected workflow",
                    "http_status": response.status_code,
                    "response_body": response.text[:1000],
                },
            )
        try:
            product_response = response.json()
        except ValueError:
            return _runtime_output(
                trace_id=trace_id,
                action_type=action_type,
                intent_id=intent.get("intent_id"),
                requested_base_url=requested_base_url,
                effective_url=effective_url,
                request_bytes=request_bytes,
                started_at=started_at,
                response=response,
                error={
                    "type": "product_invalid_json",
                    "message": "product did not return JSON",
                    "http_status": response.status_code,
                    "response_body": response.text[:1000],
                },
            )
        response_schema = intent.get("response_schema")
        if isinstance(response_schema, dict):
            try:
                validate(product_response, response_schema)
            except ValidationError as exc:
                return _runtime_output(
                    trace_id=trace_id,
                    action_type=action_type,
                    intent_id=intent.get("intent_id"),
                    requested_base_url=requested_base_url,
                    effective_url=effective_url,
                    request_bytes=request_bytes,
                    started_at=started_at,
                    response=response,
                    error={
                        "type": "product_response_contract_error",
                        "message": (
                            "product response violated manifest schema: "
                            + exc.message
                        ),
                        "http_status": response.status_code,
                    },
                )
        return _runtime_output(
            trace_id=trace_id,
            action_type=action_type,
            intent_id=intent.get("intent_id"),
            requested_base_url=requested_base_url,
            effective_url=effective_url,
            request_bytes=request_bytes,
            started_at=started_at,
            response=response,
            product_response=product_response,
        )

    registry.register(
        CapabilityDescriptor(
            capability_id=REMOTE_DISPATCH_CAPABILITY,
            name="MITRA Remote Product Dispatch",
            version="1.0.0",
            description=(
                "Executes a selected MITRA product capability from its "
                "published manifest contract."
            ),
            execution_mode=ExecutionMode.SYNC,
            timeout_seconds=180.0,
            retry_policy=RetryPolicy(max_retries=0),
        )
    )
    engine.register_handler(REMOTE_DISPATCH_CAPABILITY, remote_product_handler)

    @app.on_event("startup")
    def startup() -> None:
        engine.start_queue_workers()

    @app.on_event("shutdown")
    def shutdown() -> None:
        engine.shutdown()

    @app.get("/health")
    @app.get("/api/health")
    def runtime_health() -> dict[str, Any]:
        report = health.get_health_report().to_dict()
        return {
            **report,
            "status": "healthy" if report["overall_status"] != "unhealthy" else "unhealthy",
            "service": "kanishk-universal-capability-runtime",
            "canonical_owner_runtime": True,
            "owner_repository": OWNER_REPOSITORY,
            "owner_commit": OWNER_COMMIT,
            "integration_capability": REMOTE_DISPATCH_CAPABILITY,
        }

    @app.get("/api/capabilities")
    def capabilities() -> list[dict[str, Any]]:
        # The owner API calls CapabilityDescriptor.to_dict(), but the pinned
        # owner model is a dataclass and does not implement that method.
        return [asdict(item) for item in registry.list_all()]

    @app.post("/api/capabilities/{capability_id}/execute")
    def execute(
        capability_id: str, payload: ExecuteRequest, request: Request
    ) -> dict[str, Any]:
        require_api_key(request, "CAPABILITY_RUNTIME_API_KEY")
        if not engine.has_handler(capability_id):
            raise HTTPException(status_code=404, detail="capability not registered")
        result = engine.execute(
            capability_id=capability_id,
            inputs=payload.inputs or {},
            metadata=payload.metadata or {},
        )
        return {
            "execution_id": result.execution_id,
            "capability_id": result.capability_id,
            "state": str(result.state),
            "duration_seconds": result.duration_seconds,
            "outputs": result.outputs,
            "error": result.error,
            "retry_count": result.retry_count,
            "runtime": {
                "service": "kanishk-universal-capability-runtime",
                "owner_repository": OWNER_REPOSITORY,
                "owner_commit": OWNER_COMMIT,
            },
        }

    @app.get("/api/executions/{execution_id}")
    def execution(execution_id: str, request: Request) -> dict[str, Any]:
        require_api_key(request, "CAPABILITY_RUNTIME_API_KEY")
        result = engine.get_result(execution_id)
        record = lifecycle.get(execution_id)
        return {
            "execution_id": execution_id,
            "result": result.__dict__ if result else None,
            "timeline": record.get_timeline() if record else [],
            "active": execution_id in engine.get_active_executions(),
        }

    @app.get("/api/bucket/records")
    def bucket_records(request: Request) -> list[dict[str, Any]]:
        require_api_key(request, "CAPABILITY_RUNTIME_API_KEY")
        return bucket.get_all_records()

    return app


def _runtime_output(
    *,
    trace_id: str,
    action_type: str,
    intent_id: Any,
    requested_base_url: str,
    effective_url: str,
    request_bytes: bytes,
    started_at: str,
    response: httpx.Response | None = None,
    product_response: Any = None,
    error: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "status": "success" if error is None else "product_error",
        "trace_id": trace_id,
        "runtime": {
            "service": "kanishk-universal-capability-runtime",
            "mode": "canonical-owner-engine",
            "owner_repository": OWNER_REPOSITORY,
            "owner_commit": OWNER_COMMIT,
        },
        "execution_result": {
            "success": error is None,
            "trace_id": trace_id,
            "action_type": action_type,
            "intent_id": intent_id,
            "requested_base_url": requested_base_url,
            "effective_url": effective_url,
            "http_status": response.status_code if response else None,
            "request_sha256": sha256_bytes(request_bytes),
            "response_sha256": sha256_bytes(response.content) if response else None,
            "started_at": started_at,
            "completed_at": utc_now(),
            "product_response": product_response,
            "error": error,
        },
    }


app = create_app()
