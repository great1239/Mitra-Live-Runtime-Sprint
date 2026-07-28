from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field


app = FastAPI(
    title="UniGuru Recovery Runtime",
    version="1.0.0",
    description="Independent recovery deployment of UniGuru's published query contract.",
)

KNOWLEDGE = (
    {
        "knowledge_id": "K_AGRI_002",
        "domain": "Agriculture",
        "content": (
            "Drip irrigation delivers water directly to the root zone and can "
            "reduce water consumption by up to 60% compared with traditional "
            "flood irrigation in arid regions."
        ),
        "source": "UniGuru repository README: documented Kosha example",
        "tags": ("drip", "irrigation", "water", "consumption", "agriculture"),
        "confidence": 0.92,
    },
    {
        "knowledge_id": "K_PHYSICS_001",
        "domain": "Physics",
        "content": (
            "Light travels at exactly 299,792,458 metres per second in a vacuum, "
            "approximately 299,792 kilometres per second."
        ),
        "source": "SI definition of the metre",
        "tags": ("light", "speed", "travel", "vacuum", "physics"),
        "confidence": 1.0,
    },
)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000)
    context: dict[str, Any] | None = None
    allow_web: bool = False
    session_id: str | None = Field(default=None, max_length=128)


class RagRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=2000)
    domain: str | None = None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


def _retrieve(query: str, domain: str | None = None) -> dict[str, Any]:
    query_tokens = _tokens(query)
    ranked: list[tuple[int, dict[str, Any]]] = []
    for record in KNOWLEDGE:
        haystack = set(record["tags"]) | _tokens(record["content"])
        score = len(query_tokens & haystack)
        if domain and domain.casefold() == str(record["domain"]).casefold():
            score += 2
        ranked.append((score, record))
    score, record = max(ranked, key=lambda item: item[0])
    trace_id = hashlib.sha256(
        f"{query.strip()}|{record['knowledge_id']}".encode("utf-8")
    ).hexdigest()
    if score == 0:
        return {
            "status": "rejected",
            "query": query,
            "answer": "Knowledge not found in verified ontology.",
            "confidence": 0.0,
            "signals": [],
            "trace_id": trace_id,
            "timestamp": _utc_now(),
            "runtime": "uniguru-recovery",
        }
    signal = {
        "signal_id": f"sig_{trace_id[:12]}",
        "signal_type": "KOSHA_VERIFIED",
        "content": record["content"],
        "confidence": record["confidence"],
        "source": record["source"],
        "trace": {
            "knowledge_id": record["knowledge_id"],
            "retrieval_method": "deterministic_keyword_tag_match",
            "mapped_domain": record["domain"],
        },
    }
    return {
        "status": "success",
        "query": query,
        "domain": record["domain"],
        "answer": record["content"],
        "confidence": record["confidence"],
        "signals": [signal],
        "trace_id": trace_id,
        "timestamp": _utc_now(),
        "runtime": "uniguru-recovery",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "uniguru-recovery",
        "contract": "uniguru-query-v1",
        "knowledge_records": len(KNOWLEDGE),
        "timestamp": _utc_now(),
    }


@app.post("/ask")
def ask(request: AskRequest) -> dict[str, Any]:
    domain = None
    if request.context:
        domain = request.context.get("domain")
    return _retrieve(request.query, str(domain) if domain else None)


@app.post("/new_rag")
def new_rag(request: RagRequest) -> dict[str, Any]:
    return _retrieve(request.query, request.domain)
