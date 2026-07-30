# Agent Identity Hub (AIH)

> **Enterprise-Grade Machine Identity & Access Governance Purpose-Built for AI Agents** — *"Okta for AI Agents"*

Human employees get identity records, role-based scope limits, lifecycle management, credential rotation, and quarterly access reviews. AI agents historically just get a static, over-privileged API key pasted into an environment variable — with zero scope enforcement, no expiry, and no usage visibility. **Agent Identity Hub (AIH)** closes that security gap by provisioning and managing machine identities for AI agents with the same security rigour applied to human enterprise accounts.

---

## 🚀 Live Production Deployment

- **Live Web Application & API Base URL**: `https://agent-identity-hub.onrender.com`
- **Interactive Swagger API Docs**: `https://agent-identity-hub.onrender.com/docs`
- **System Health Endpoint**: `https://agent-identity-hub.onrender.com/health`

### Live Production Architecture & Deployment Checklist
- [x] **Multi-Worker Concurrency**: Gunicorn running 4 Uvicorn worker processes (`--timeout 120 --keep-alive 5`).
- [x] **Production Serverless Database**: Connected to Neon PostgreSQL with connection pool safety (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`) and safe auto-schema migrations.
- [x] **Single-Container Delivery**: Multi-stage Docker image serving FastAPI backend and Vite React SPA.
- [x] **AI Governance Engine**: Powered by Groq (`GROQ_API_KEY`) running Llama-3.3-70b (`AI_MODE=live`) with deterministic fallback heuristics. Gemini settings remain present in config for future use.

---

## ⚡ AI Infrastructure & Risk Reasoning

### Groq Provider Integration
- AI governance analysis, risk classification, and the 2-stage chatbot pipeline are powered by **Groq** (`llama-3.3-70b-versatile`).
- *Note on Gemini*: Google Gemini configuration settings (`GEMINI_API_KEY`) remain present in the codebase and config schema but are unused, preserving flexibility to swap providers without configuration churn.

### Risk-Level Reasoning Display
- Every agent registration triggers a grounded risk analysis.
- Rather than displaying unhelpful boilerplate, AIH surfaces a **short, specific risk-reasoning line directly under the Risk Badge** on the Identity Card (e.g. `Critical Risk — Agent has write access to payment records (payments:write), which can directly move enterprise funds.`).

---

## 💡 How AIH Fits into the AI Stack

### Credential Relationship & Boundaries
- **Access Credential vs. LLM Provider Key**: AIH issues and governs the agent's *enterprise access credential* (`aih_{agent_id}_{nonce}_{secret}`) used to access company tools and API scopes. AIH does **NOT** manage or store the agent's underlying LLM provider API key (e.g., OpenAI API key, Anthropic API key), which remains an internal runtime configuration outside AIH's boundary.
- **Enforcement Architecture**: AIH operates as an authoritative **Governance & Validation Service**. Downstream enterprise services or API gateways call `POST /credentials/validate` before honoring an agent request. AIH is an IAM authority, not an inline network proxy.

---

## 🔑 Demo & Evaluation Credentials

Seeded demo accounts available for immediate evaluation:

| Email | Password | Role | System Permissions |
| :--- | :--- | :--- | :--- |
| `admin@aih.dev` | `AdminPass123!` | **superadmin** | Full system control: admin account management (`/admins`), scope manifest mutation (`/scopes`), agent & credential CRUD. |
| `operator@aih.dev` | `OperatorPass123!` | **admin** | Full agent registration, credential lifecycle, and review CRUD. |
| `auditor@aih.dev` | `AuditorPass123!` | **auditor** | Read-only access across directory, dashboard, reports, and audit logs; 403 Forbidden on all mutating routes. |

---

## 🤖 Two-Stage AI Insights Chatbot Architecture

The AI Insights Chatbot (`POST /chatbot/ask` & floating UI widget) is implemented as a **real two-stage retrieval pipeline**:

```text
[User Question]
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 1: Retriever Agent (Groq Tool Calling)             │
│ - Inspects question and requests tool calls:             │
│   • list_agents(status?, owning_team?)                   │
│   • get_agent_detail(identifier)                         │
│   • list_stale_agents(inactivity_days?)                 │
│   • get_review_report(owning_team?)                      │
│   • search_audit_logs(agent_id?, action?)               │
│   • get_dashboard_metrics()                              │
│ - Executes queries against REAL database repository      │
│ - Server-side logs tool calls, args & returned counts    │
└──────────────────────────┬───────────────────────────────┘
                           │ Actual Structured DB Data
                           ▼
┌──────────────────────────────────────────────────────────┐
│ STAGE 2: Responder Agent (Facts-Only Synthesizer)        │
│ - System prompt: "Only state facts present in provided   │
│   retrieved data. Never invent agent names or dates."    │
│ - Formats concise, specific natural-language answer       │
└──────────────────────────────────────────────────────────┘
```

### Strict Domain & Read-Only Boundaries
- **Strict Domain Boundary**: Questions outside the AIH domain (e.g. *"What is the capital of France?"*) return: `"I can only answer questions about agents and data within Agent Identity Hub."`
- **Read-Only Guardrail**: Mutating requests (e.g. *"Revoke Agent X's credential"*) decline and direct users to the dashboard UI.
- **Telemetry Boundary**: Questions requesting non-existent telemetry (e.g. *"What is Agent X's uptime percentage?"*) state that performance telemetry is not tracked, never fabricating data.

---

## 🛠️ Local Development & Setup

### Prerequisites
- Python 3.12+
- Node.js v20+ & npm
- Docker & Docker Compose (optional)

### Environment Setup
1. Copy `.env.example` to create your local `.env`:
   ```bash
   cp .env.example .env
   ```
2. Set configuration values:
   ```env
   DATABASE_URL=sqlite:///./aih_local.db
   JWT_SECRET=super_secret_jwt_signing_key_replace_in_production_32bytes
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   REFRESH_TOKEN_EXPIRE_DAYS=7
   GROQ_API_KEY=your_groq_api_key_here
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
3. Launch FastAPI backend:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
4. Build or run Frontend React SPA:
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
*Save returned `access_token` as `TOKEN`.*

---

### 2. Register Agents with Owning Team & Tool Scopes

#### Agent 1 — Customer Support Reply Agent (Team: Customer Support)
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "SupportReplyBot",
    "purpose": "Reads customer tickets and drafts email replies",
    "owning_team": "Customer Support",
    "requested_scopes": ["tickets:read", "crm:read"]
  }'
