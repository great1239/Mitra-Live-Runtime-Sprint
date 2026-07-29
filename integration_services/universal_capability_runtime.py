from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from jsonschema import ValidationError, validate

from .common import canonical_bytes, require_api_key, sha256_bytes, utc_now


SUPPORTED_CONTRACT_VERSIONS = {"1.0.0"}
SUPPORTED_RUNTIME_VERSIONS = {"1.0.0"}


def _effective_base_url(requested_base_url: str) -> str:
    value = os.environ.get("CAPABILITY_ENDPOINT_OVERRIDES_JSON", "{}")
    try:
        overrides = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "CAPABILITY_ENDPOINT_OVERRIDES_JSON must be valid JSON"
        ) from exc
    if not isinstance(overrides, dict):
        raise RuntimeError(
            "CAPABILITY_ENDPOINT_OVERRIDES_JSON must be an object"
        )
    normalized = requested_base_url.rstrip("/")
    override = overrides.get(normalized, normalized)
    if not isinstance(override, str):
        raise RuntimeError("Capability endpoint overrides must be strings")
    return override.rstrip("/")


def create_app(
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    app = FastAPI(
        title="Universal Capability Runtime Compatibility Service",
        version="1.0.0",
    )
    app.state.transport = transport
    app.state.capabilities = {}
    app.state.execution_count = 0

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "healthy",
            "service": "universal-capability-runtime",
            "runtime_version": "1.0.0",
            "mode": "product-neutral-compatibility",
            "canonical_owner_certified": False,
            "registered_capabilities": len(app.state.capabilities),
            "execution_count": app.state.execution_count,
        }

    @app.get("/api/v1/capabilities")
    async def capabilities() -> dict[str, Any]:
        return {
            "runtime_version": "1.0.0",
            "capabilities": list(app.state.capabilities.values()),
        }

    @app.post("/api/v1/capabilities/execute")
    async def execute(request: Request) -> dict[str, Any]:
        require_api_key(request, "CAPABILITY_RUNTIME_API_KEY")
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=422, detail="request must be an object")
        trace_id = payload.get("trace_id")
        action_type = payload.get("action_type")
        contract = payload.get("capability_contract")
        contract_version = payload.get("contract_version", "1.0.0")
        requested_runtime = payload.get("runtime_version", "1.0.0")
        if not isinstance(trace_id, str) or not trace_id:
            raise HTTPException(status_code=422, detail="trace_id is required")
        if not isinstance(action_type, str) or not action_type:
            raise HTTPException(status_code=422, detail="action_type is required")
        if not isinstance(contract, dict):
            raise HTTPException(
                status_code=422,
                detail="capability_contract is required",
            )
        if contract_version not in SUPPORTED_CONTRACT_VERSIONS:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "contract_version_not_supported",
                    "supported": sorted(SUPPORTED_CONTRACT_VERSIONS),
                },
            )
        if requested_runtime not in SUPPORTED_RUNTIME_VERSIONS:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "runtime_version_not_supported",
                    "supported": sorted(SUPPORTED_RUNTIME_VERSIONS),
                },
            )

        product = contract.get("product") or {}
        capability = contract.get("capability") or {}
        intent = contract.get("intent") or {}
        dispatch = intent.get("dispatch") or {}
        requested_base_url = product.get("base_url")
        endpoint = dispatch.get("endpoint")
        if not isinstance(requested_base_url, str) or not requested_base_url:
            raise HTTPException(status_code=422, detail="product base_url is required")
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise HTTPException(status_code=422, detail="HTTP dispatch endpoint is required")
        effective_base_url = _effective_base_url(requested_base_url)
        effective_url = urljoin(
            effective_base_url.rstrip("/") + "/",
            endpoint.lstrip("/"),
        )
        if urlparse(effective_url).scheme not in {"http", "https"}:
            raise HTTPException(status_code=422, detail="unsupported dispatch URL")

        original_payload = contract.get("input", {}).get("payload", {})
        if not isinstance(original_payload, dict):
            raise HTTPException(status_code=422, detail="capability input must be an object")
        business_payload = dict(original_payload)
        business_payload.pop("raj_workflow", None)
        arguments = payload.get("arguments")
        if isinstance(arguments, dict):
            business_payload.update(arguments)

        options = dispatch.get("options") or {}
        headers = {
            "Content-Type": "application/json",
            "X-Mitra-Trace-ID": trace_id,
        }
        configured_headers = options.get("headers") or {}
        if not isinstance(configured_headers, dict):
            raise HTTPException(status_code=422, detail="dispatch headers must be an object")
        headers.update(
            {str(key): str(value) for key, value in configured_headers.items()}
        )
        token_environment = options.get("bearer_token_env")
        if token_environment:
            token = os.environ.get(str(token_environment))
            if not token:
                raise HTTPException(
                    status_code=503,
                    detail=f"required product secret is unavailable: {token_environment}",
                )
            headers["Authorization"] = f"Bearer {token}"
        secret_headers = options.get("secret_headers") or {}
        if not isinstance(secret_headers, dict):
            raise HTTPException(
                status_code=422,
                detail="dispatch secret_headers must be an object",
            )
        for name, environment_name in secret_headers.items():
            value = os.environ.get(str(environment_name))
            if not value:
                raise HTTPException(
                    status_code=503,
                    detail=f"required product secret is unavailable: {environment_name}",
                )
            headers[str(name)] = value

        request_body_mode = options.get("request_body", "payload")
        if request_body_mode == "payload":
            product_request = business_payload
        elif request_body_mode == "envelope":
            context = payload.get("mitra_context") or {}
            product_request = {
                "dispatch_id": context.get("execution_id"),
                "correlation_id": trace_id,
                "product_id": product.get("product_id"),
                "capability_id": capability.get("capability_id"),
                "intent_id": intent.get("intent_id"),
                "payload": business_payload,
            }
        else:
            raise HTTPException(
                status_code=422,
                detail="unsupported published request body mode",
            )

        capability_key = ":".join(
            str(item)
            for item in (
                product.get("product_id"),
                capability.get("capability_id"),
                intent.get("intent_id"),
            )
        )
        app.state.capabilities[capability_key] = {
            "capability_key": capability_key,
            "product_id": product.get("product_id"),
            "capability_id": capability.get("capability_id"),
            "intent_id": intent.get("intent_id"),
            "product_version": product.get("product_version"),
            "lifecycle_state": "ACTIVE",
            "contract_version": contract_version,
            "runtime_version": requested_runtime,
        }
        timeout = float(dispatch.get("timeout_seconds") or 45)
        started_at = utc_now()
        request_bytes = canonical_bytes(product_request)

        def product_error(
            error_type: str,
            message: str,
            *,
            http_status: int | None = None,
            response_bytes: bytes | None = None,
            response_body: str | None = None,
        ) -> dict[str, Any]:
            return {
                "status": "product_error",
                "trace_id": trace_id,
                "runtime": {
                    "service": "universal-capability-runtime",
                    "mode": "product-neutral-compatibility",
                    "capability_key": capability_key,
                },
                "execution_result": {
                    "success": False,
                    "trace_id": trace_id,
                    "action_type": action_type,
                    "intent_id": intent.get("intent_id"),
                    "requested_base_url": requested_base_url,
                    "effective_url": effective_url,
                    "http_status": http_status,
                    "request_sha256": sha256_bytes(request_bytes),
                    "response_sha256": (
                        sha256_bytes(response_bytes)
                        if response_bytes is not None
                        else None
                    ),
                    "started_at": started_at,
                    "completed_at": utc_now(),
                    "product_response": None,
                    "error": {
                        "type": error_type,
                        "message": message,
                        "http_status": http_status,
                        "response_body": response_body,
                    },
                },
            }

        try:
            async with httpx.AsyncClient(
                transport=app.state.transport,
                timeout=timeout,
                follow_redirects=bool(options.get("follow_redirects", False)),
            ) as client:
                response = await client.post(
                    effective_url,
                    content=request_bytes,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            return product_error(
                "product_transport_error",
                f"product transport failed: {type(exc).__name__}",
            )
        app.state.execution_count += 1
        if not 200 <= response.status_code < 300:
            return product_error(
                "product_rejected_workflow",
                "product rejected workflow",
                http_status=response.status_code,
                response_bytes=response.content,
                response_body=response.text[:1000],
            )
        try:
            product_response = response.json()
        except ValueError:
            return product_error(
                "product_invalid_json",
                "product did not return JSON",
                http_status=response.status_code,
                response_bytes=response.content,
                response_body=response.text[:1000],
            )
        response_schema = intent.get("response_schema")
        if isinstance(response_schema, dict):
            try:
                validate(product_response, response_schema)
            except ValidationError as exc:
                return product_error(
                    "product_response_contract_error",
                    "product response violated manifest schema: " + exc.message,
                    http_status=response.status_code,
                    response_bytes=response.content,
                    response_body=response.text[:1000],
                )
        return {
            "status": "success",
            "trace_id": trace_id,
            "runtime": {
                "service": "universal-capability-runtime",
                "mode": "product-neutral-compatibility",
                "capability_key": capability_key,
                "contract_version": contract_version,
                "runtime_version": requested_runtime,
            },
            "execution_result": {
                "success": True,
                "trace_id": trace_id,
                "action_type": action_type,
                "intent_id": intent.get("intent_id"),
                "requested_base_url": requested_base_url,
                "effective_url": effective_url,
                "http_status": response.status_code,
                "request_sha256": sha256_bytes(request_bytes),
                "response_sha256": sha256_bytes(response.content),
                "started_at": started_at,
                "completed_at": utc_now(),
                "product_response": product_response,
            },
        }

    return app


app = create_app()
