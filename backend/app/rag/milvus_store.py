"""
Milvus vector store for the whole knowledge base (master prompt section 16).

One collection holds BOTH sources, the same way the replica project does:
  source_type = "markdown"  one vector per Markdown chunk
  source_type = "excel"     one vector per curated Q&A question / question variation
Every field is declared in the schema (no hidden dynamic `$meta` column), so
Attu (http://localhost:3001) shows real columns — text, source file, section,
Q&A id — and the row count is correct because inserts are flushed.

Connects to the Docker Milvus standalone stack (+ etcd + MinIO). Point
MILVUS_URI at a local file path instead to fall back to Milvus Lite; the
MilvusClient API is identical either way. The collection is dropped and
recreated on every startup (editing content + restarting is the whole
content-update workflow).
"""

import socket
from urllib.parse import urlparse

from pymilvus import DataType, MilvusClient

from backend.app.config import settings

COLLECTION_NAME = "ptc_knowledge"
LEGACY_COLLECTIONS = ("markdown_chunks",)

TEXT_MAX_CHARS = 16000

OUTPUT_FIELDS = [
    "chunk_id", "source_type", "source_file", "level", "full_context_path",
    "qa_id", "question", "text", "chunk_index", "total_chunks",
]

_client: MilvusClient | None = None


def check_reachable(timeout_seconds: float = 3.0) -> None:
    """Fails fast with a clear message instead of pymilvus's own behavior,
    which is to hang rather than error out when Milvus isn't running. A no-op
    for a Milvus Lite (local file) URI, which has nothing to reach."""
    parsed = urlparse(settings.milvus_uri)
    if not parsed.hostname or not parsed.port:
        return

    try:
        with socket.create_connection((parsed.hostname, parsed.port), timeout=timeout_seconds):
            return
    except OSError as exc:
        raise RuntimeError(
            f"Can't reach Milvus at {settings.milvus_uri}. "
            "Start this project's Docker containers first: `docker compose up -d`, "
            "wait ~30-60s for them to report healthy (`docker ps`), then start the app again."
        ) from exc


def get_client() -> MilvusClient:
    global _client
    if _client is None:
        check_reachable()
        _client = MilvusClient(settings.milvus_uri)
    return _client


def reset_collection() -> None:
    client = get_client()
    for name in (COLLECTION_NAME, *LEGACY_COLLECTIONS):
        if client.has_collection(name):
            client.drop_collection(name)

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=120)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=settings.embedding_dim)
    schema.add_field("source_type", DataType.VARCHAR, max_length=20)
    schema.add_field("chunk_id", DataType.VARCHAR, max_length=120)
    schema.add_field("source_file", DataType.VARCHAR, max_length=300)
    schema.add_field("level", DataType.VARCHAR, max_length=120)
    schema.add_field("full_context_path", DataType.VARCHAR, max_length=1000)
    schema.add_field("qa_id", DataType.VARCHAR, max_length=50)
    schema.add_field("question", DataType.VARCHAR, max_length=1000)
    schema.add_field("text", DataType.VARCHAR, max_length=TEXT_MAX_CHARS)
    schema.add_field("chunk_index", DataType.INT64)
    schema.add_field("total_chunks", DataType.INT64)

    index_params = client.prepare_index_params()
    # AUTOINDEX picks a reasonable default. Swap for tuned HNSW params once
    # there's real data to benchmark against (master prompt section 16).
    index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="IP")

    client.create_collection(collection_name=COLLECTION_NAME, schema=schema, index_params=index_params)


def insert_rows(rows: list[dict]) -> None:
    if not rows:
        return
    client = get_client()
    for row in rows:
        row["text"] = row["text"][:TEXT_MAX_CHARS]
        row["question"] = row["question"][:1000]
        row["full_context_path"] = row["full_context_path"][:1000]
    client.insert(collection_name=COLLECTION_NAME, data=rows)
    client.flush(collection_name=COLLECTION_NAME)


def search(query_vector: list[float], top_k: int, source_type: str | None = None) -> list[dict]:
    client = get_client()
    if not client.has_collection(COLLECTION_NAME):
        return []

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        limit=top_k,
        filter=f'source_type == "{source_type}"' if source_type else "",
        output_fields=OUTPUT_FIELDS,
    )
    hits = results[0] if results else []
    return [{**hit["entity"], "vector_score": hit["distance"]} for hit in hits]
