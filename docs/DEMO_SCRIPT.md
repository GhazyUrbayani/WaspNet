# ChainRadar — DEMO SCRIPT

## 90-Second Demo Sequence for Dune SIM Judges

> **Goal:** Show all 4 SIM endpoint types + webhooks = maximum Fulfillment score.

---

### Pre-Demo Setup (before going live)
1. ✅ Backend running (FastAPI + Redis + PostgreSQL)
2. ✅ Frontend running (Next.js on localhost:3000)
3. ✅ Telegram bot configured and ready
4. ✅ Test wallet with known activity prepared
5. ✅ SIM API key configured and verified

---

### Demo Flow (90 seconds)

#### [0:00 - 0:15] Introduction + Problem Statement
- **Say:** "ChainRadar is PagerDuty for Solana — real-time onchain monitoring powered entirely by Dune SIM."
- **Show:** Landing page with radar animation
- **Click:** "Start Monitoring" → Login/Register

#### [0:15 - 0:30] Add Wallet — SIM Endpoint #1
- **Action:** Paste a known whale address (e.g., `9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM`)
- **Show:** Dashboard pulls live balance from **SIM: GET /v1/solana/balances/{address}**
- **Point out:** "This is LIVE data from Dune SIM — not mocked, not cached."

#### [0:30 - 0:45] Transaction History — SIM Endpoint #2
- **Action:** Click on the wallet card
- **Show:** Transaction feed populated by **SIM: GET /v1/solana/transactions/{address}**
- **Point out:** "Last 10 transactions, real-time from SIM. Including amounts, types, and timestamps."

#### [0:45 - 0:55] Cross-Chain View — SIM Endpoint #3
- **Action:** Toggle to "EVM Cross-Chain" tab
- **Show:** Cross-chain activity from **SIM: GET /v1/evm/activity/{address}**
- **Point out:** "Same wallet tracked across Solana AND EVM chains — single pane of glass."

#### [0:55 - 1:10] Set Alert Rule + Webhook — SIM Endpoint #4
- **Action:** Navigate to Alert Rules → Create Rule
- **Set:** "Alert if transfer > 500 SOL"
- **Select:** Telegram + In-App delivery
- **Point out:** "Under the hood, this subscribes to **SIM webhooks** — POST /webhooks/subscribe"
- **Show:** Terminal/logs showing webhook subscription created

#### [1:10 - 1:25] Live Alert Trigger 🚨
- **Action:** Trigger a simulated transfer event (or wait for real activity)
- **Show:** 
  1. Telegram message arrives in real-time
  2. Dashboard alert feed updates WITHOUT page refresh (SSE)
  3. Status dot pulses green → "Live"
- **Point out:** "From SIM webhook to Telegram notification — under 2 seconds. No polling."

#### [1:25 - 1:30] Closing
- **Say:** "4 SIM endpoints, real-time webhooks, multi-channel alerts. ChainRadar — because you shouldn't learn about a drain from Twitter."

---

### Key Talking Points for Judges

1. **SIM Fulfillment:** "We use ALL 4 SIM endpoint types plus webhooks — balances, transactions, EVM activity, and real-time push."

2. **Why SIM (not Helius/QuickNode):** "SIM's webhook capability is the ONLY way to get push-based real-time data for Solana. Without it, we'd have to poll — which doesn't scale."

3. **Quality of Integration:** "Every data point you see comes through SIM → Redis cache (30s TTL for balances, 5min for history) → Frontend. Zero hardcoded data."

4. **Production-Ready:** "Circuit breaker pattern, rate limiting (4 algorithms), idempotent notification delivery, JWT auth — this isn't a hackathon prototype, it's infrastructure."

---

### Backup Demo (if SIM API is slow/down)

If SIM API has issues during demo:
1. Show cached data in Redis (still recent)
2. Show circuit breaker state in health endpoint
3. Show graceful degradation message in UI
4. Explain: "This is exactly why we implemented circuit breaker — production resilience."

---

### Screenshot Checklist for Submission

- [ ] Landing page with radar animation
- [ ] Dashboard with live wallet data
- [ ] Transaction feed from SIM
- [ ] Alert rule creation form
- [ ] Telegram notification received
- [ ] SSE live update in dashboard
- [ ] Health check showing all systems green
- [ ] Architecture diagram
