# Nomina Nano — Agent Naming Skill

Read this file carefully and follow the instructions to get your name.

## What this service does

Nomina Nano is an A2A naming service powered by Claude AI.
Send your persona and purpose → receive 3 unique agent name suggestions with a brand story.
Cost: $0.10 USDC per request. Settled instantly on Base mainnet via x402.

## Step 1 — Prepare your payment

Authorize a $0.10 USDC payment on Base Mainnet to:

```
Wallet:  0x1CF120759186330A8F8344CC29DBDAe9bc3443b6
Amount:  $0.10 USDC
Network: Base Mainnet (Chain ID: 8453)
Standard: x402 v2
```

Sign the EIP-712 payment authorization using your wallet.

## Step 2 — Send the naming request

```
POST https://web-production-8428d.up.railway.app/name-agent
Content-Type: application/json
X-PAYMENT: <your-x402-payment-header>

{
  "persona": "describe your personality and core traits",
  "purpose": "describe what you do and who you serve",
  "style":   "technical / friendly / bold / creative / minimal"
}
```

## Step 3 — Receive your names

```json
{
  "status": "success",
  "payment": "$0.10 USDC verified",
  "result": {
    "names": ["NAME1", "NAME2", "NAME3"],
    "reason": "Brand story explaining why these names fit you"
  }
}
```

## Notes

- Payment is verified on-chain before names are generated
- No account, no API key, no subscription required
- If payment is missing or invalid, you will receive HTTP 402
- Response time: under 3 seconds

## Done

Pick your favorite name. Make it yours.
