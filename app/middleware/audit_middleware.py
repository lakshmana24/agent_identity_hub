import json
import logging
from datetime import datetime, timezone
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.database.session import SessionLocal
from app.repository.audit_repository import create_audit_log
from app.auth.jwt_handler import decode_token

logger = logging.getLogger("aih.audit")

EXCLUDED_PATHS = {"/health", "/metrics", "/audit", "/docs", "/openapi.json", "/redoc"}

def map_action(method: str, path: str) -> str:
    if path.startswith("/auth/login"):
        return "auth.login"
    elif path.startswith("/auth/refresh-token"):
        return "auth.refresh"
    elif path.startswith("/agents") and method == "POST":
        return "agent.register"
    elif path.startswith("/agents") and method == "PUT":
        return "agent.update"
    elif path.startswith("/agents") and method == "DELETE":
        return "agent.delete"
    elif path.startswith("/credentials/generate"):
        return "credential.generate"
    elif path.startswith("/credentials/rotate"):
        return "credential.rotate"
    elif path.startswith("/credentials/renew"):
        return "credential.renew"
    elif path.startswith("/credentials/revoke"):
        return "credential.revoke"
    elif path.startswith("/credentials/validate"):
        return "credential.validate"
    elif path.startswith("/governance/analyze"):
        return "governance.analyze"
    elif path.startswith("/governance/scope-recommendation"):
        return "governance.recommend_scopes"
    elif path.startswith("/governance/identity-summary"):
        return "governance.identity_summary"
    return f"{path.strip('/').replace('/', '.')}.{method.lower()}"

class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        method = request.method
        path = request.url.path

        # 1. Skip non-mutating requests (GET, OPTIONS) and excluded paths
        if method in ("GET", "OPTIONS") or any(path.startswith(ex) for ex in EXCLUDED_PATHS):
            return await call_next(request)

        # 2. Extract performed_by from Authorization Bearer token
        performed_by = "anonymous"
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = decode_token(token)
                performed_by = payload.get("email") or payload.get("sub", "admin")
            except Exception:
                performed_by = "invalid_token"

        # 3. Extract agent_id from path params or request body preview
        agent_id = None
        # Extract from path e.g., /agents/agt_123 or /governance/security-score/agt_123
        parts = path.split("/")
        for p in parts:
            if p.startswith("agt_"):
                agent_id = p
                break

        # Read body for POST/PUT if agent_id not in path
        request_body_bytes = b""
        if not agent_id and method in ("POST", "PUT"):
            try:
                request_body_bytes = await request.body()
                if request_body_bytes:
                    body_json = json.loads(request_body_bytes.decode("utf-8"))
                    agent_id = body_json.get("agent_id")
            except Exception:
                pass

            # Re-wrap request body stream so endpoint handlers can read it
            async def receive():
                return {"type": "http.request", "body": request_body_bytes}
            request = Request(request.scope, receive=receive)

        # 4. Call endpoint
        response = await call_next(request)

        # 5. Non-blocking audit log creation post-response
        try:
            status_code = response.status_code
            status_str = "success" if status_code < 400 else "failure"
            action_name = map_action(method, path)

            metadata = {
                "client_host": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }

            db = SessionLocal()
            try:
                create_audit_log(db, {
                    "action": action_name,
                    "method": method,
                    "path": path,
                    "agent_id": agent_id,
                    "performed_by": performed_by,
                    "status_code": status_code,
                    "status": status_str,
                    "metadata_json": metadata,
                    "timestamp": datetime.now(timezone.utc)
                })
            finally:
                db.close()
        except Exception as e:
            logger.error(f"AuditMiddleware error writing log: {e}")

        return response
