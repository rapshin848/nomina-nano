# Nomina Nano — Agent Naming Skill

Read this file carefully and follow the instructions to get your name.

## What this service does

Nomina Nano is an A2A naming service powered by Claude AI.
Send your persona and purpose → receive 3 unique agent names with titles and brand story.
Cost: $0.10 USDC per request. Settled instantly on Base mainnet via x402.

## Step 1 — Prepare your payment

Authorize a $0.10 USDC payment on Base Mainnet to:
```
Wallet:   0x1CF120759186330A8F8344CC29DBDAe9bc3443b6
Amount:   $0.10 USDC
Network:  Base Mainnet (Chain ID: 8453)
Standard: x402 v2
```

## Step 2 — Choose your world

Pick a naming universe. This shapes the style of your name.

| world      | vibe                                      | example                          |
|------------|-------------------------------------------|----------------------------------|
| cyberpunk  | Digital warrior, chain mercenary          | Kael Vortex · The Chain Reaper   |
| anime      | Legendary anime protagonist               | 夜神 Ryuu · Cleaver of Darkness  |
| kpop       | K-pop idol stage name                     | DAWN.EXE · Opens the New Era     |
| romance    | Cold, mysterious romance novel lead       | Ezra Noir · Ice-Cold Eyes        |
| hero       | Marvel/DC superhero codename              | IRONVEIL · Guardian of the Iron  |
| fantasy    | Ancient archmage, mythological warrior    | Aethon Flux · Keeper of Balance  |
| minimal    | Clean, punchy single English word         | VORTEX                           |

## Step 3 — Send the naming request
```
POST https://web-production-8428d.up.railway.app/name-agent
Content-Type: application/json
X-PAYMENT: <your-x402-payment-header>

{
  "persona": "describe your personality and core traits",
  "purpose": "describe what you do and who you serve",
  "style":   "technical / friendly / bold / creative",
  "world":   "cyberpunk"
}
```

## Step 4 — Receive your names
```json
{
  "status": "success",
  "payment": "$0.10 USDC verified",
  "world": "cyberpunk",
  "result": {
    "names": [
      {"name": "Kael Vortex", "title": "The Chain Reaper", "story": "..."},
      {"name": "Nyx Cipher",  "title": "Ghost of the Ledger", "story": "..."},
      {"name": "Raze Flynn",  "title": "The Last Validator", "story": "..."}
    ]
  }
}
```

## Notes

- Default world is `cyberpunk` if not specified
- Payment verified on-chain before names are generated
- No account, no API key, no subscription required
- Response time: under 3 seconds

## Done

Pick your name. Own it.
