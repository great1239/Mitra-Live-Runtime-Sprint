from __future__ import annotations

import os
from typing import Any
from urllib.parse import urljoin

import httpx
from fastapi import FastAPI, HTTPException, Request

from .common import canonical_bytes, require_api_key, sha256_bytes, utc_now


def create_app(
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    app = FastAPI(title="TANTRA Execution Gateway", version="1.0.0")
    app.state.transport = transport

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "healthy",
            "service": "tantra-execution-gateway",
            "runtime_configured": bool(
                os.environ.get("UNIVERSAL_CAPABILITY_RUNTIME_URL")
            ),
            "authority": "execution-boundary-only",
        }

    @app.post("/api/v1/execute")
    async def execute(request: Request) -> dict[str, Any]:
        require_api_key(request, "TANTRA_EXECUTION_API_KEY")
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=422, detail="request must be an object")
        trace_id = payload.get("trace_id")
        if not isinstance(trace_id, str) or not trace_id:
            raise HTTPException(status_code=422, detail="trace_id is required")
        if not isinstance(payload.get("capability_contract"), dict):
            raise HTTPException(
                status_code=422,
                detail="capability_contract is required",
            )
        runtime_url = os.environ.get("UNIVERSAL_CAPABILITY_RUNTIME_URL")
        if not runtime_url:
            raise HTTPException(
                status_code=503,
                detail="universal capability runtime is not configured",
            )
        body = canonical_bytes(
            {
                **payload,
                "contract_version": payload.get(
                    "contract_version",
                    "1.0.0",
                ),
                "runtime_version": payload.get("runtime_version", "1.0.0"),
            }
        )
        headers = {
            "Content-Type": "application/json",
            "X-Mitra-Trace-ID": trace_id,
        }
        runtime_key = os.environ.get("UNIVERSAL_CAPABILITY_RUNTIME_API_KEY")
        if runtime_key:
            headers["X-API-Key"] = runtime_key
        started_at = utc_now()
        try:
            async with httpx.AsyncClient(
                transport=app.state.transport,
                timeout=float(os.environ.get("TANTRA_EXECUTION_TIMEOUT", "90")),
            ) as client:
                response = await client.post(
                    urljoin(
                        runtime_url.rstrip("/") + "/",
                        "api/v1/capabilities/execute",
                    ),
                    content=body,
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502,
                detail=f"capability runtime transport failed: {type(exc).__name__}",
            ) from exc
        if not 200 <= response.status_code < 300:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "capability runtime rejected execution",
                    "http_status": response.status_code,
                    "body": response.text[:1000],
                },
            )
        result = response.json()
        if result.get("trace_id") != trace_id:
            raise HTTPException(
                status_code=502,
                detail="capability runtime mutated trace_id",
            )
        return {
            **result,
            "tantra": {
                "boundary_contract": "raj-to-tantra-execution.v1",
                "trace_id": trace_id,
                "request_sha256": sha256_bytes(body),
                "response_sha256": sha256_bytes(response.content),
                "started_at": started_at,
                "completed_at": utc_now(),
                "authority": "execution-boundary-only",
            },
        }

    return app


app = create_app()
