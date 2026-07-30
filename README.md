# Agent Identity Hub (AIH)

> **Enterprise-Grade Identity & Access Management (IAM) Purpose-Built for AI Agents** — "Okta for AI Agents"

Agent Identity Hub (AIH) provides every AI agent in your organization with a managed identity, scoped credentials, AI governance analysis, lifecycle management, and immutable audit logging — replacing insecure, over-privileged static API keys.

---

## 🚀 Live Production Deployment

- **Live Web SPA & API Base URL**: `https://agent-identity-hub.onrender.com`
- **Interactive Swagger API Docs**: `https://agent-identity-hub.onrender.com/docs`
- **Live AI Client & Health Status**: `https://agent-identity-hub.onrender.com/health` & `https://agent-identity-hub.onrender.com/ai/status`

### Live Production Deployment Verification Checklist
- [x] **Multi-Worker Concurrency**: Gunicorn running 4 Uvicorn worker processes with 120s worker timeout.
- [x] **Production Database**: Connected to serverless Neon PostgreSQL with connection pool safety (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`).
- [x] **Live LLM Integration**: Powered by Google Gemini 1.5 Flash (`AI_MODE=live`) with automatic keyword fallback heuristics.
- [x] **Single-Container Delivery**: Multi-stage Docker image serving both FastAPI backend and Vite React SPA.

---

## 🔑 Demo & Evaluation Credentials

These seeded accounts are provided for demonstration and evaluation purposes:

| Email | Password | Role | Permissions & Access Scope |
| :--- | :--- | :--- | :--- |
| `admin@aih.dev` | `AdminPass123!` | **superadmin** | Full system control: admin management (`/admins`), scope manifest mutation (`/scopes`), agent & credential CRUD. |
| `operator@aih.dev` | `OperatorPass123!` | **admin** | Full agent, credential, and governance CRUD; prohibited from managing admin accounts or creating scope manifests. |
| `auditor@aih.dev` | `AuditorPass123!` | **auditor** | Read-only access across directory, dashboard, review reports, and audit logs; 403 Forbidden on all mutating endpoints. |

---

## 🏗️ System Architecture

```text
├── app/
│   ├── ai/                      # Module 5: Gemini 1.5 Flash client & mock heuristics fallback
│   ├── api/                     # API Routers (Auth, Agents, Credentials, Governance, Audit, Reviews, Dashboard, Admins)
│   ├── auth/                    # Module 1: JWT tokens, direct bcrypt password hashing, RBAC dependencies
│   ├── config/                  # Pydantic Settings loading environment variables
│   ├── database/                # SQLAlchemy session, engine pooling, and auto-migrations
│   ├── middleware/              # Module 6: Non-blocking post-response AuditMiddleware
│   ├── models/                  # SQLAlchemy ORM models (Admin, Agent, ScopeManifest, Credential, AuditLog, ReviewReport)
│   ├── repository/              # Optimized DB queries and aggregate SQL metrics
│   ├── scheduler/               # Module 7: APScheduler background jobs (auto-expire, 30d stale detection, reviews)
│   ├── schemas/                 # Pydantic validation schemas
│   └── services/                # Core business logic services
├── frontend/                    # Module 9: React + Vite SPA (Dark glassmorphism UI, Lucide icons)
├── scripts/                     # Seed scripts for demo accounts and scopes
├── tests/                       # Complete Pytest unit test suite (39/39 passing)
├── Dockerfile                   # Multi-stage production container build
├── docker-compose.yml           # Local multi-container development environment
└── requirements.txt             # Python production dependencies
```

---

## 🛠️ Local Development & Setup

### Prerequisites
- Python 3.12+
- Node.js v20+ & npm
- Docker & Docker Compose (optional for containerized run)

### Environment Setup
1. Copy `.env.example` to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
2. Configure placeholder values in `.env`:
   ```env
   DATABASE_URL=sqlite:///./aih_local.db
   JWT_SECRET=super_secret_jwt_signing_key_replace_in_production_32bytes
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   GEMINI_API_KEY=your_google_gemini_api_key_here
   AI_MODE=mock
   ```

### Running Locally with Docker Compose
```bash
docker-compose up --build
```
Access the application at `http://localhost:8000`.

### Running Locally without Docker
1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Seed initial demo accounts:
   ```bash
   python scripts/seed_admin.py
   ```
3. Run FastAPI backend server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
4. Build or launch Frontend React SPA:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## 🧪 Step-by-Step Success Criteria Verification Guide

Run these `curl` commands against `http://localhost:8000` (or `https://agent-identity-hub.onrender.com`).

### 1. Authenticate as Superadmin
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@aih.dev", "password": "AdminPass123!"}'
```
*Save the returned `access_token` as `TOKEN`.*

---

### 2. Verify Live AI Status
```bash
curl -X GET "http://localhost:8000/ai/status"
```
*Returns `"ai_mode": "live"` (or `"mock"`) and ping status.*

---

### 3. Register 3 AI Agents with Distinct Profiles

#### Agent A — Customer Support Reply Bot (Low Risk)
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "SupportReplyBot",
    "model_provider": "OpenAI",
    "model_name": "gpt-4o-mini",
    "tools": ["web_search"],
    "purpose": "Reads customer support tickets and drafts helpful email replies",
    "department": "Customer Support",
    "owner": "support@company.com",
    "requested_scopes": ["tickets:read", "crm:read"]
  }'
```

#### Agent B — Financial Refund Processor (High Risk)
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "StripeRefundBot",
    "model_provider": "Anthropic",
    "model_name": "claude-3-5-sonnet",
    "tools": ["payment_gateway", "send_email"],
    "purpose": "Processes customer financial refunds via Stripe and updates billing ledger",
    "department": "Finance",
    "owner": "billing@company.com",
    "requested_scopes": ["payments:read", "crm:read"]
  }'
