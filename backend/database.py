"""
GNOVA Fintech Platform - Database Layer
SQLite with full ACID transaction support
Designed for easy PostgreSQL migration
"""

import aiosqlite
from pathlib import Path
from datetime import datetime, timezone
import uuid

DATABASE_PATH = Path(__file__).parent / "gnova.db"


async def get_db():
    """Get database connection"""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    # Enable foreign keys
    await db.execute("PRAGMA foreign_keys = ON")
    return db


# ==================== Table Creation ====================

async def create_asset_tables(db):
    """Create asset-related tables (assets, exchange rates)"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id TEXT PRIMARY KEY,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            decimal_precision INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id TEXT PRIMARY KEY,
            base_asset_id TEXT NOT NULL,
            quote_asset_id TEXT NOT NULL,
            rate_numeric REAL NOT NULL,
            spread_percentage REAL,
            source TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (base_asset_id) REFERENCES assets(id),
            FOREIGN KEY (quote_asset_id) REFERENCES assets(id)
        )
    """)


async def create_user_tables(db):
    """Create user-related tables (users, settings, referrals)"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            password_hash TEXT,
            kyc_status TEXT DEFAULT 'pending',
            risk_level TEXT DEFAULT 'low',
            status TEXT DEFAULT 'active',
            two_fa_enabled INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            language TEXT DEFAULT 'fa',
            currency TEXT DEFAULT 'IRR',
            notifications_enabled INTEGER DEFAULT 1,
            spending_limit_daily INTEGER,
            spending_limit_monthly INTEGER,
            settings_json TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id TEXT PRIMARY KEY,
            referrer_user_id TEXT NOT NULL,
            referred_user_id TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            reward_amount INTEGER,
            created_at TEXT NOT NULL,
            completed_at TEXT,
            FOREIGN KEY (referrer_user_id) REFERENCES users(id),
            FOREIGN KEY (referred_user_id) REFERENCES users(id)
        )
    """)


async def create_ledger_tables(db):
    """Create ledger tables (accounts, transactions, ledger entries)"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            asset_id TEXT NOT NULL,
            account_type TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (asset_id) REFERENCES assets(id),
            UNIQUE(user_id, asset_id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            asset_from_id TEXT,
            asset_to_id TEXT,
            amount_from_minor INTEGER,
            amount_to_minor INTEGER,
            fee_minor INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            reference_id TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS ledger_entries (
            id TEXT PRIMARY KEY,
            transaction_id TEXT NOT NULL,
            account_id TEXT NOT NULL,
            asset_id TEXT NOT NULL,
            debit_minor INTEGER DEFAULT 0,
            credit_minor INTEGER DEFAULT 0,
            source_event TEXT NOT NULL,
            source_ref TEXT,
            status TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (asset_id) REFERENCES assets(id)
        )
    """)


async def create_operations_tables(db):
    """Create operational tables (webhooks, quotes, alerts, categories, audit)"""
    await db.execute("""
        CREATE TABLE IF NOT EXISTS webhook_events (
            id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            external_id TEXT UNIQUE,
            payload TEXT,
            signature_valid INTEGER,
            processed INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS conversion_quotes (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            from_asset_id TEXT NOT NULL,
            to_asset_id TEXT NOT NULL,
            amount_minor INTEGER NOT NULL,
            rate REAL NOT NULL,
            quoted_amount_minor INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id TEXT PRIMARY KEY,
            actor_id TEXT,
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            before_state TEXT,
            after_state TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS rate_alerts (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            from_asset_id TEXT NOT NULL,
            to_asset_id TEXT NOT NULL,
            target_rate REAL NOT NULL,
            condition TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS transaction_categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            emoji TEXT,
            color TEXT,
            created_at TEXT NOT NULL
        )
    """)


async def setup_indexes(db):
    """Create all database indexes"""
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)
    """)
    await db.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_ledger_source_ref 
        ON ledger_entries(source_ref) WHERE source_ref IS NOT NULL
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_ledger_account_id ON ledger_entries(account_id)
    """)


async def create_tables(db):
    """Create all database tables and indexes"""
    await create_asset_tables(db)
    await create_user_tables(db)
    await create_ledger_tables(db)
    await create_operations_tables(db)
    await setup_indexes(db)


# ==================== Initialization ====================

async def init_database():
    """Initialize database schema and seed data"""
    db = await aiosqlite.connect(DATABASE_PATH)
    await db.execute("PRAGMA foreign_keys = ON")

    try:
        await create_tables(db)
        await db.commit()

        await seed_initial_data(db)
        await db.commit()

        print("✅ Database initialized successfully")

    except Exception as e:
        await db.rollback()
        print(f"❌ Database initialization error: {e}")
        raise
    finally:
        await db.close()


# ==================== Seed Data ====================

async def seed_initial_data(db):
    """Seed all default data"""
    await seed_default_assets(db)
    await seed_default_categories(db)


async def seed_default_assets(db):
    """Seed default assets"""
    now = datetime.now(timezone.utc).isoformat()
    
    default_assets = [
        {
            "id": "asset-credit-irr",
            "code": "CREDIT",
            "name": "اعتبار ریالی",
            "type": "fiat",
            "decimal_precision": 0
        },
        {
            "id": "asset-irr",
            "code": "IRR",
            "name": "ریال ایران",
            "type": "fiat",
            "decimal_precision": 0
        },
        {
            "id": "asset-usdt",
            "code": "USDT",
            "name": "Tether",
            "type": "crypto",
            "decimal_precision": 6
        },
        {
            "id": "asset-btc",
            "code": "BTC",
            "name": "Bitcoin",
            "type": "crypto",
            "decimal_precision": 8
        }
    ]
    
    for asset in default_assets:
        try:
            await db.execute("""
                INSERT OR IGNORE INTO assets (id, code, name, type, decimal_precision, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (asset["id"], asset["code"], asset["name"], asset["type"], 
                  asset["decimal_precision"], now))
        except Exception as e:
            print(f"Asset {asset['code']} already exists or error: {e}")


async def seed_default_categories(db):
    """Seed default transaction categories"""
    now = datetime.now(timezone.utc).isoformat()
    
    categories = [
        {"id": str(uuid.uuid4()), "name": "واریز", "emoji": "💰", "color": "#10b981"},
        {"id": str(uuid.uuid4()), "name": "برداشت", "emoji": "💸", "color": "#ef4444"},
        {"id": str(uuid.uuid4()), "name": "تبدیل", "emoji": "🔄", "color": "#3b82f6"},
        {"id": str(uuid.uuid4()), "name": "خرید", "emoji": "🛒", "color": "#f59e0b"},
        {"id": str(uuid.uuid4()), "name": "انتقال", "emoji": "↔️", "color": "#8b5cf6"},
    ]
    
    for cat in categories:
        try:
            await db.execute("""
                INSERT OR IGNORE INTO transaction_categories (id, name, emoji, color, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (cat["id"], cat["name"], cat["emoji"], cat["color"], now))
        except Exception:
            pass


if __name__ == "__main__":
    import asyncio
    asyncio.run(init_database())
