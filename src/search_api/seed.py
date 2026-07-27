"""Load the sample corpus (corpus/sample) into Postgres: chunk each
document by paragraph, embed each chunk with the stub embedder, and insert.
Idempotent: re-running truncates and reloads, so the demo corpus is always
a known state.
"""
import json
import os
import re
from pathlib import Path

from sqlalchemy import text

from .db import SessionLocal, reset_db
from .embedder import embed

# In the packaged/installed case (pip install .), __file__ lives under
# site-packages, nowhere near the repo's corpus/ directory -- so the
# container sets CORPUS_DIR explicitly. Falling back to cwd-relative covers
# running seed.py straight from a repo checkout without installing.
_CORPUS_DIR = Path(os.environ.get("CORPUS_DIR", "corpus/sample")).resolve()

_FRONT_MATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _parse_front_matter(raw: str) -> tuple[dict, str]:
    match = _FRONT_MATTER_RE.match(raw)
    if not match:
        return {}, raw
    meta_block, body = match.groups()
    meta = {}
    for line in meta_block.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, body


def _chunks(body: str) -> list[str]:
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    return paragraphs


def load_corpus() -> int:
    reset_db()
    session = SessionLocal()
    inserted = 0
    try:
        for path in sorted(_CORPUS_DIR.glob("*.md")):
            doc_id = path.stem
            raw = path.read_text(encoding="utf-8")
            meta, body = _parse_front_matter(raw)
            source_uri = meta.pop("sourceUri", f"kb/{doc_id}.md")

            session.execute(
                text("INSERT INTO documents (id, source_uri) VALUES (:id, :uri)"),
                {"id": doc_id, "uri": source_uri},
            )

            metadata = dict(meta)
            metadata["sourceUri"] = source_uri

            for index, chunk_text in enumerate(_chunks(body)):
                chunk_id = f"{doc_id}:{index}"
                vector = embed(chunk_text)
                vec_literal = "[" + ",".join(repr(v) for v in vector) + "]"
                session.execute(
                    text(
                        """
                        INSERT INTO chunks (id, document_id, chunk_index, text, metadata, embedding)
                        VALUES (:id, :doc_id, :idx, :text, CAST(:metadata AS jsonb), CAST(:vec AS vector))
                        """
                    ),
                    {
                        "id": chunk_id,
                        "doc_id": doc_id,
                        "idx": index,
                        "text": chunk_text,
                        "metadata": json.dumps(metadata),
                        "vec": vec_literal,
                    },
                )
                inserted += 1
        session.commit()
    finally:
        session.close()
    return inserted


if __name__ == "__main__":
    count = load_corpus()
    print(f"seeded {count} chunks")
