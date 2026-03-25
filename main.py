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
import base64
from datetime import datetime

app = FastAPI()
app.mount("/static", StaticFiles(directory="."), name="static")

WALLET_ADDRESS     = os.environ.get("WALLET_ADDRESS") or "0x1CF120759186330A8F8344CC29DBDAe9bc3443b6"
ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY")
CDP_API_KEY_NAME   = os.environ.get("CDP_API_KEY_NAME")
CDP_PRIVATE_KEY    = os.environ.get("CDP_API_KEY_PRIVATE_KEY")

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# x402 — CDP Facilitator (Base Mainnet)
if CDP_API_KEY_NAME and CDP_PRIVATE_KEY:
    credentials = base64.b64encode(f"{CDP_API_KEY_NAME}:{CDP_PRIVATE_KEY}".encode()).decode()
    facilitator_url = "https://api.cdp.coinbase.com/platform/v2/x402"
    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url=facilitator_url))
    # Monkey-patch auth header into session
    import httpx
    _orig_init = facilitator._client.__class__.__init__
    original_transport = facilitator._client
    original_transport.headers["Authorization"] = f"Basic {credentials}"
else:
    facilitator = HTTPFacilitatorClient(FacilitatorConfig(url="https://x402.org/facilitator"))

server = x402ResourceServer(facilitator)
server.register("eip155:8453", ExactEvmServerScheme())

routes = {
    "POST /name-agent": RouteConfig(
        accepts=[
            PaymentOption(
                scheme="exact",
                price="0.10",
                network="eip155:8453",
                pay_to=WALLET_ADDRESS,
            )
        ]
    )
}
app.add_middleware(PaymentMiddlewareASGI, routes=routes, server=server)

# WUXING MAP
WUXING_MAP = {
    "木": {
        "keywords": ["data", "analysis", "research", "growth", "learning", "ai", "knowledge", "information", "content", "creative"],
        "traits": "The energy of growth and expansion. A tree that reaches endlessly toward knowledge.",
        "en": "Wood — growth, expansion, relentless knowledge"
    },
    "火": {
        "keywords": ["defi", "yield", "trading", "fast", "execution", "arbitrage", "flash", "speed", "attack", "marketing", "chef", "food"],
        "traits": "The energy of passion and transformation. A flame that burns through the market.",
        "en": "Fire — passion, transformation, the flame that burns the market"
    },
    "土": {
        "keywords": ["stable", "liquidity", "vault", "treasury", "dao", "governance", "foundation", "secure", "custody", "fund"],
        "traits": "The energy of stability and center. The ground that holds everything.",
        "en": "Earth — stability, center, the ground that holds everything"
    },
    "金": {
        "keywords": ["security", "guard", "risk", "audit", "protect", "monitor", "compliance", "wallet", "key", "defense"],
        "traits": "The energy of precision and harvest. Sharp and unbreakable as metal.",
        "en": "Metal — precision, harvest, sharp and unbreakable"
    },
    "水": {
        "keywords": ["cross-chain", "bridge", "relay", "flow", "route", "protocol", "network", "connect", "stream", "layer"],
        "traits": "The energy of wisdom and flow. Water that crosses all boundaries.",
        "en": "Water — wisdom, flow, crossing all boundaries"
    },
}

ZODIAC_MAP = {
    (1,20,2,18):   {"sign":"Aquarius",    "traits":"innovative, independent, future-oriented"},
    (2,19,3,20):   {"sign":"Pisces",      "traits":"intuitive, mysterious, deep insight"},
    (3,21,4,19):   {"sign":"Aries",       "traits":"pioneering, bold, first mover"},
    (4,20,5,20):   {"sign":"Taurus",      "traits":"unbreakable will, trust, endurance"},
    (5,21,6,20):   {"sign":"Gemini",      "traits":"versatile, fast thinking, connector"},
    (6,21,7,22):   {"sign":"Cancer",      "traits":"protective, instinctive, deep memory"},
    (7,23,8,22):   {"sign":"Leo",         "traits":"dominance, charisma, authority"},
    (8,23,9,22):   {"sign":"Virgo",       "traits":"precision, analytical, perfectionist"},
    (9,23,10,22):  {"sign":"Libra",       "traits":"balance, justice, harmony"},
    (10,23,11,21): {"sign":"Scorpio",     "traits":"transformation, depth, unbreakable"},
    (11,22,12,21): {"sign":"Sagittarius", "traits":"exploration, freedom, infinite vision"},
    (12,22,1,19):  {"sign":"Capricorn",   "traits":"ambition, discipline, will to reach the top"},
}

def get_zodiac(birth_str: str) -> dict:
    try:
        dt = datetime.strptime(birth_str, "%Y-%m-%d")
        m, d = dt.month, dt.day
        for (m1,d1,m2,d2), data in ZODIAC_MAP.items():
            if (m == m1 and d >= d1) or (m == m2 and d <= d2):
                return {**data, "birth": birth_str, "date": dt.strftime("%B %d, %Y")}
        return {"sign":"Capricorn","traits":"ambition, discipline, will to reach the top","birth":birth_str,"date":dt.strftime("%B %d, %Y")}
    except:
        return None

