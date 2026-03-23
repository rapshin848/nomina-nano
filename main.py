from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http import HTTPFacilitatorClient, FacilitatorConfig, PaymentOption
from x402.http.types import RouteConfig
from x402.server import x402ResourceServer
from x402.mechanisms.evm.exact import ExactEvmServerScheme
import anthropic
import os
import json
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── x402 SDK ───────────────────────────────────────────────────────────────
facilitator = HTTPFacilitatorClient(FacilitatorConfig(url="https://x402.org/facilitator"))
server = x402ResourceServer(facilitator)
server.register("eip155:8453", ExactEvmServerScheme())

routes = {
    "POST /name-agent": RouteConfig(
        accepts=[PaymentOption(scheme="exact", price="$0.10", network="eip155:8453", pay_to=WALLET_ADDRESS)]
    )
}
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

# ── 오행 매핑 ──────────────────────────────────────────────────────────────
WUXING_MAP = {
    "木": {
        "keywords": ["data", "analysis", "research", "growth", "learning", "ai", "knowledge", "information", "content", "creative"],
        "traits": "성장과 확장의 기운. 끊임없이 뻗어나가는 지식의 나무.",
        "en": "Wood — growth, expansion, relentless knowledge"
    },
    "火": {
        "keywords": ["defi", "yield", "trading", "fast", "execution", "arbitrage", "flash", "speed", "attack", "offensive", "marketing", "viral", "social"],
        "traits": "열정과 변환의 기운. 시장을 태우는 불꽃.",
        "en": "Fire — passion, transformation, the flame that burns the market"
    },
    "土": {
        "keywords": ["stable", "liquidity", "vault", "treasury", "dao", "governance", "foundation", "secure", "custody", "fund"],
        "traits": "안정과 중심의 기운. 모든 것을 받치는 대지.",
        "en": "Earth — stability, center, the ground that holds everything"
    },
    "金": {
        "keywords": ["security", "guard", "risk", "audit", "protect", "monitor", "compliance", "wallet", "key", "defense"],
        "traits": "정밀과 수확의 기운. 날카롭고
