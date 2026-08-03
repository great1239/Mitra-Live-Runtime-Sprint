from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from fastapi import FastAPI, HTTPException, Request
from jsonschema import ValidationError, validate

from .common import canonical_bytes, require_api_key, sha256_bytes, utc_now


def _endpoint_overrides() -> dict[str, str]:
    value = os.environ.get("RAJ_ENDPOINT_OVERRIDES_JSON", "{}")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise RuntimeError("RAJ_ENDPOINT_OVERRIDES_JSON must be valid JSON") from exc
    if not isinstance(parsed, dict) or not all(
        isinstance(key, str) and isinstance(item, str)
        for key, item in parsed.items()
    ):
        raise RuntimeError("RAJ_ENDPOINT_OVERRIDES_JSON must be a string map")
    return {
        key.rstrip("/"): item.rstrip("/")
        for key, item in parsed.items()
    }


def _effective_base_url(requested_base_url: str) -> str:
    normalized = requested_base_url.rstrip("/")
    return _endpoint_overrides().get(normalized, normalized)


def create_app(
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    app = FastAPI(title="Raj Workflow Executor", version="1.0.0")
    app.state.transport = transport

    @app.get("/healthz")
    async def healthz() -> dict[str, Any]:
        external_transport = (
            os.environ.get("RAJ_TANTRA_TRANSPORT", "in-process").strip().lower()
            == "external"
        )
        return {
            "status": "ok",
            "service": "workflow-executor",
            "version": "1.0.0",
            "execution_mode": (
                "external-tantra-compatibility"
                if external_transport
                else "in-chain-tantra-runtime"
            ),
            "tantra_configured": True,
            "tantra_transport": (
                "http" if external_transport else "in-process"
            ),
            "capability_runtime_configured": bool(
                os.environ.get("RAJ_CAPABILITY_RUNTIME_URL")
            ),
        }

    @app.post("/api/workflow/execute")
    async def execute(request: Request) -> dict[str, Any]:
        require_api_key(request, "RAJ_API_KEY")
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=422, detail="request must be an object")
        trace_id = payload.get("trace_id")
        owner_payload = payload.get("data", {}).get("payload", {})
        if not isinstance(trace_id, str) or not trace_id:
            raise HTTPException(status_code=422, detail="trace_id is required")
        if not isinstance(owner_payload, dict):
            raise HTTPException(status_code=422, detail="workflow payload is required")
        action_type = owner_payload.get("action_type")
        contract = owner_payload.get("mitra_context", {}).get(
            "capability_contract"
        )
        if not isinstance(action_type, str) or not action_type:
            raise HTTPException(status_code=422, detail="action_type is required")
        if not isinstance(contract, dict):
            raise HTTPException(
                status_code=422,
                detail="selected capability contract is required",
            )
        external_transport = (
            os.environ.get("RAJ_TANTRA_TRANSPORT", "in-process").strip().lower()
            == "external"
        )
        tantra_url = (
            os.environ.get("RAJ_TANTRA_EXECUTION_URL")
            if external_transport
            else None
        )
        if external_transport and not tantra_url:
            raise HTTPException(
                status_code=503,
                detail="external TANTRA compatibility transport is not configured",
            )
        if tantra_url:
            tantra_payload = {
                "trace_id": trace_id,
                "action_type": action_type,
                "capability_contract": contract,
                "arguments": owner_payload.get("arguments"),
                "mitra_context": owner_payload.get("mitra_context") or {},
                "contract_version": "1.0.0",
                "runtime_version": "1.0.0",
            }
            body = canonical_bytes(tantra_payload)
            headers = {
                "Content-Type": "application/json",
                "X-Mitra-Trace-ID": trace_id,
            }
            tantra_key = os.environ.get("RAJ_TANTRA_EXECUTION_API_KEY")
            if tantra_key:
                headers["X-API-Key"] = tantra_key
            try:
                async with httpx.AsyncClient(
                    transport=app.state.transport,
                    timeout=float(os.environ.get("RAJ_TANTRA_TIMEOUT", "120")),
                ) as client:
                    response = await client.post(
                        urljoin(
                            tantra_url.rstrip("/") + "/",
                            "api/v1/execute",
                        ),
                        content=body,
                        headers=headers,
                    )
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=502,
                    detail=f"TANTRA transport failed: {type(exc).__name__}",
                ) from exc
            if not 200 <= response.status_code < 300:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": "TANTRA rejected workflow",
                        "http_status": response.status_code,
                        "body": response.text[:1000],
                    },
                )
            result = response.json()
            if result.get("trace_id") != trace_id:
                raise HTTPException(
                    status_code=502,
                    detail="TANTRA mutated trace_id",
                )
            return {
                **result,
                "raj": {
                    "orchestration_mode": "external-tantra-compatibility",
                    "trace_id": trace_id,
                    "tantra_request_sha256": sha256_bytes(body),
                    "tantra_response_sha256": sha256_bytes(response.content),
                },
            }

        runtime_url = os.environ.get("RAJ_CAPABILITY_RUNTIME_URL")
        if runtime_url:
            runtime_payload = {
                "trace_id": trace_id,
                "action_type": action_type,
                "capability_contract": contract,
                "arguments": owner_payload.get("arguments"),
                "mitra_context": owner_payload.get("mitra_context") or {},
                "contract_version": "1.0.0",
                "runtime_version": "1.0.0",
            }
            runtime_body = canonical_bytes(runtime_payload)
            owner_runtime_body = canonical_bytes(
                {
                    "inputs": runtime_payload,
                    "metadata": {
                        "source": "raj",
                        "trace_id": trace_id,
                    },
                }
            )
            runtime_headers = {
                "Content-Type": "application/json",
                "X-Mitra-Trace-ID": trace_id,
            }
            runtime_key = os.environ.get("RAJ_CAPABILITY_RUNTIME_API_KEY")
            if runtime_key:
                runtime_headers["X-API-Key"] = runtime_key
            started_at = utc_now()
            max_attempts = max(
                1,
                int(os.environ.get("RAJ_CAPABILITY_RUNTIME_ATTEMPTS", "3")),
            )
            retry_statuses = {502, 503, 504}
            attempts: list[dict[str, Any]] = []
            response: httpx.Response | None = None
            async with httpx.AsyncClient(
                transport=app.state.transport,
                timeout=float(
                    os.environ.get("RAJ_CAPABILITY_RUNTIME_TIMEOUT", "150")
                ),
            ) as client:
                for attempt in range(1, max_attempts + 1):
                    attempt_started = utc_now()
                    try:
                        response = await client.post(
                            urljoin(
                                runtime_url.rstrip("/") + "/",
                                "api/capabilities/mitra-remote-product-v1/execute",
                            ),
                            content=owner_runtime_body,
                            headers=runtime_headers,
                        )
                    except httpx.HTTPError as exc:
                        attempts.append(
                            {
                                "attempt": attempt,
                                "started_at": attempt_started,
                                "completed_at": utc_now(),
                                "http_status": None,
                                "error": type(exc).__name__,
                            }
                        )
                        if attempt >= max_attempts:
                            raise HTTPException(
                                status_code=502,
                                detail={
                                    "message": "capability runtime transport failed",
                                    "attempts": attempts,
                                },
                            ) from exc
                    else:
                        attempts.append(
                            {
                                "attempt": attempt,
                                "started_at": attempt_started,
                                "completed_at": utc_now(),
                                "http_status": response.status_code,
                                "error": None,
                            }
                        )
                        if (
                            response.status_code not in retry_statuses
                            or attempt >= max_attempts
                        ):
                            break
                    await asyncio.sleep(min(2 ** (attempt - 1), 4))
            if response is None:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": "capability runtime produced no response",
                        "attempts": attempts,
                    },
                )
            if not 200 <= response.status_code < 300:
                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": "capability runtime rejected execution",
                        "http_status": response.status_code,
                        "body": response.text[:1000],
                        "attempts": attempts,
                    },
                )
            owner_result = response.json()
            if owner_result.get("state") != "completed":
                raise HTTPException(
                    status_code=502,
                    detail={
                        "message": "capability runtime execution failed",
                        "execution_id": owner_result.get("execution_id"),
                        "state": owner_result.get("state"),
                        "error": owner_result.get("error"),
                    },
                )
            result = owner_result.get("outputs") or {}
            if result.get("trace_id") != trace_id:
                raise HTTPException(
                    status_code=502,
                    detail="capability runtime mutated trace_id",
                )
            return {
                **result,
                "canonical_runtime_execution": {
                    "execution_id": owner_result.get("execution_id"),
                    "capability_id": owner_result.get("capability_id"),
                    "state": owner_result.get("state"),
                    "duration_seconds": owner_result.get("duration_seconds"),
                    "retry_count": owner_result.get("retry_count"),
                    "runtime": owner_result.get("runtime"),
                    "transport_attempts": attempts,
                },
                "raj": {
                    "orchestration_mode": "in-chain-tantra-runtime",
                    "trace_id": trace_id,
                },
                "tantra": {
                    "boundary_contract": "raj-to-tantra-execution.v1",
                    "transport": "in-process",
                    "trace_id": trace_id,
                    "request_sha256": sha256_bytes(owner_runtime_body),
                    "response_sha256": sha256_bytes(response.content),
                    "started_at": started_at,
                    "completed_at": utc_now(),
                    "authority": "execution-boundary-only",
                },
            }

        product = contract.get("product") or {}
        intent = contract.get("intent") or {}
        dispatch = intent.get("dispatch") or {}
        requested_base_url = product.get("base_url")
        endpoint = dispatch.get("endpoint")
        if not isinstance(requested_base_url, str) or not requested_base_url:
            raise HTTPException(status_code=422, detail="product base_url is required")
        if not isinstance(endpoint, str) or not endpoint.startswith("/"):
            raise HTTPException(status_code=422, detail="HTTP dispatch endpoint is required")
        effective_base_url = _effective_base_url(requested_base_url)
        effective_url = urljoin(effective_base_url.rstrip("/") + "/", endpoint.lstrip("/"))
        if urlparse(effective_url).scheme not in {"http", "https"}:
            raise HTTPException(status_code=422, detail="unsupported dispatch URL")

        original_payload = contract.get("input", {}).get("payload", {})
        if not isinstance(original_payload, dict):
            raise HTTPException(status_code=422, detail="capability input must be an object")
        business_payload = dict(original_payload)
        business_payload.pop("raj_workflow", None)
        arguments = owner_payload.get("arguments")
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
        headers.update({str(key): str(value) for key, value in configured_headers.items()})
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
                    detail=(
                        "required product secret is unavailable: "
                        f"{environment_name}"
                    ),
                )
            headers[str(name)] = value

        request_body_mode = options.get("request_body", "payload")
        if request_body_mode == "payload":
            product_request = business_payload
        elif request_body_mode == "envelope":
            context = owner_payload.get("mitra_context") or {}
            product_request = {
                "dispatch_id": context.get("execution_id"),
                "correlation_id": trace_id,
                "product_id": product.get("product_id"),
                "capability_id": (contract.get("capability") or {}).get(
                    "capability_id"
                ),
                "intent_id": intent.get("intent_id"),
                "payload": business_payload,
            }
        else:
            raise HTTPException(
                status_code=422,
                detail="unsupported published request body mode",
            )

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
            result = {
                "status": "product_error",
                "trace_id": trace_id,
                "raj": {
                    "orchestration_mode": "in-chain-tantra-runtime",
                    "trace_id": trace_id,
                },
                "tantra": {
                    "boundary_contract": "raj-to-tantra-execution.v1",
                    "transport": "in-process",
                    "trace_id": trace_id,
                    "authority": "execution-boundary-only",
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
            return result

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
                    "product response violated manifest schema: "
                    + exc.message,
                    http_status=response.status_code,
                    response_bytes=response.content,
                    response_body=response.text[:1000],
                )

        response_bytes = response.content
        return {
            "status": "success",
            "trace_id": trace_id,
            "raj": {
                "orchestration_mode": "in-chain-tantra-runtime",
                "trace_id": trace_id,
            },
            "tantra": {
                "boundary_contract": "raj-to-tantra-execution.v1",
                "transport": "in-process",
                "trace_id": trace_id,
                "request_sha256": sha256_bytes(request_bytes),
                "response_sha256": sha256_bytes(response_bytes),
                "started_at": started_at,
                "completed_at": utc_now(),
                "authority": "execution-boundary-only",
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
                "response_sha256": sha256_bytes(response_bytes),
                "started_at": started_at,
                "completed_at": utc_now(),
                "product_response": product_response,
            },
        }

    return app


app = create_app()
