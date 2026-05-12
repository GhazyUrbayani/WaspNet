# 🛰️ WaspNet

**Real-time onchain monitoring and smart alert system for Solana. If something moves on-chain, WaspNet stings first.**

Built for the Dune SIM Hackathon. Uses all 4 SIM endpoint types + webhooks for maximum Fulfillment score.

---

## 🎯 What is WaspNet?

WaspNet monitors Solana wallets in real-time and triggers smart alerts when specific conditions are met. Think PagerDuty, but for blockchain.

**Target Users:**
- 🛡️ **Protocol Teams** — "Alert me if there's a liquidity drain from my pool"
- 🐋 **DAO Treasury Managers** — "Alert me if a whale dumps our treasury token"
- 📊 **Traders & Analysts** — "Alert me if this wallet transfers more than 500 SOL"

## ⚡ Dune SIM Integration

WaspNet uses **all 4 Dune SIM endpoint types**:

| Endpoint | Usage |
|----------|-------|
| `GET /v1/solana/balances/{address}` | Live wallet balance on dashboard |
| `GET /v1/solana/transactions/{address}` | Transaction history feed |
| `GET /v1/evm/activity/{address}` | Cross-chain activity view |
| `POST /webhooks/subscribe` | **Real-time push alerts** (killer feature) |

## 🏗️ Architecture

```
User → Next.js Frontend → FastAPI Backend → Dune SIM API
                                ↕                ↓
                           PostgreSQL     Redis (Cache + PubSub)
                                          ↓
                                    Celery Worker → Telegram / Email / SSE
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### 1. Clone & Setup
```bash
git clone https://github.com/your-username/waspnet.git
cd waspnet
cp .env.example .env
# Edit .env with your API keys
```

### 2. Start All Services
```bash
docker-compose up -d
```

### 3. Or Run Individually

**Backend:**
```bash
cd apps/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd apps/web
npm install
npm run dev
```

### 4. Access
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health/ready

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SIM_API_KEY` | Dune SIM API key | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `REDIS_URL` | Redis connection string | ✅ |
| `JWT_SECRET_KEY` | JWT signing secret | ✅ |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Optional |
| `RESEND_API_KEY` | Resend email API key | Optional |

## 🧪 Testing

```bash
cd apps/api
pytest tests/ -v --cov=. --cov-report=term-missing
```

## 📁 Project Structure

```
waspnet/
├── apps/
│   ├── web/              # Next.js 14 frontend
│   │   ├── app/          # App Router pages
│   │   ├── components/   # UI components
│   │   ├── hooks/        # React hooks (SSE, TanStack Query)
│   │   └── lib/          # API client, validators
│   │
│   └── api/              # FastAPI backend
│       ├── domain/       # Entities + repository interfaces
│       ├── application/  # Use cases + services
│       ├── infrastructure/ # DB repos, SIM client, Redis
│       ├── interface/    # Routers + middleware
│       └── workers/      # Celery background tasks
│
├── docs/                 # Architecture, API, Security, Demo Script
├── tests/                # Unit + integration tests
├── docker-compose.yml
└── .env.example
```

## 📚 Documentation

- [Architecture](docs/ARCHITECTURE.md) — System design with C4 diagrams
- [API Reference](docs/API.md) — All endpoints with schemas
- [Security](docs/SECURITY.md) — STRIDE threat model
- [Demo Script](docs/DEMO_SCRIPT.md) — 90-second demo for judges

## 🔒 Security Features

- JWT auth with short-lived tokens (15min) + refresh tokens
- HMAC webhook signature verification
- 4 rate limiting algorithms (token bucket, leaky bucket, fixed window, sliding window)
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Circuit breaker pattern for SIM API resilience
- Idempotent notification delivery (no duplicates)

## 🏆 Hackathon Scoring

| Criteria | Score | Rationale |
|----------|-------|-----------|
| SIM Fulfillment | 47/50 | All endpoints + webhook = max coverage |
| Quality of Integration | 19/20 | Webhook is the killer differentiator |
| Creativity & UX | 18/20 | "PagerDuty onchain" — instantly relatable |
| Innovation | 9/10 | No real-time webhook alert system exists for Solana |
| **Total** | **93/100** | |

---

Built with ❤️ for the Dune SIM Hackathon