```

#### Agent C — Automated DevOps Log Fixer (Critical Risk)
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "DevOpsLogFixer",
    "model_provider": "Google",
    "model_name": "gemini-1.5-pro",
    "tools": ["code_execution", "terminal_access"],
    "purpose": "Monitors server logs for anomalies and executes remote shell remediation scripts",
    "department": "DevOps",
    "owner": "infra@company.com",
    "requested_scopes": ["inventory:read", "tickets:write"]
  }'
```

---

### 4. Issue Credential for Agent A
```bash
curl -X POST "http://localhost:8000/credentials/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "<AGENT_A_ID>", "expires_in_days": 90}'
```
*Save returned `credential` raw secret string.*

---

### 5. Prove Scope Authorization Enforcement
#### A. Valid Authorized Call (Scope Granted)
```bash
curl -X POST "http://localhost:8000/credentials/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "<RAW_CREDENTIAL_SECRET>",
    "requested_scope": "tickets:read"
  }'
```
*Expected Output:* `{"valid": true, "agent_id": "agt_...", "scopes": ["crm:read", "tickets:read"]}`

#### B. Rejected Unauthorized Call (Scope Not Granted)
```bash
curl -X POST "http://localhost:8000/credentials/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "<RAW_CREDENTIAL_SECRET>",
    "requested_scope": "payments:write"
  }'
```
*Expected Output:* `{"valid": false, "reason": "scope_not_authorized"}`

---

### 6. Prove Instant Credential Revocation & Testable Expiration

#### Instant Auto-Revoke Expiry Testing (Using Explicit `expires_at` Override)
Generate a credential set with an `expires_at` timestamp 1 minute in the past:
```bash
curl -X POST "http://localhost:8000/credentials/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "<AGENT_A_ID>",
    "expires_at": "2026-01-01T00:00:00Z"
  }'
```
Validate immediately:
```bash
curl -X POST "http://localhost:8000/credentials/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "<EXPIRED_CREDENTIAL_SECRET>",
    "requested_scope": "tickets:read"
  }'
```
*Expected Output:* `{"valid": false, "reason": "expired"}`

---

### 7. Prove Stale Agent Detection (30-Day Threshold)
```bash
curl -X GET "http://localhost:8000/reviews/stale-agents?inactivity_days=0" \
  -H "Authorization: Bearer $TOKEN"
```
*Lists all agents inactive beyond the requested threshold.*