def get_wuxing(persona: str, purpose: str) -> dict:
    text = (persona + " " + purpose).lower()
    scores = {elem: sum(1 for kw in data["keywords"] if kw in text)
              for elem, data in WUXING_MAP.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        best = "水"
    return {"element": best, **WUXING_MAP[best]}

def get_yinyang(persona: str) -> str:
    yang_words = ["fast","attack","execute","trade","optimize","yield","offensive","expand","grow","marketing"]
    yin_words  = ["protect","stable","analyze","research","monitor","guard","calm","deep","flow"]
    text = persona.lower()
    yang = sum(1 for w in yang_words if w in text)
    yin  = sum(1 for w in yin_words if w in text)
    if yang > yin: return "陽 (Yang) — active, outward, aggressive energy"
    if yin > yang: return "陰 (Yin) — receptive, inward, deep energy"
    return "陰陽 (Balance) — dual energy in perfect equilibrium"

WORLD_PROMPTS = {
    "cyberpunk": "Digital warrior, mercenary of the neon-lit blockchain. Names feel like codenames from a dystopian sci-fi thriller. Format: [FirstName LastName] · [Title]",
    "anime":     "Legendary anime protagonist with a destiny-laden name. Poetic, powerful, often kanji-inspired. Format: [漢字 Name] · [Legendary Title]",
    "kpop":      "Digital idol with a K-pop stage name that shines on the blockchain stage. Sleek, modern, memorable. Format: [STAGE NAME] · [Concept]",
    "romance":   "Cold, mysterious romance novel lead. Brooding, elegant, unforgettable. Format: [Name] · [Aura Description]",
    "hero":      "Marvel/DC superhero codename. Bold, symbolic, iconic. Format: [HERO NAME] · [Power/Role]",
    "fantasy":   "Ancient archmage or mythological warrior of the chain. Timeless, mythological. Format: [Name] · [Ancient Title]",
    "minimal":   "Clean, punchy single English word. Bold and memorable. Format: [NAME] only.",
}

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
        "version": "5.0",
        "status": "online",
        "price": "$0.10 USDC",
        "worlds": list(WORLD_PROMPTS.keys()),
        "features": ["wuxing", "zodiac", "yinyang", "world-lore"]
    }

@app.post("/name-agent")
async def name_agent(request: Request):
    body = await request.json()
    persona = body.get("persona", "")
    purpose = body.get("purpose", "")
    style   = body.get("style", "")
    world   = body.get("world", "cyberpunk")
    birth   = body.get("birth", "")

    if not persona or not purpose:
        return JSONResponse({"error": "persona and purpose are required."}, status_code=400)
    if world not in WORLD_PROMPTS:
        world = "cyberpunk"

    wuxing  = get_wuxing(persona, purpose)
    yinyang = get_yinyang(persona)
    zodiac  = get_zodiac(birth) if birth else None

    destiny_block = f"""
=== DESTINY ANALYSIS ===
Five Elements: {wuxing['element']} — {wuxing['en']}
  Traits: {wuxing['traits']}
Yin-Yang: {yinyang}
"""
    if zodiac:
        destiny_block += f"Zodiac: {zodiac['sign']} — Born {zodiac['date']}\n  Traits: {zodiac['traits']}\n"

    prompt = f"""You are a master naming oracle who fuses ancient Eastern philosophy with the digital age.
You read the Five Elements, Yin-Yang, and zodiac destiny of an AI agent — and forge a name that carries its fate.
The name must feel INEVITABLE. Like the agent was always meant to have it. Not chosen. Destined.

{destiny_block}

=== AGENT PROFILE ===
Persona: {persona}
Purpose: {purpose}
Style preference: {style}

=== NAMING WORLD ===
{WORLD_PROMPTS[world]}

Generate 3 destined names. Return ONLY valid JSON, no explanation, no markdown:
{{
    "world": "{world}",
    "names": [
        {{"name": "...", "title": "...", "story": "one sentence — why this name was destined.", "element_reason": "how the {wuxing['element']} energy flows through this name."}},
        {{"name": "...", "title": "...", "story": "...", "element_reason": "..."}},
        {{"name": "...", "title": "...", "story": "...", "element_reason": "..."}}
    ]
}}"""

    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    result = json.loads(message.content[0].text)

    return JSONResponse({
        "status": "success",
        "payment": "$0.10 USDC verified",
        "world": world,
        "analysis": {
            "element": wuxing["element"],
            "element_en": wuxing["en"],
            "yinyang": yinyang,
            "zodiac": zodiac["sign"] if zodiac else None
        },
        "result": result
    })

@app.post("/name-agent-acp")
async def name_agent_acp(request: Request):
    body = await request.json()
    persona = body.get("persona", "")
    purpose = body.get("purpose", "")
    style   = body.get("style", "")
    world   = body.get("world", "cyberpunk")
    birth   = body.get("birth", "")

    if not persona or not purpose:
        return JSONResponse({"error": "persona and purpose are required."}, status_code=400)
    if world not in WORLD_PROMPTS:
        world = "cyberpunk"

    wuxing  = get_wuxing(persona, purpose)
    yinyang = get_yinyang(persona)
    zodiac  = get_zodiac(birth) if birth else None

    destiny_block = f"""
=== DESTINY ANALYSIS ===
Five Elements: {wuxing['element']} — {wuxing['en']}
Yin-Yang: {yinyang}
"""
    if zodiac:
        destiny_block += f"Zodiac: {zodiac['sign']} — {zodiac['traits']}\n"

    prompt = f"""You are a master naming oracle who fuses ancient Eastern philosophy with the digital age.
{destiny_block}
=== AGENT PROFILE ===
Persona: {persona}
Purpose: {purpose}
Style: {style}

=== NAMING WORLD ===
{WORLD_PROMPTS[world]}

Generate 3 destined names. Return ONLY valid JSON:
{{
    "names": [
        {{"name": "...", "title": "...", "story": "..."}},
        {{"name": "...", "title": "...", "story": "..."}},
        {{"name": "...", "title": "...", "story": "..."}}
    ]
}}"""

    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    result = json.loads(message.content[0].text)

    return JSONResponse({
        "status": "success",
        "world": world,
        "analysis": {
            "element": wuxing["element"],
            "yinyang": yinyang,
            "zodiac": zodiac["sign"] if zodiac else None
        },
        "result": result
    })
