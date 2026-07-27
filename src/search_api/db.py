from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL, EMBEDDING_DIM

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

_SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id text PRIMARY KEY,
    source_uri text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS chunks (
    id text PRIMARY KEY,
    document_id text NOT NULL REFERENCES documents(id),
    chunk_index int NOT NULL,
    text text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb,
    tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    embedding vector({EMBEDDING_DIM}) NOT NULL
);

CREATE INDEX IF NOT EXISTS chunks_tsv_idx ON chunks USING GIN(tsv);
CREATE INDEX IF NOT EXISTS chunks_metadata_idx ON chunks USING GIN(metadata);
"""


def init_db() -> None:
    with engine.begin() as conn:
        for statement in _SCHEMA.strip().split(";\n\n"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))


def reset_db() -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS chunks"))
        conn.execute(text("DROP TABLE IF EXISTS documents"))
    init_db()
