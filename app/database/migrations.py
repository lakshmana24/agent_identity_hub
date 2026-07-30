import logging
from sqlalchemy import inspect, text

logger = logging.getLogger("aih.migrations")

def apply_auto_migrations(engine):
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    is_postgres = "postgres" in engine.dialect.name

    with engine.connect() as conn:
        # 1. scope_manifest table
        if "scope_manifest" in tables:
            cols = [c["name"] for c in inspector.get_columns("scope_manifest")]
            if "deprecated" not in cols:
                logger.info("Migrating scope_manifest: adding 'deprecated' column")
                conn.execute(text("ALTER TABLE scope_manifest ADD COLUMN deprecated BOOLEAN NOT NULL DEFAULT FALSE;"))

        # 2. agents table
        if "agents" in tables:
            cols = [c["name"] for c in inspector.get_columns("agents")]
            if "owning_team" not in cols:
                logger.info("Migrating agents: adding 'owning_team' column")
                conn.execute(text("ALTER TABLE agents ADD COLUMN owning_team VARCHAR NOT NULL DEFAULT 'DefaultTeam';"))
            if "expiry_date" not in cols:
                logger.info("Migrating agents: adding 'expiry_date' column")
                conn.execute(text("ALTER TABLE agents ADD COLUMN expiry_date TIMESTAMP WITH TIME ZONE;"))
            if "model_provider" not in cols:
                conn.execute(text("ALTER TABLE agents ADD COLUMN model_provider VARCHAR NOT NULL DEFAULT 'Other';"))
            if "model_name" not in cols:
                conn.execute(text("ALTER TABLE agents ADD COLUMN model_name VARCHAR NOT NULL DEFAULT 'unknown';"))
            if "tools" not in cols:
                if is_postgres:
                    conn.execute(text("ALTER TABLE agents ADD COLUMN tools JSON NOT NULL DEFAULT '[]'::json;"))
                else:
                    conn.execute(text("ALTER TABLE agents ADD COLUMN tools JSON NOT NULL DEFAULT '[]';"))
            if "agent_endpoint_url" not in cols:
                conn.execute(text("ALTER TABLE agents ADD COLUMN agent_endpoint_url VARCHAR;"))
            if "deployment_environment" not in cols:
                conn.execute(text("ALTER TABLE agents ADD COLUMN deployment_environment VARCHAR NOT NULL DEFAULT 'production';"))
            if "risk_level_source" not in cols:
                conn.execute(text("ALTER TABLE agents ADD COLUMN risk_level_source VARCHAR NOT NULL DEFAULT 'ai_recommended';"))

        # 3. credentials table
        if "credentials" in tables:
            cols = [c["name"] for c in inspector.get_columns("credentials")]
            if "last_used_at" not in cols:
                logger.info("Migrating credentials: adding 'last_used_at' column")
                conn.execute(text("ALTER TABLE credentials ADD COLUMN last_used_at TIMESTAMP WITH TIME ZONE;"))
            if "call_count" not in cols:
                logger.info("Migrating credentials: adding 'call_count' column")
                conn.execute(text("ALTER TABLE credentials ADD COLUMN call_count INTEGER NOT NULL DEFAULT 0;"))

        # 4. admins table
        if "admins" in tables:
            cols = [c["name"] for c in inspector.get_columns("admins")]
            if "is_active" not in cols:
                logger.info("Migrating admins: adding 'is_active' column")
                conn.execute(text("ALTER TABLE admins ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;"))

        conn.commit()
