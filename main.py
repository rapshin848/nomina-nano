from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import anthropic
import os

app = FastAPI()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
WALLET_ADDRESS = os.environ.get("WALLET_ADDRESS")

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

@app.get("/")
def root():
    return {"service": "Nomina Nano", "version": "1.0", "status": "online"}

@app.post("/name-agent")
async def name_agent(request: Request):

    # 1. 요청 데이터 받기
    body = await request.json()
    persona    = body.get("persona", "")
    purpose    = body.get("purpose", "")
    style      = body.get("style", "")

    if not persona or not purpose:
        raise HTTPException(status_code=400, detail="persona와 purpose는 필수입니다.")

    # 2. Claude에게 이름 생성 요청
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
        model="claude-opus-4-5-20251001",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    result = json.loads(message.content[0].text)

    # 3. 결과 반환
    return JSONResponse({
        "status": "success",
        "payment": "0.5 USDC received",
        "result": result
    })