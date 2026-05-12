# WaspNet — Implementation Plan

## Overview
Real-time onchain monitoring and smart alert system for Solana. If something moves on-chain, WaspNet stings first.

## Phase Tracking

### Phase 1 — Foundation
- [ ] docker-compose.yml (PostgreSQL + Redis + FastAPI + Next.js)
- [ ] .env.example
- [ ] FastAPI main.py + health endpoints
- [ ] SQLAlchemy models + Alembic migration
- [ ] JWT auth (register, login, refresh)

### Phase 2 — Dune SIM Integration (CORE)
- [ ] sim_client.py — async httpx, circuit breaker, retry
- [ ] cache_service.py — Redis cache wrapper
- [ ] webhook_handler.py — SIM push receiver
- [ ] sim_service.py — orchestrator

### Phase 3 — Alert Engine
- [ ] alert_rule.py entity + conditions
- [ ] evaluate_rules.py use case (TDD)
- [ ] alert_worker.py Celery task
- [ ] notification_service.py (Telegram + Email + SSE)

### Phase 4 — Rate Limiting & Security
- [ ] rate_limiter.py (4 algorithms)
- [ ] security_headers.py
- [ ] Input validation (Pydantic v2)

### Phase 5 — Frontend
- [ ] Next.js 14 project setup
- [ ] sim-client.ts typed wrapper
- [ ] Dashboard page (watchlist, live data)
- [ ] Alert rule form + history
- [ ] SSE integration

### Phase 6 — Tests & Docs
- [ ] Unit tests (rule engine, rate limiter, SIM client)
- [ ] Integration tests (webhook flow, alert delivery)
- [ ] ARCHITECTURE.md, API.md, SECURITY.md, DEMO_SCRIPT.md
- [ ] README.md

## Current Status: Starting Phase 1