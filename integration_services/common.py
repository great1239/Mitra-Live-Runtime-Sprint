from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, Request


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def runtime_secret(environment_name: str) -> str | None:
    value = os.environ.get(environment_name)
    if value:
        return value
    prefix = "MITRA_PRODUCT_"
    if environment_name.startswith(prefix):
        return os.environ.get(environment_name[len(prefix):])
    return None


def require_api_key(request: Request, environment_name: str) -> None:
    expected = os.environ.get(environment_name)
    if expected and request.headers.get("x-api-key") != expected:
        raise HTTPException(status_code=401, detail="invalid API key")
