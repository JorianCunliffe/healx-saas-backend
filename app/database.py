
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Logic: If DATABASE_URL is set, use it.
# If not, check if we are local (likely docker-compose).
# If neither, fallback to SQLite so the app boots on Cloud Run without config.
database_url = os.getenv("DATABASE_URL")

if not database_url:
    # Default fallback for standalone/cloud-run without Cloud SQL.
    # We use /tmp because the application directory might be read-only in some container environments.
    database_url = "sqlite+aiosqlite:////tmp/healx_fallback.db"
    print(f"WARNING: DATABASE_URL not set. Using SQLite fallback: {database_url}")
else:
    print(f"Connecting to database: {database_url}")

engine = create_async_engine(database_url, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
