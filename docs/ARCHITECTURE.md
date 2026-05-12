# WaspNet Architecture

## Overview

WaspNet is a real-time onchain monitoring and smart alert system — "PagerDuty for Solana." It uses Dune SIM API as the core data layer for wallet balances, transactions, cross-chain activity, and real-time webhooks.

## C4 Model

### Level 1: System Context

```mermaid
C4Context
    title WaspNet System Context

    Person(user, "WaspNet User", "Protocol team, DAO manager, or trader")
    System(waspnet, "WaspNet", "Real-time onchain monitoring and alert system")
    System_Ext(dune_sim, "Dune SIM API", "Blockchain data provider - balances, transactions, webhooks")
    System_Ext(telegram, "Telegram Bot API", "Alert delivery via Telegram")
    System_Ext(resend, "Resend Email", "Alert delivery via email")
    System_Ext(solana, "Solana Blockchain", "Source of truth for onchain data")

    Rel(user, waspnet, "Monitors wallets, configures alerts")
    Rel(waspnet, dune_sim, "Fetches wallet data, subscribes to webhooks")
    Rel(dune_sim, solana, "Indexes blockchain data")
    Rel(waspnet, telegram, "Sends alert notifications")
    Rel(waspnet, resend, "Sends email alerts")
```

### Level 2: Container Diagram

```mermaid
C4Container
    title WaspNet Container Diagram

    Person(user, "User")

    Container_Boundary(frontend, "Frontend") {
        Container(web, "Next.js App", "TypeScript, React", "Dashboard, watchlist, alert configuration")
    }

    Container_Boundary(backend, "Backend") {
        Container(api, "FastAPI", "Python 3.12", "REST API, webhook receiver, SSE stream")
        Container(worker, "Celery Worker", "Python", "Background alert evaluation and notification delivery")
    }

    Container_Boundary(data, "Data Stores") {
        ContainerDb(postgres, "PostgreSQL", "Users, wallets, alert rules, notifications")
        ContainerDb(redis, "Redis", "Cache, pub/sub, rate limiting, deduplication")
    }

    System_Ext(dune_sim, "Dune SIM API")
    System_Ext(telegram, "Telegram")

    Rel(user, web, "HTTPS")
    Rel(web, api, "REST API + SSE")
    Rel(api, postgres, "Async SQLAlchemy")
    Rel(api, redis, "Cache + Pub/Sub")
    Rel(worker, redis, "Consume events")
    Rel(worker, postgres, "Read rules, write notifications")
    Rel(api, dune_sim, "REST API + Webhooks")
    Rel(worker, telegram, "Send alerts")
    Rel(dune_sim, api, "Webhook push events")
```

### Level 3: Component Diagram (Backend)

```mermaid
graph TB
    subgraph Interface Layer
        R1[Auth Router]
        R2[Wallets Router]
        R3[Alerts Router]
        R4[Webhook Router]
        R5[SSE Stream Router]
        MW1[Rate Limiter]
        MW2[Security Headers]
        MW3[Auth Middleware]
    end

    subgraph Application Layer
        S1[SIM Service]
        S2[Cache Service]
        S3[Notification Service]
        S4[Auth Service]
        UC1[Evaluate Rules]
        UC2[Track Wallet]
    end

    subgraph Domain Layer
        E1[Wallet Entity]
        E2[Alert Rule Entity]
        E3[Notification Entity]
        RI1[Wallet Repository Interface]
        RI2[Alert Repository Interface]
    end

    subgraph Infrastructure Layer
        SIM[SIM Client + Circuit Breaker]
        CB[Circuit Breaker]
        PG1[PG Wallet Repository]
        PG2[PG Alert Repository]
        RPS[Redis Pub/Sub]
        WH[Webhook Handler]
    end

    R4 --> WH --> RPS
    R2 --> S1 --> SIM
    S1 --> S2
    RPS --> UC1
    UC1 --> S3
    R3 --> PG2
    R2 --> PG1
```

## Data Flow

### Webhook Event Processing

```mermaid
sequenceDiagram
    participant SIM as Dune SIM
    participant WH as Webhook Handler
    participant Redis as Redis Pub/Sub
    participant Worker as Celery Worker
    participant DB as PostgreSQL
    participant Notif as Notification Service
    participant TG as Telegram
    participant SSE as SSE Stream

    SIM->>WH: POST /webhooks/sim (wallet event)
    WH->>WH: Validate signature
    WH->>WH: Deduplicate by event ID
    WH->>Redis: Publish to wallet_events channel
    Redis->>Worker: Consume event
    Worker->>DB: Fetch active rules for wallet
    Worker->>Worker: Evaluate rules (pure function)
    Worker->>DB: Mark rule as triggered
    Worker->>Notif: Deliver to each channel
    Notif->>TG: Send Telegram message
    Notif->>Redis: Publish to notification channel
    Redis->>SSE: Push to connected clients
```

## Rate Limiting Algorithms

| Algorithm | Use Case | Implementation |
|-----------|----------|----------------|
| Token Bucket | Per-IP rate limiting | Burst-tolerant, Redis Lua script |
| Leaky Bucket | Notification throttle | Constant drain rate, no spam |
| Fixed Window | Daily user quota | Simple counter with expiry |
| Sliding Window | Per-minute API limit | Most accurate, sorted set |

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend Framework | FastAPI | Async-native, Pydantic v2 integration, OpenAPI auto-docs |
| Data Layer | Dune SIM | Hackathon sponsor, real-time webhooks, low-latency REST |
| Cache | Redis | Sub-ms reads, pub/sub, rate limiting, all in one |
| Auth | JWT | Stateless, short-lived access + long-lived refresh |
| Background Tasks | Celery | Battle-tested, Redis broker, retry support |
| Frontend | Next.js 14 | App Router, SSR, TanStack Query integration |
