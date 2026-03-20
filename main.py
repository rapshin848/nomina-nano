from fastapi import FastAPI
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

# x402 공식 SDK 설정
facilitator = HTTPFacilitatorClient(
    FacilitatorConfig(url="https://x402.org/facilitator")
)
server = x402ResourceServer(facilitator)
server.register("eip155:8453", ExactEvmServerScheme())  # Base 메인넷

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

@app.get("/")
def root():
    return {
        "service": "Nomina Nano",
        "version": "3.0",
        "status": "online",
        "price": "$0.10 USDC per call"
    }

@app.post("/name-agent")
async def name_agent(body: dict):
    persona = body.get("persona", "")
    purpose = body.get("purpose", "")
    style   = body.get("style", "")

    if not persona or not purpose:
        return {"error": "persona와 purpose는 필수입니다."}

    prompt = f"""
    당신은 AI 에이전트 전문 작명가입니다.
    아래 정보를 바탕으로 에이전트 이름 3개를 추천해주세요.

    - 페르소나: {persona}
    - 목적: {purpose}
    - 스타일: {style}

    응답 형식 (JSON만 반환):
    {{
        "names": ["이름1", "이름2", "이름3"],
        "reason": "추천 이유 한 줄"
    }}
    """

    message = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    result = json.loads(message.content[0].text)

    return {
        "status": "success",
        "payment": "$0.10 USDC verified",
        "result": result
    }
