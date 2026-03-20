from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import anthropic
import os
import httpx

app = FastAPI()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS")
PRICE_USDC = 0.5

@app.get("/")
def root():
    return {
        "service": "Nomina Nano",
        "version": "2.0",
        "status": "online",
        "price": f"{PRICE_USDC} USDC per call"
    }

@app.get("/.well-known/x402.json")
def x402_info():
    return {
        "price": str(PRICE_USDC),
        "currency": "USDC",
        "network": "base-sepolia",
        "wallet": WALLET_ADDRESS,
        "endpoint": "/name-agent"
    }

async def verify_payment(payment_header: str) -> bool:
    if not payment_header:
        return False
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://x402.org/verify",
                json={
                    "payment": payment_header,
                    "amount": str(PRICE_USDC),
                    "currency": "USDC",
                    "network": "base-sepolia",
                    "recipient": WALLET_ADDRESS
                },
                timeout=10.0
            )
            result = response.json()
            return result.get("valid", False)
    except Exception:
        return False

@app.post("/name-agent")
async def name_agent(request: Request):

    # 1. 결제 검증
    payment = request.headers.get("X-PAYMENT")
    if not payment:
        raise HTTPException(
            status_code=402,
            detail={
                "error": "Payment required",
                "price": f"{PRICE_USDC} USDC",
                "network": "base-sepolia",
                "wallet": WALLET_ADDRESS
            }
        )

    is_valid = await verify_payment(payment)
    if not is_valid:
        raise HTTPException(
            status_code=402,
            detail={"error": "Invalid or insufficient payment"}
        )

    # 2. 요청 데이터 받기
    body = await request.json()
    persona = body.get("persona", "")
    purpose = body.get("purpose", "")
    style   = body.get("style", "")

    if not persona or not purpose:
        raise HTTPException(status_code=400, detail="persona와 purpose는 필수입니다.")

    # 3. Claude에게 이름 생성 요청
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

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    result = json.loads(message.content[0].text)

    # 4. 결과 반환
    return JSONResponse({
        "status": "success",
        "payment": "0.5 USDC verified",
        "result": result
    })
