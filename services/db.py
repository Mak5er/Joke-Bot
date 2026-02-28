from __future__ import annotations

import re

from cachetools import TTLCache
from sqlalchemy import and_, case, delete, exists, func, insert, literal, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

import config
from services.schema import build_jokes_table, ideas, sent_jokes, users, votes

SAFE_TABLE_NAME = re.compile(r"^[a-z_][a-z0-9_]*$")


class DataBase:
    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
        self._language_cache: TTLCache[int, str] = TTLCache(maxsize=20_000, ttl=600)
        self._status_cache: TTLCache[int, str] = TTLCache(maxsize=20_000, ttl=300)

    async def connect(self) -> None:
        if self._engine is not None:
            return

        self._engine = create_async_engine(
            self._to_sqlalchemy_dsn(config.db_auth),
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=10,
        )
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

        async with self._engine.connect() as connection:
            await connection.execute(select(1))

        await self._ensure_indexes()

    async def close(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def _to_sqlalchemy_dsn(self, dsn: str) -> str:
        if dsn.startswith("postgresql+psycopg://"):
            return dsn
        if dsn.startswith("postgresql://"):
            return dsn.replace("postgresql://", "postgresql+psycopg://", 1)
        if dsn.startswith("postgres://"):
            return dsn.replace("postgres://", "postgresql+psycopg://", 1)
        return dsn

    def _table_name(self, table_name: str) -> str:
        if not SAFE_TABLE_NAME.fullmatch(table_name):
            raise ValueError(f"Unsafe table name: {table_name}")
        return table_name

    def _jokes_table(self, table_name: str):
        return build_jokes_table(self._table_name(table_name))

    async def _session(self) -> AsyncSession:
        if self._session_factory is None:
            await self.connect()

        if self._session_factory is None:
            raise RuntimeError("Database session factory is not initialized")

        return self._session_factory()

    async def _execute(self, statement) -> None:
        async with await self._session() as session:
            await session.execute(statement)
            await session.commit()

    async def _fetchall(self, statement):
        async with await self._session() as session:
            result = await session.execute(statement)
            return [tuple(row) for row in result.fetchall()]

    async def _fetchone(self, statement):
        async with await self._session() as session:
            result = await session.execute(statement)
            row = result.fetchone()
            return tuple(row) if row is not None else None

    async def _fetchval(self, statement):
        async with await self._session() as session:
            result = await session.execute(statement)
            return result.scalar_one_or_none()

    async def _ensure_indexes(self) -> None:
        index_statements = [
            "CREATE INDEX IF NOT EXISTS idx_sent_jokes_user_joke ON sent_jokes (user_id, joke_id)",
            "CREATE INDEX IF NOT EXISTS idx_sent_jokes_joke_id ON sent_jokes (joke_id)",
            "CREATE INDEX IF NOT EXISTS idx_votes_joke_user ON votes (joke_id, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_votes_joke_type ON votes (joke_id, vote_type)",
            "CREATE INDEX IF NOT EXISTS idx_users_chat_type_status ON users (chat_type, status)",
            "CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users (referrer_id)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users (user_username)",
        ]
        async with await self._session() as session:
            for statement in index_statements:
                await session.execute(text(statement))
            await session.commit()

    async def add_users(
        self,
        user_id,
        user_name,
        user_username,
        chat_type,
        language,
        status,
        referrer_id,
    ):
        statement = pg_insert(users).values(
            user_id=user_id,
            user_name=user_name,
            user_username=user_username,
            chat_type=chat_type,
            language=language,
            status=status,
            referrer_id=referrer_id,
        ).on_conflict_do_nothing(index_elements=[users.c.user_id])
        await self._execute(statement)
        self._language_cache[user_id] = language
        self._status_cache[user_id] = status

    async def sync_user(
        self,
        user_id,
        user_name,
        user_username,
        chat_type,
        language,
        status,
        referrer_id=None,
    ):
        statement = pg_insert(users).values(
            user_id=user_id,
            user_name=user_name,
            user_username=user_username,
            chat_type=chat_type,
            language=language,
            status=status,
            referrer_id=referrer_id,
        )
        excluded = statement.excluded
        update_values = {
            "user_name": excluded.user_name,
            "user_username": excluded.user_username,
            "chat_type": case(
                (users.c.chat_type == "private", users.c.chat_type),
                (excluded.chat_type == "private", excluded.chat_type),
                else_=excluded.chat_type,
            ),
            "language": case(
                (excluded.chat_type == "private", excluded.language),
                else_=func.coalesce(users.c.language, excluded.language),
            ),
            "status": case(
                (users.c.status == "ban", users.c.status),
                else_=excluded.status,
            ),
            "referrer_id": func.coalesce(users.c.referrer_id, excluded.referrer_id),
        }
        await self._execute(statement.on_conflict_do_update(index_elements=[users.c.user_id], set_=update_values))
        self._language_cache.pop(user_id, None)
        self._status_cache.pop(user_id, None)

    async def delete_user(self, user_id):
        await self._execute(delete(users).where(users.c.user_id == user_id))
        self._language_cache.pop(user_id, None)
        self._status_cache.pop(user_id, None)

    async def user_count(self):
        return await self._fetchval(select(func.count()).select_from(users)) or 0

    async def active_user_count(self):
        return await self._fetchval(
            select(func.count()).select_from(users).where(users.c.status == "active")
        ) or 0

    async def inactive_user_count(self):
        return await self._fetchval(
            select(func.count()).select_from(users).where(users.c.status != "active")
        ) or 0

    async def joke_count(self, table_name):
        jokes_table = self._jokes_table(table_name)
        return await self._fetchval(select(func.count()).select_from(jokes_table)) or 0

    async def sent_count(self):
        return await self._fetchval(select(func.count()).select_from(sent_jokes)) or 0

    async def joke_sent(self, user_id):
        return await self._fetchval(
            select(func.count()).select_from(sent_jokes).where(sent_jokes.c.user_id == user_id)
        ) or 0

    async def all_users(self):
        return await self._fetchall(select(users.c.user_id).order_by(users.c.user_id))

    async def user_exist(self, user_id):
        statement = select(exists(select(1).select_from(users).where(users.c.user_id == user_id)))
        return bool(await self._fetchval(statement))

    async def user_update_name(self, user_id, user_name, user_username):
        await self._execute(
            update(users)
            .where(users.c.user_id == user_id)
            .values(user_username=user_username, user_name=user_name)
        )

    async def get_private_users(self):
        statement = (
            select(users.c.user_id)
            .distinct()
            .where(and_(users.c.chat_type == "private", users.c.status == "active"))
            .order_by(users.c.user_id)
        )
        return await self._fetchall(statement)

    async def refs_count(self, referrer_id):
        return await self._fetchval(
            select(func.count()).select_from(users).where(users.c.referrer_id == referrer_id)
        ) or 0

    async def add_joke(self, joke_text, table_name):
        jokes_table = self._jokes_table(table_name)
        await self._execute(insert(jokes_table).values(text=joke_text))

    async def seen_joke(self, joke_id, user_id):
        exists_query = (
            select(1)
            .select_from(sent_jokes)
            .where(and_(sent_jokes.c.joke_id == joke_id, sent_jokes.c.user_id == user_id))
        )
        select_values = select(literal(joke_id), literal(user_id)).where(~exists(exists_query))
        statement = insert(sent_jokes).from_select(["joke_id", "user_id"], select_values)
        await self._execute(statement)

    async def check_seen_joke(self, joke_id, user_id):
        statement = select(literal(1)).select_from(sent_jokes).where(
            and_(sent_jokes.c.joke_id == joke_id, sent_jokes.c.user_id == user_id)
        )
        return await self._fetchone(statement)

    async def joke_seens(self, joke_id):
        return await self._fetchval(
            select(func.count()).select_from(sent_jokes).where(sent_jokes.c.joke_id == joke_id)
        ) or 0

    async def joke_rate(self, joke_id, table_name):
        likes_count = await self.count_votes(joke_id, "like")
        dislikes_count = await self.count_votes(joke_id, "dislike")
        return likes_count - dislikes_count

    async def like_joke(self, joke_id, table_name):
        return None

    async def dislike_joke(self, joke_id, table_name):
        return None

    async def get_joke(self, user_id):
        jokes_table = self._jokes_table("jokes_uk")
        votes_count = (
            select(func.count())
            .select_from(votes)
            .where(votes.c.joke_id == jokes_table.c.id)
            .scalar_subquery()
        )
        seen_exists = exists(
            select(1)
            .select_from(sent_jokes)
            .where(and_(sent_jokes.c.joke_id == jokes_table.c.id, sent_jokes.c.user_id == user_id))
        )
        statement = (
            select(jokes_table)
            .where(~seen_exists)
            .order_by(votes_count.desc(), jokes_table.c.id.asc())
            .limit(1)
        )
        return await self._fetchall(statement)

    async def get_tagged_joke(self, user_id, tag):
        jokes_table = self._jokes_table("jokes_uk")
        votes_count = (
            select(func.count())
            .select_from(votes)
            .where(votes.c.joke_id == jokes_table.c.id)
            .scalar_subquery()
        )
        seen_exists = exists(
            select(1)
            .select_from(sent_jokes)
            .where(and_(sent_jokes.c.joke_id == jokes_table.c.id, sent_jokes.c.user_id == user_id))
        )
        statement = (
            select(jokes_table)
            .where(and_(jokes_table.c.tags.ilike(f"%{tag}%"), ~seen_exists))
            .order_by(votes_count.desc(), jokes_table.c.id.asc())
            .limit(1)
        )
        return await self._fetchall(statement)

    async def get_daily_joke(self):
        jokes_table = self._jokes_table("jokes_uk")
        votes_count = (
            select(func.count())
            .select_from(votes)
            .where(votes.c.joke_id == jokes_table.c.id)
            .scalar_subquery()
        )
        seen_exists = exists(select(1).select_from(sent_jokes).where(sent_jokes.c.joke_id == jokes_table.c.id))
        statement = select(jokes_table).where(~seen_exists).order_by(votes_count.desc(), jokes_table.c.id.asc()).limit(1)
        return await self._fetchall(statement)

    async def get_joke_by_id(self, joke_id):
        jokes_table = self._jokes_table("jokes_uk")
        joke = await self._fetchone(select(jokes_table).where(jokes_table.c.id == int(joke_id)))
        return [joke] if joke else []

    async def get_joke_by_text(self, text):
        jokes_table = self._jokes_table("jokes_uk")
        statement = select(jokes_table).where(jokes_table.c.text.ilike(f"%{text}%")).order_by(jokes_table.c.id.asc())
        return await self._fetchall(statement)

    async def get_joke_meta(self, joke_id, user_id):
        jokes_table = self._jokes_table("jokes_uk")
        likes_count = (
            select(func.count())
            .select_from(votes)
            .where(and_(votes.c.joke_id == joke_id, votes.c.vote_type == "like"))
            .scalar_subquery()
        )
        dislikes_count = (
            select(func.count())
            .select_from(votes)
            .where(and_(votes.c.joke_id == joke_id, votes.c.vote_type == "dislike"))
            .scalar_subquery()
        )
        user_vote = (
            select(votes.c.vote_type)
            .where(and_(votes.c.joke_id == joke_id, votes.c.user_id == user_id))
            .limit(1)
            .scalar_subquery()
        )

        statement = select(
            jokes_table.c.tags,
            likes_count.label("likes_count"),
            dislikes_count.label("dislikes_count"),
            user_vote.label("user_vote"),
        ).where(jokes_table.c.id == joke_id)

        row = await self._fetchone(statement)
        return row if row is not None else (None, 0, 0, None)

    async def get_language(self, user_id):
        if user_id in self._language_cache:
            return self._language_cache[user_id]

        language = await self._fetchval(select(users.c.language).where(users.c.user_id == user_id))
        if language is not None:
            self._language_cache[user_id] = language
        return language

    async def get_tags(self, joke_id):
        jokes_table = self._jokes_table("jokes_uk")
        return await self._fetchval(select(jokes_table.c.tags).where(jokes_table.c.id == joke_id))

    async def set_language(self, user_id, language):
        await self._execute(update(users).where(users.c.user_id == user_id).values(language=language))
        self._language_cache[user_id] = language

    async def status(self, user_id):
        if user_id in self._status_cache:
            return self._status_cache[user_id]

        status = await self._fetchval(select(users.c.status).where(users.c.user_id == user_id))
        if status is not None:
            self._status_cache[user_id] = status
        return status

    async def get_user_info(self, user_id):
        statement = select(users.c.user_name, users.c.user_username, users.c.status).where(users.c.user_id == int(user_id))
        return await self._fetchone(statement)

    async def get_user_info_username(self, user_username):
        statement = select(users.c.user_name, users.c.user_id, users.c.status).where(users.c.user_username == user_username)
        return await self._fetchone(statement)

    async def get_all_users_info(self):
        statement = select(
            users.c.user_id,
            users.c.chat_type,
            users.c.user_name,
            users.c.user_username,
            users.c.language,
            users.c.status,
            users.c.referrer_id,
        ).order_by(users.c.user_id)
        return await self._fetchall(statement)

    async def ban_user(self, user_id):
        await self._execute(update(users).where(users.c.user_id == int(user_id)).values(status="ban"))
        self._status_cache[int(user_id)] = "ban"

    async def set_inactive(self, user_id):
        await self._execute(update(users).where(users.c.user_id == int(user_id)).values(status="inactive"))
        self._status_cache[int(user_id)] = "inactive"

    async def set_active(self, user_id):
        await self._execute(update(users).where(users.c.user_id == int(user_id)).values(status="active"))
        self._status_cache[int(user_id)] = "active"

    async def add_vote(self, joke_id, user_id, vote_type):
        exists_query = (
            select(1)
            .select_from(votes)
            .where(and_(votes.c.joke_id == joke_id, votes.c.user_id == user_id))
        )
        select_values = select(literal(joke_id), literal(user_id), literal(vote_type)).where(~exists(exists_query))
        statement = insert(votes).from_select(["joke_id", "user_id", "vote_type"], select_values)
        await self._execute(statement)

    async def remove_vote(self, joke_id, user_id):
        await self._execute(delete(votes).where(and_(votes.c.joke_id == joke_id, votes.c.user_id == user_id)))

    async def update_vote(self, joke_id, user_id, new_vote_type):
        await self._execute(
            update(votes)
            .where(and_(votes.c.joke_id == joke_id, votes.c.user_id == user_id))
            .values(vote_type=new_vote_type)
        )

    async def get_user_vote(self, joke_id, user_id):
        statement = select(votes.c.vote_type).where(and_(votes.c.joke_id == joke_id, votes.c.user_id == user_id))
        return await self._fetchval(statement)

    async def count_votes(self, joke_id, vote_type):
        statement = select(func.count()).select_from(votes).where(
            and_(votes.c.joke_id == joke_id, votes.c.vote_type == vote_type)
        )
        return await self._fetchval(statement) or 0

    async def get_ideas(self):
        return await self._fetchall(select(ideas.c.id, ideas.c.text).order_by(ideas.c.id.asc()))

    async def get_languages_for_users(self, user_ids):
        if not user_ids:
            return {}

        statement = select(users.c.user_id, users.c.language).where(users.c.user_id.in_(user_ids))
        rows = await self._fetchall(statement)
        languages = {user_id: language for user_id, language in rows if language}
        self._language_cache.update(languages)
        return languages

    async def get_votes_for_users(self, joke_id, user_ids):
        if not user_ids:
            return {}

        statement = select(votes.c.user_id, votes.c.vote_type).where(
            and_(votes.c.joke_id == joke_id, votes.c.user_id.in_(user_ids))
        )
        rows = await self._fetchall(statement)
        return {user_id: vote_type for user_id, vote_type in rows}

    async def get_idea(self, idea_id):
        return await self._fetchone(select(ideas.c.text).where(ideas.c.id == idea_id))

    async def delete_idea(self, note_id):
        await self._execute(delete(ideas).where(ideas.c.id == note_id))

    async def add_idea(self, text):
        await self._execute(insert(ideas).values(text=text))


database = DataBase()