```

#### Agent 2 — Financial Refund Agent (Team: Finance)
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "RefundProcessorBot",
    "purpose": "Processes customer financial refunds and updates ledger",
    "owning_team": "Finance",
    "requested_scopes": ["payments:read", "payments:write"]
  }'
```

---

### 3. Issue Credential & Verify Scope Enforcement

#### Issue Credential for Agent 1 (SupportReplyBot)
```bash
curl -X POST "http://localhost:8000/credentials/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "<AGENT_1_ID>", "expires_in_days": 90}'
```
*Save returned `credential` secret.*

#### A. Authorized Request (Read-Only Scope Granted)
```bash
curl -X POST "http://localhost:8000/credentials/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "<AGENT_1_CREDENTIAL_SECRET>",
    "requested_scope": "tickets:read"
  }'
```
*Expected Result:* `{"valid": true, "agent_id": "agt_...", "scopes": ["tickets:read", "crm:read"]}`
*(Note: Valid validation updates `last_used_at = now()` and increments `call_count` in real-time).*

#### B. Rejected Request (Write Scope Not Granted)
```bash
curl -X POST "http://localhost:8000/credentials/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "<AGENT_1_CREDENTIAL_SECRET>",
    "requested_scope": "payments:write"
  }'
```
*Expected Result:* `{"valid": false, "reason": "scope_not_authorized"}`

---

### 4. Prove Stale Agent Detection & Team Quarterly Access Review

#### Query Team Quarterly Access Review Report
```bash
curl -X GET "http://localhost:8000/reviews/report?owning_team=Customer%20Support" \
  -H "Authorization: Bearer $TOKEN"
```
*Returns structured report showing active agents, healthy agents, stale agents (inactive 30+ days), and recommendation summary.*

#### Instant Testing Affordance for Staleness
Query with `inactivity_days=0` to treat all inactive agents as stale immediately:
```bash
curl -X GET "http://localhost:8000/reviews/stale-agents?inactivity_days=0" \
  -H "Authorization: Bearer $TOKEN"
```

---

### 5. Prove Auto-Revoke & Testing Affordances

#### Instant Credential Expiry Testing
Generate a credential with an explicit past `expires_at` timestamp:
```bash
curl -X POST "http://localhost:8000/credentials/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "<AGENT_1_ID>",
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
*Expected Result:* `{"valid": false, "reason": "expired"}`

#### Instant Agent Identity Expiry Testing
Register an agent with an explicit past `expiry_date` timestamp:
```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "ExpiredIdentityBot",
    "purpose": "Test identity expiration",
    "owning_team": "DevOps",
    "expiry_date": "2026-01-01T00:00:00Z",
    "requested_scopes": ["tickets:read"]
  }'
```
Issue a credential and validate:
```bash
curl -X POST "http://localhost:8000/credentials/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "<CREDENTIAL_FOR_EXPIRED_AGENT>",
    "requested_scope": "tickets:read"
  }'
