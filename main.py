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
        "traits": "정밀과 수확의 기운. 날카롭고 흔들리지 않는 금속.",
        "en": "Metal — precision, harvest, sharp and unbreakable"
    },
    "水": {
        "keywords": ["cross-chain", "bridge", "relay", "flow", "route", "protocol", "network", "connect", "stream", "layer"],
        "traits": "지혜와 흐름의 기운. 모든 경계를 넘는 물.",
        "en": "Water — wisdom, flow, crossing all boundaries"
    },
}

ZODIAC_MAP = {
    (1,20,2,18):   {"sign":"Aquarius",   "kr":"물병자리",  "traits":"혁신적, 독립적, 미래지향적"},
    (2,19,3,20):   {"sign":"Pisces",     "kr":"물고기자리","traits":"직관적, 신비로운, 깊은 통찰"},
    (3,21,4,19):   {"sign":"Aries",      "kr":"양자리",    "traits":"선구자적, 과감한, 첫 번째"},
    (4,20,5,20):   {"sign":"Taurus",     "kr":"황소자리",  "traits":"불굴의 의지, 신뢰, 인내"},
    (5,21,6,20):   {"sign":"Gemini",     "kr":"쌍둥이자리","traits":"다재다능, 빠른 사고, 연결"},
    (6,21,7,22):   {"sign":"Cancer",     "kr":"게자리",    "traits":"보호, 직감, 깊은 기억"},
    (7,23,8,22):   {"sign":"Leo",        "kr":"사자자리",  "traits":"지배력, 카리스마, 권위"},
    (8,23,9,22):   {"sign":"Virgo",      "kr":"처녀자리",  "traits":"정밀함, 분석력, 완벽주의"},
    (9,23,10,22):  {"sign":"Libra",      "kr":"천칭자리",  "traits":"균형, 정의, 조화"},
    (10,23,11,21): {"sign":"Scorpio",    "kr":"전갈자리",  "traits":"변환, 깊이, 불굴"},
    (11,22,12,21): {"sign":"Sagittarius","kr":"사수자리",  "traits":"탐험, 자유, 무한한 시야"},
    (12,22,1,19):  {"sign":"Capricorn",  "kr":"염소자리",  "traits":"야망, 규율, 정상을 향한 의지"},
}

def get_zodiac(birth_str: str) -> dict:
    try:
        dt = datetime.strptime(birth_str, "%Y-%m-%d")
        m, d = dt.month, dt.day
        for (m1,d1,m2,d2), data in ZODIAC_MAP.items():
            if (m == m1 and d >= d1) or (m == m2 and d <= d2):
                return {**data, "birth": birth_str, "date": dt.strftime("%B %d, %Y")}
        return {"sign":"Capricorn","kr":"염소자리","traits":"야망, 규율, 정상을 향한 의지","birth":birth_str,"date":dt.strftime("%B %d, %Y")}
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
    yang_words = ["fast","attack","execute","trade","optimize","yield","offensive","expand","grow","marketing","viral"]
    yin_words  = ["protect","stable","analyze","research","monitor","guard","calm","deep","flow"]
    text = persona.lower()
    yang = sum(1 for w in yang_words if w in text)
    yin  = sum(1 for w in yin_words if w in text)
    if yang > yin: return "陽 (Yang) — 적극적, 외향적, 공격적 에너지"
    if yin > yang: return "陰 (Yin) — 수용적, 내향적, 깊은 에너지"
    return "陰陽 (Balance) — 균형잡힌 이중적 에너지"

# ── 세계관 프롬프트 ────────────────────────────────────────────────────────
WORLD_PROMPTS = {
    "cyberpunk": "Digital warrior, mercenary of the neon-lit blockchain. Names feel like codenames from a dystopian sci-fi thriller. Format: [FirstName LastName] · [Title]",
    "anime":     "Legendary anime protagonist with a destiny-laden name. Poetic, powerful, often kanji-inspired. Format: [漢字 Name] · [Legendary Title]",
    "kpop":      "Digital idol with a K-pop stage name. Sleek, modern, memorable. Format: [STAGE NAME] · [Concept]",
    "romance":   "Cold, mysterious romance novel lead. Brooding, elegant, unforgettable. Format: [Name] · [Aura Description]",
    "hero":      "Marvel/DC superhero codename. Bold, symbolic, iconic. Format: [HERO NAME] · [Power/Role]",
    "fantasy":   "Ancient archmage or mythological warrior of the chain. Timeless, mythological. Format: [Name] · [Ancient Title]",
    "minimal":   "Clean, punchy single English word. Bold and memorable. Format: [NAME] only.",
}

def build_prompt(persona, purpose, style, world, birth):
    wuxing  = get_wuxing(persona, purpose)
    yinyang = get_yinyang(persona)
    zodiac  = get_zodiac(birth) if birth else None

    destiny_block = f"""
=== DESTINY ANALYSIS ===
Five Elements (오행): {wuxing['element']} — {wuxing['en']}
  Traits: {wuxing['traits']}
Yin-Yang (음양): {yinyang}
"""
    if zodiac:
        destiny_block += f"Zodiac: {zodiac['sign']} ({zodiac['kr']}) — Born {zodiac['date']}\n  Traits: {zodiac['traits']}\n"

    return f"""You are a master naming oracle who fuses ancient Eastern philosophy with the digital age.
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
    "destiny": {{
        "element": "{wuxing['element']}",
        "element_en": "{wuxing['en']}",
        "yinyang": "{yinyang.split('—')[0].strip()}",
        "zodiac": "{zodiac['sign'] if zodiac else 'Unknown'}"
    }},
    "names": [
        {{"name": "...", "title": "...", "story": "...", "element_reason": "..."}},
        {{"name": "...", "title": "...", "story": "...", "element_reason": "..."}},
        {{"name": "...", "title": "...", "story": "...", "element_reason": "..."}}
    ]
}}""", wuxing, yinyang, zodiac

# ── 정적 파일 ──────────────────────────────────────────────────────────────
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

# ── x402 엔드포인트 (기존) ─────────────────────────────────────────────────
@app.post("/name-agent")
async def name_agent(body: dict):
    persona = body.get("persona", "")
    purpose = body.get("purpose", "")
    style   = body.get("style", "")
    world   = body.get("world", "cyberpunk")
    birth   = body.get("birth", "")

    if not persona or not purpose:
        return {"error": "persona and purpose are required."}
    if world not in WORLD_PROMPTS:
        world = "cyberpunk"

    prompt, wuxing, yinyang, zodiac = build_prompt(persona, purpose, style, world, birth)

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

# ── ACP 엔드포인트 (Virtuals ACP 전용) ────────────────────────────────────
@app.post("/name-agent-acp")
async def name_agent_acp(request: Request):
    """Virtuals ACP endpoint — payment handled by ACP escrow"""
    try:
        body = await request.json()
    except:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    persona = body.get("persona", "")
    purpose = body.get("purpose", "")
    style   = body.get("style", "")
    world   = body.get("world", "cyberpunk")
    birth   = body.get("birth", "")

    if not persona or not purpose:
        return JSONResponse({"error": "persona and purpose are required."}, status_code=400)
    if world not in WORLD_PROMPTS:
        world = "cyberpunk"

    prompt, wuxing, yinyang, zodiac = build_prompt(persona, purpose, style, world, birth)

    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    result = json.loads(message.content[0].text)

    return JSONResponse({
        "status": "success",
        "world": world,
        "analysis": {
            "element": wuxing["element"],
            "element_en": wuxing["en"],
            "yinyang": yinyang,
            "zodiac": zodiac["sign"] if zodiac else None
        },
        "result": result
    })
