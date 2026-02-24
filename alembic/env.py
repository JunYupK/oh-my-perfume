import os
import sys

from alembic import context
from sqlalchemy import create_engine, pool


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from app.core.config import settings
from app.models.base import Base
import app.models.brand  # noqa: F401 — Base.metadata에 테이블 등록
import app.models.perfume  # noqa: F401 — Base.metadata에 테이블 등록

config = context.config

db_url = os.getenv("DATABASE_URL", settings.database_url)
sync_db_url = db_url.replace("+asyncpg", "+psycopg")
config.set_main_option("sqlalchemy.url", sync_db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        sync_db_url,
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