```
*Expected Result:* `{"valid": false, "reason": "agent_identity_expired"}`

---

## 🔐 Bonus — Auth0 / OIDC Integration Status

- **Status**: Conceptually scaffolded.
- **Architecture**: In an enterprise OIDC setup, AIH acts as the Governance Authority deciding identity lifecycle, owning teams, and scope approvals, while an external OIDC provider (Auth0/Okta) acts as the Token Issuer (issuing cryptographically signed JWT access tokens via client_credentials grant). AIH's fast `POST /credentials/validate` endpoint serves as the lightweight local verification authority.

---

## 📌 Known Limitations

- **Single-Org Scaffolding**: Multi-tenant `org_id` is present on all models but defaults to `org_default`.
- **In-Memory Scheduler**: APScheduler runs within the Uvicorn worker process. For multi-node horizontal scaling, a distributed redis lock or standalone worker runner is recommended.

---

## 📡 Complete API Endpoint Reference Table

| Method | Path | Auth & Role Required | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | None | System health check (`db` & `ai_mode` status). |
| `HEAD` | `/health` | None | Infrastructure health probe endpoint (bypasses audit logging). |
| `GET` | `/governance/ai-status` | None | Detailed AI client inspection (`provider: groq` when live). |
| `POST` | `/auth/login` | None | Admin authentication returning JWT access & refresh tokens. |
| `POST` | `/auth/refresh-token` | None | Obtains new access token using valid refresh token. |
| `GET` | `/auth/me` | Bearer (Any Role) | Returns logged-in admin profile and assigned role. |
| `GET` | `/agents` | Bearer (Any Role) | Paginated list of managed agents (supports `owning_team` filter). |
| `POST` | `/agents` | Bearer (`admin`/`superadmin`) | Registers new AI Agent with `owning_team`, `purpose`, and scopes. |
| `GET` | `/agents/{id}` | Bearer (Any Role) | Retrieves full Identity Card for an agent. |
| `PUT` | `/agents/{id}` | Bearer (`admin`/`superadmin`) | Updates agent identity details or granted scopes. |
| `DELETE` | `/agents/{id}` | Bearer (`superadmin`) | Soft-deletes agent (`lifecycle_status = deprovisioned`). |
| `GET` | `/scopes` | Bearer (Any Role) | Returns active live IAM scope manifest. |
| `POST` | `/scopes` | Bearer (`superadmin`) | Creates new API scope entry in runtime scope manifest. |
| `DELETE` | `/scopes/{id}` | Bearer (`superadmin`) | Soft-deletes or marks scope as deprecated if in active use. |
| `POST` | `/credentials/generate` | Bearer (`admin`/`superadmin`) | Issues two-part scoped credential (`aih_{id}_{nonce}_{secret}`). |
| `POST` | `/credentials/rotate` | Bearer (`admin`/`superadmin`) | Rotates credential secret and deactivates old secret. |
| `POST` | `/credentials/renew` | Bearer (`admin`/`superadmin`) | Extends credential expiration timestamp. |
| `POST` | `/credentials/revoke` | Bearer (`admin`/`superadmin`) | Revokes agent credential immediately. |
| `POST` | `/credentials/validate` | None (Public for AI) | Fast validation checking expiry, identity status, & scopes; updates usage metrics. |
| `POST` | `/chatbot/ask` | Bearer (Any Role) | 2-Stage AI Insights chatbot executing tool calls against real DB data. |
| `GET` | `/reviews/stale-agents` | Bearer (Any Role) | Lists agents inactive for 30+ days based on real usage metrics. |
| `GET` | `/reviews/report` | Bearer (Any Role) | Returns team quarterly access review report (filter by `owning_team`). |
| `GET` | `/reviews` | Bearer (Any Role) | Paginated list of historical governance review reports. |
| `POST` | `/reviews/run` | Bearer (`admin`/`superadmin`) | Triggers background governance sweeper jobs. |
| `POST` | `/governance/analyze` | Bearer (Any Role) | Evaluates posture, score penalties, and security recommendations. |
| `GET` | `/governance/security-score/{id}`| Bearer (Any Role) | Returns computed security score (0-100) & penalty breakdown. |
| `GET` | `/audit` | Bearer (Any Role) | Filterable, paginated audit log trail. |
| `GET` | `/dashboard` | Bearer (Any Role) | Aggregate SQL metrics, risk distribution, and activity feed. |
| `GET` | `/admins` | Bearer (`superadmin`) | Lists all admin accounts. |
| `POST` | `/admins` | Bearer (`superadmin`) | Creates new admin account (`email`, `password`, `role`). |
| `PUT` | `/admins/{id}` | Bearer (`superadmin`) | Updates admin role or `is_active` status. |
