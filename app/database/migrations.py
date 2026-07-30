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
                conn.execute(text("ALTER TABLE agents ADD COLUMN owning_team VARCHAR NOT NULL DEFAULT 'Growth';"))
            if "expiry_date" not in cols:
                logger.info("Migrating agents: adding 'expiry_date' column")
                conn.execute(text("ALTER TABLE agents ADD COLUMN expiry_date TIMESTAMP WITH TIME ZONE;"))
            if "risk_reasoning" not in cols:
                logger.info("Migrating agents: adding 'risk_reasoning' column")
                conn.execute(text("ALTER TABLE agents ADD COLUMN risk_reasoning VARCHAR;"))

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
