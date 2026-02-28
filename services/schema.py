from __future__ import annotations

from sqlalchemy import BigInteger, Column, Integer, MetaData, String, Table, Text

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("user_id", BigInteger, primary_key=True),
    Column("user_name", Text),
    Column("user_username", Text),
    Column("chat_type", String(32)),
    Column("language", String(16)),
    Column("status", String(32)),
    Column("referrer_id", BigInteger),
)

sent_jokes = Table(
    "sent_jokes",
    metadata,
    Column("joke_id", Integer, nullable=False),
    Column("user_id", BigInteger, nullable=False),
)

votes = Table(
    "votes",
    metadata,
    Column("joke_id", Integer, nullable=False),
    Column("user_id", BigInteger, nullable=False),
    Column("vote_type", String(16), nullable=False),
)

ideas = Table(
    "ideas",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", Text, nullable=False),
)


def build_jokes_table(table_name: str) -> Table:
    return Table(
        table_name,
        metadata,
        Column("id", BigInteger, primary_key=True),
        Column("text", Text),
        Column("tags", Text),
        extend_existing=True,
    )
