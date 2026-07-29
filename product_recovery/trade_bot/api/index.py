from __future__ import annotations

import asyncio
import json
import math
import urllib.parse
import urllib.request
from urllib.error import HTTPError
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator


app = FastAPI(
    title="Samruddhi Trade Bot Recovery Runtime",
    version="1.0.0",
    description="Independent recovery deployment of the published Trade Bot contract.",
)

YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
YAHOO_SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"


class PredictRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbols: list[str] = Field(min_length=1, max_length=50)
    horizon: str = "intraday"
    risk_profile: str | None = "moderate"
    stop_loss_pct: float | None = Field(default=2.0, ge=0.1, le=50.0)
    capital_risk_pct: float | None = Field(default=1.0, ge=0.1, le=100.0)
    drawdown_limit_pct: float | None = Field(default=5.0, ge=0.1, le=100.0)

    @field_validator("symbols")
    @classmethod
    def normalize_symbols(cls, value: list[str]) -> list[str]:
        symbols = [item.strip().upper() for item in value if item.strip()]
        if not symbols:
            raise ValueError("At least one symbol is required.")
        return symbols

    @field_validator("horizon")
    @classmethod
    def validate_horizon(cls, value: str) -> str:
        value = value.lower()
        if value not in {"intraday", "short", "long"}:
            raise ValueError("horizon must be intraday, short, or long")
        return value


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=20)
    horizons: list[str] = Field(default_factory=lambda: ["intraday"])
    stop_loss_pct: float = Field(default=2.0, ge=0.1, le=50.0)
    capital_risk_pct: float = Field(default=1.0, ge=0.1, le=100.0)
    drawdown_limit_pct: float = Field(default=5.0, ge=0.1, le=100.0)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fetch_chart(symbol: str, range_value: str, interval: str) -> dict[str, Any]:
    encoded = urllib.parse.quote(symbol, safe=".")
    url = YAHOO_CHART_URL.format(symbol=encoded)
    url += "?" + urllib.parse.urlencode(
        {"range": range_value, "interval": interval, "includePrePost": "false"}
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mitra-Samruddhi-Recovery/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    result = ((payload.get("chart") or {}).get("result") or [None])[0]
    if not result:
        error = (payload.get("chart") or {}).get("error") or {}
        raise ValueError(error.get("description") or f"No market data for {symbol}")
    return result


def _resolve_symbol(symbol: str) -> str:
    url = YAHOO_SEARCH_URL + "?" + urllib.parse.urlencode(
        {"q": symbol, "quotesCount": 8, "newsCount": 0}
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mitra-Samruddhi-Recovery/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    quotes = payload.get("quotes") or []
    requested = symbol.upper()
    candidates = [
        quote
        for quote in quotes
        if isinstance(quote, dict)
        and quote.get("quoteType") in {"EQUITY", "ETF", "INDEX"}
        and isinstance(quote.get("symbol"), str)
    ]
    exact = next(
        (
            quote["symbol"]
            for quote in candidates
            if quote["symbol"].upper() == requested
        ),
        None,
    )
    if exact:
        return exact
    exchange_qualified = next(
        (
            quote["symbol"]
            for quote in candidates
            if quote["symbol"].upper().split(".", 1)[0] == requested
        ),
        None,
    )
    if exchange_qualified:
        return exchange_qualified
    raise ValueError(f"Yahoo Finance could not resolve market symbol {symbol}")


def _period(horizon: str) -> tuple[str, str]:
    if horizon == "long":
        return "1y", "1d"
    if horizon == "short":
        return "3mo", "1d"
    return "5d", "15m"


def _analyze_chart(symbol: str, horizon: str) -> dict[str, Any]:
    range_value, interval = _period(horizon)
    resolved_input = symbol
    try:
        chart = _fetch_chart(resolved_input, range_value, interval)
    except HTTPError as exc:
        if exc.code != 404 or "." in symbol:
            raise
        resolved_input = _resolve_symbol(symbol)
        chart = _fetch_chart(resolved_input, range_value, interval)
    meta = chart.get("meta") or {}
    quote = (((chart.get("indicators") or {}).get("quote") or [{}])[0])
    closes = [
        float(value)
        for value in quote.get("close") or []
        if value is not None and math.isfinite(float(value))
    ]
    if len(closes) < 2:
        raise ValueError(f"Insufficient live candles for {symbol}")
    first = closes[0]
    last = closes[-1]
    change_pct = ((last - first) / first) * 100 if first else 0.0
    signal = "LONG" if change_pct > 0.35 else "SHORT" if change_pct < -0.35 else "HOLD"
    confidence = min(0.95, 0.5 + abs(change_pct) / 20)
    return {
        "symbol": symbol,
        "resolved_symbol": meta.get("symbol") or resolved_input,
        "currency": meta.get("currency"),
        "exchange": meta.get("exchangeName"),
        "market_price": round(last, 6),
        "window_open": round(first, 6),
        "window_change_pct": round(change_pct, 4),
        "action": signal,
        "confidence": round(confidence, 4),
        "horizon": horizon,
        "candle_count": len(closes),
        "data_source": "Yahoo Finance chart API",
        "analysis_model": "transparent-window-momentum-v1",
    }


async def _analyze_symbol(symbol: str, horizon: str) -> dict[str, Any]:
    return await asyncio.to_thread(_analyze_chart, symbol, horizon)


@app.get("/tools/health")
def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "samruddhi-trade-bot-recovery",
        "contract": "trade-bot-tools-v1",
        "market_data_source": "Yahoo Finance chart API",
        "timestamp": _utc_now(),
    }


@app.post("/tools/predict")
async def predict(request: PredictRequest) -> dict[str, Any]:
    predictions = []
    for symbol in request.symbols:
        try:
            predictions.append(await _analyze_symbol(symbol, request.horizon))
        except Exception as exc:
            predictions.append({"symbol": symbol, "error": str(exc)})
    if all("error" in item for item in predictions):
        raise HTTPException(status_code=502, detail={"predictions": predictions})
    return {
        "status": "success",
        "predictions": predictions,
        "metadata": {
            "requested_symbols": request.symbols,
            "risk_profile": request.risk_profile,
            "stop_loss_pct": request.stop_loss_pct,
            "capital_risk_pct": request.capital_risk_pct,
            "drawdown_limit_pct": request.drawdown_limit_pct,
            "runtime": "samruddhi-trade-bot-recovery",
        },
        "timestamp": _utc_now(),
    }


@app.post("/tools/analyze")
async def analyze(request: AnalyzeRequest) -> dict[str, Any]:
    results = []
    for horizon in request.horizons:
        if horizon not in {"intraday", "short", "long"}:
            raise HTTPException(status_code=422, detail=f"Unsupported horizon: {horizon}")
        results.append(await _analyze_symbol(request.symbol, horizon))
    return {
        "status": "success",
        "analysis": results,
        "risk": {
            "stop_loss_pct": request.stop_loss_pct,
            "capital_risk_pct": request.capital_risk_pct,
            "drawdown_limit_pct": request.drawdown_limit_pct,
        },
        "timestamp": _utc_now(),
        "runtime": "samruddhi-trade-bot-recovery",
    }
