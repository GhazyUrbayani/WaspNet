# ChainRadar — API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.chainradar.xyz`

## Authentication
All authenticated endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Health

#### GET /health/live
Liveness probe — is the process running?

**Response:** `200 OK`
```json
{ "status": "alive", "service": "chainradar-api" }
```

#### GET /health/ready
Readiness probe — can the service handle requests?

**Response:** `200 OK`
```json
{
  "status": "ready",
  "checks": { "database": true, "redis": true, "sim_api": true }
}
```

---

### Authentication

#### POST /api/v1/auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "satoshi",
  "password": "securepassword123"
}
```

**Response:** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "refresh_token": "eyJhbGciOiJIUzI1NiI...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### POST /api/v1/auth/login
Authenticate and receive tokens.

#### POST /api/v1/auth/refresh
Exchange refresh token for new token pair.

#### GET /api/v1/auth/me
Get authenticated user profile. Requires Bearer token.

---

### Wallets

#### POST /api/v1/wallets
Add a wallet to the watchlist. 🔒 Auth required.

**Request Body:**
```json
{
  "address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
  "network": "solana",
  "label": "Phantom Whale #1"
}
```

#### GET /api/v1/wallets
List all wallets in watchlist. 🔒 Auth required.

#### GET /api/v1/wallets/{wallet_id}
Get specific wallet details. 🔒 Auth required.

#### PATCH /api/v1/wallets/{wallet_id}
Update wallet label or active status. 🔒 Auth required.

#### DELETE /api/v1/wallets/{wallet_id}
Remove wallet from watchlist. 🔒 Auth required.

---

### Alert Rules

#### POST /api/v1/alerts
Create an alert rule. 🔒 Auth required.

**Request Body:**
```json
{
  "name": "Large Transfer Alert",
  "wallet_id": "uuid-of-watched-wallet",
  "conditions": [
    {
      "condition_type": "large_transfer",
      "threshold": 500,
      "comparison": "gte"
    }
  ],
  "severity": "critical",
  "delivery_channels": ["telegram", "in_app"],
  "cooldown_minutes": 5
}
```

**Condition Types:**
| Type | Description | Threshold Unit |
|------|-------------|----------------|
| `balance_above` | Balance exceeds threshold | SOL |
| `balance_below` | Balance drops below threshold | SOL |
| `balance_change` | Balance changes by percentage | % |
| `large_transfer` | Transfer exceeds amount | SOL |
| `whale_movement` | Known whale address activity | SOL |
| `token_transfer` | Specific token moved | tokens |
| `new_token` | New token appears in wallet | N/A |
| `program_interaction` | Interaction with specific program | N/A |

#### GET /api/v1/alerts
List all alert rules. 🔒 Auth required.

#### PATCH /api/v1/alerts/{rule_id}
Toggle alert rule active/inactive. 🔒 Auth required.

#### DELETE /api/v1/alerts/{rule_id}
Delete alert rule. 🔒 Auth required.

---

### Webhooks

#### POST /api/v1/webhooks/sim
Receive Dune SIM webhook events. No auth — validated via signature header.

**Headers:**
- `X-Sim-Signature`: HMAC-SHA256 signature of the payload

**Payload:** (from Dune SIM)
```json
{
  "id": "evt_abc123",
  "type": "transfer",
  "address": "9WzDXwBbmkg...",
  "amount": 2500000000000,
  "timestamp": 1697000000
}
```

---

### SSE Stream

#### GET /api/v1/stream/events
Server-Sent Events stream for real-time notifications. 🔒 Auth required.

**Event Types:**
- `connected` — Initial connection confirmation
- `alert` — Alert rule triggered
- `notification` — Notification delivered
- `error` — Stream error

---

## Dune SIM API Usage

ChainRadar uses all 4 SIM endpoint types:

| SIM Endpoint | ChainRadar Usage | Cache TTL |
|-------------|------------------|-----------|
| `GET /v1/solana/balances/{address}` | Dashboard wallet balance | 30s |
| `GET /v1/solana/transactions/{address}` | Transaction feed | 5min |
| `GET /v1/evm/activity/{address}` | Cross-chain view | 5min |
| `POST /webhooks/subscribe` | Real-time alert trigger | N/A |