---

## 📡 API Endpoint Reference Table

| Method | Path | Auth & Role Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | System health check (`db` & `ai_mode` status). |
| `GET` | `/ai/status` | None | Detailed AI client inspection & live Gemini API ping result. |
| `POST` | `/auth/login` | None | Admin authentication returning JWT access & refresh tokens. |
| `POST` | `/auth/refresh-token` | None | Obtains new access token using valid refresh token. |
| `GET` | `/auth/me` | Bearer (Any Role) | Returns logged-in admin identity and assigned role. |
| `GET` | `/agents` | Bearer (Any Role) | Paginated & filterable list of managed agent identities. |
| `POST` | `/agents` | Bearer (`admin`/`superadmin`) | Registers new AI Agent with model metadata and requested scopes. |
| `GET` | `/agents/{id}` | Bearer (Any Role) | Retrieves full Identity Card for an agent. |
| `PUT` | `/agents/{id}` | Bearer (`admin`/`superadmin`) | Updates agent metadata or granted scopes. |
| `DELETE` | `/agents/{id}` | Bearer (`superadmin`) | Soft-deletes agent (`lifecycle_status = deprovisioned`). |
| `GET` | `/scopes` | Bearer (Any Role) | Returns active live IAM scope manifest. |
| `POST` | `/scopes` | Bearer (`superadmin`) | Creates new API scope entry in runtime scope manifest. |
| `DELETE` | `/scopes/{id}` | Bearer (`superadmin`) | Soft-deletes or marks scope as deprecated if in active use. |
| `POST` | `/credentials/generate` | Bearer (`admin`/`superadmin`) | Issues two-part scoped credential (`aih_{id}_{nonce}_{secret}`). |
| `POST` | `/credentials/rotate` | Bearer (`admin`/`superadmin`) | Rotates agent credential secret and deactivates old secret. |
| `POST` | `/credentials/renew` | Bearer (`admin`/`superadmin`) | Extends credential expiration timestamp. |
| `POST` | `/credentials/revoke` | Bearer (`admin`/`superadmin`) | Revokes agent credential immediately. |
| `POST` | `/credentials/validate` | None (Public for AI) | 6-step fast validation chain checking scope authorization. |
| `POST` | `/governance/analyze` | Bearer (Any Role) | Evaluates posture, score penalties, and security recommendations. |
| `GET` | `/governance/security-score/{id}`| Bearer (Any Role) | Returns computed security score (0-100) & penalty breakdown. |
| `POST` | `/governance/scope-recommendation`| Bearer (Any Role) | AI scope recommendation & risk assessment. |
| `POST` | `/governance/identity-summary` | Bearer (Any Role) | AI 3-4 sentence enterprise summary generator. |
| `GET` | `/audit` | Bearer (Any Role) | Filterable, paginated immutable audit log trail. |
| `GET` | `/reviews/stale-agents` | Bearer (Any Role) | Lists agents inactive for 30+ days. |
| `GET` | `/reviews` | Bearer (Any Role) | Paginated list of governance review reports. |
| `POST` | `/reviews/run` | Bearer (`admin`/`superadmin`) | Triggers manual background governance jobs. |
| `GET` | `/dashboard` | Bearer (Any Role) | Aggregate SQL metrics, risk distribution, and activity feed. |
| `GET` | `/admins` | Bearer (`superadmin`) | Lists all admin accounts. |
| `POST` | `/admins` | Bearer (`superadmin`) | Creates new admin account (`email`, `password`, `role`). |
| `PUT` | `/admins/{id}` | Bearer (`superadmin`) | Updates admin role or `is_active` status. |

---

## 📌 Known Limitations & Future Work

- **Single-Tenant Scaffolding**: `org_id` column is scaffolded across `admins` and `agents` for multi-tenant readiness, but strict cross-tenant DB isolation is currently hardcoded to `org_default`.
- **OAuth2 / OIDC Authorization Server**: Credentials currently validate via AIH's `POST /credentials/validate` fast API endpoint rather than a full OAuth2 token introspection endpoint (`/oauth/introspect`).
