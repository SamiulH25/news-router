from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import _BACKEND_ROOT, settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={"timeout": 30},
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


async def init_db() -> None:
    from app import models  # noqa: F401

    (_BACKEND_ROOT / "data").mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_schema)


def _table_columns(sync_conn, table: str) -> set[str]:
    cursor = sync_conn.execute(text(f"PRAGMA table_info({table})"))
    return {row[1] for row in cursor.fetchall()}


def _migrate_schema(sync_conn) -> None:
    article_cols = _table_columns(sync_conn, "articles")
    if "image_url" not in article_cols:
        sync_conn.execute(text("ALTER TABLE articles ADD COLUMN image_url VARCHAR(2048)"))
    sync_conn.execute(
        text(
            "UPDATE articles SET summary = NULL "
            "WHERE summary LIKE '%Article URL:%' OR summary LIKE '%Comments URL:%'"
        )
    )

    ua_cols = _table_columns(sync_conn, "user_articles")
    if "archived_at" not in ua_cols:
        sync_conn.execute(text("ALTER TABLE user_articles ADD COLUMN archived_at DATETIME"))
    for col, ddl in [
        ("dwell_ms", "INTEGER DEFAULT 0"),
        ("opened_full", "BOOLEAN DEFAULT 0"),
        ("skipped", "BOOLEAN DEFAULT 0"),
    ]:
        if col not in ua_cols:
            sync_conn.execute(text(f"ALTER TABLE user_articles ADD COLUMN {col} {ddl}"))

    topic_cols = _table_columns(sync_conn, "topics")
    if "exclude_keywords" not in topic_cols:
        sync_conn.execute(text("ALTER TABLE topics ADD COLUMN exclude_keywords TEXT DEFAULT ''"))

    user_cols = _table_columns(sync_conn, "users")
    for col, ddl in [
        ("digest_evening_hour", "INTEGER DEFAULT 19"),
        ("digest_evening_minute", "INTEGER DEFAULT 0"),
        ("timezone", "VARCHAR(64) DEFAULT 'UTC'"),
        ("feed_window_hours", "INTEGER DEFAULT 12"),
        ("last_edition_at", "DATETIME"),
    ]:
        if col not in user_cols:
            sync_conn.execute(text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))
    if "onboarded" not in user_cols:
        sync_conn.execute(text("ALTER TABLE users ADD COLUMN onboarded BOOLEAN DEFAULT 0"))
        sync_conn.execute(text("UPDATE users SET onboarded = 1"))
    if "personalized_feed" not in user_cols:
        sync_conn.execute(text("ALTER TABLE users ADD COLUMN personalized_feed BOOLEAN DEFAULT 1"))

    ft_cols = _table_columns(sync_conn, "feed_topics")
    if "user_id" not in ft_cols:
        sync_conn.execute(
            text(
                """
                CREATE TABLE feed_topics_new (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    feed_id INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
                    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
                    UNIQUE(user_id, feed_id, topic_id)
                )
                """
            )
        )
        sync_conn.execute(
            text(
                """
                INSERT INTO feed_topics_new (id, user_id, feed_id, topic_id)
                SELECT ft.id, t.user_id, ft.feed_id, ft.topic_id
                FROM feed_topics ft
                JOIN topics t ON t.id = ft.topic_id
                """
            )
        )
        sync_conn.execute(text("DROP TABLE feed_topics"))
        sync_conn.execute(text("ALTER TABLE feed_topics_new RENAME TO feed_topics"))
