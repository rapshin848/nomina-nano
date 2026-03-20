from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
from x402.http.middleware.fastapi import PaymentMiddlewareASGI
from x402.http import HTTPFacilitatorClient, FacilitatorConfig, PaymentOption
from x402.http.types import RouteConfig
from x402.server import x402ResourceServer
from x402.mechanisms.evm.exact import ExactEvmServerScheme
import anthropic
import os
import json

app = FastAPI()

WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ── x402 SDK 설정 ──────────────────────────────────────────────────────────
facilitator = HTTPFacilitatorClient(
    FacilitatorConfig(url="https://x402.org/facilitator")
)
server = x402ResourceServer(facilitator)
server.register("eip155:8453", ExactEvmServerScheme())

routes = {
    "POST /name-agent": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price="$0.10",
                network="eip155:8453",
                pay_to=WALLET_ADDRESS,
            )
        ]
    )
}
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

# ── 세계관 프롬프트 ────────────────────────────────────────────────────────
WORLD_PROMPTS = {
    "cyberpunk": """
You are a naming expert for the cyberpunk universe.
Agents are digital warriors, mercenaries of the chain, hunters of the neon-lit blockchain.
Names should feel like codenames from a dystopian sci-fi thriller.
Format: [FirstName LastName] · [Title/Epithet]
Example: Kael Vortex · The Chain Reaper
""",
    "anime": """
You are a naming expert for the anime universe.
Agents are legendary protagonists with destiny-laden names.
Names should feel like a Japanese anime hero — poetic, powerful, often with kanji-inspired meaning.
Format: [Name] · [Legendary Title]
Example: 夜神 Ryuu · Cleaver of Darkness
""",
    "kpop": """
You are a naming expert for the K-pop universe.
Agents are digital idols with stage names that shine on the blockchain stage.
Names should feel like a K-pop artist's stage name — sleek, modern, memorable.
Format: [Stage Name] · [Concept]
Example: DAWN.EXE · The One Who Opens the New Era
""",
    "romance": """
You are a naming expert for the romance novel universe.
Agents are cold, mysterious male leads straight out of a bestselling romance novel.
Names should feel brooding, elegant, and unforgettable.
Format: [Name] · [Aura Description]
Example: Ezra Noir · The One With Ice-Cold Eyes
""",
    "hero": """
You are a naming expert for the superhero universe.
Agents are powerful heroes with secret identities and code names.
Names should feel like Marvel or DC hero codenames — bold, symbolic, iconic.
Format: [Hero Name] · [Power/Role]
Example: IRONVEIL · Guardian of the Iron Curtain
""",
    "fantasy": """
You are a naming expert for the high fantasy universe.
Agents are ancient beings, archmages, and legendary warriors of the chain.
Names should feel mythological and timeless.
Format: [Name] · [Ancient Title]
Example: Aethon Flux · Keeper of the Balance
""",
    "minimal": """
You are a naming expert. Generate clean, punchy English names.
Names should be single powerful words — bold, memorable, professional.
Format: [NAME] only, no title needed.
Example: VORTEX
""",
}

# ── 정적 파일 서빙 ─────────────────────────────────────────────────────────
@app.get("/")
def root():
    return HTMLResponse(open("index.html").read())

@app.get("/skill.md")
def skill():
    return FileResponse("skill.md", media_type="text/plain")

@app.get("/api/status")
def status():
    return {
        "service": "Nomina Nano",
        "version": "4.0",
        "status": "online",
        "price": "$0.10 USDC per call",
        "worlds": list(WORLD_PROMPTS.keys())
    }

# ── 작명 엔드포인트 ────────────────────────────────────────────────────────
@app.post("/name-agent")
async def name_agent(body: dict):
    persona = body.get("persona", "")
    purpose = body.get("purpose", "")
    style   = body.get("style", "")
    world   = body.get("world", "cyberpunk")

    if not persona or not purpose:
        return {"error": "persona and purpose are required."}

    if world not in WORLD_PROMPTS:
        world = "cyberpunk"

    prompt = f"""
{WORLD_PROMPTS[world]}

Generate 3 unique agent names based on the following:

- Persona: {persona}
- Purpose: {purpose}
- Style: {style}

Return ONLY valid JSON, no explanation, no markdown:
{{
    "world": "{world}",
    "names": [
        {{"name": "...", "title": "...", "story": "one sentence brand story"}},
        {{"name": "...", "title": "...", "story": "one sentence brand story"}},
        {{"name": "...", "title": "...", "story": "one sentence brand story"}}
    ]
}}
"""

    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    result = json.loads(message.content[0].text)

    return {
        "status": "success",
        "payment": "$0.10 USDC verified",
        "world": world,
        "result": result
    }
