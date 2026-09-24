"""
Milvus vector store for Markdown RAG chunks (master prompt section 16).
Connects to the Docker Milvus standalone stack (+ etcd + MinIO) by
default, with Attu (http://localhost:3000) available to browse
collections and inspect stored vectors visually — the whole reason to
run the Docker path instead of the simpler, container-free Milvus Lite.
Point MILVUS_URI at a local file path instead to fall back to Lite; the
MilvusClient API is identical either way. The collection is dropped and
recreated on every startup, same as the rest of this project's ingestion
(editing content + restarting is the whole content-update workflow).
"""

import socket
from urllib.parse import urlparse

from pymilvus import DataType, MilvusClient

from backend.app.config import settings

COLLECTION_NAME = "markdown_chunks"

OUTPUT_FIELDS = [
    "chunk_id", "document_id", "text", "level",
    "full_context_path", "source_file", "chunk_index", "total_chunks",
]

_client: MilvusClient | None = None


def check_reachable(timeout_seconds: float = 3.0) -> None:
    """Fails fast with a clear message instead of pymilvus's own behavior,
    which is to hang rather than error out when Milvus isn't running —
    found this the hard way testing what happens if you start the app
    before `docker compose up -d`. A no-op for a Milvus Lite (local file)
    URI, which has nothing to reach over the network."""
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
    if client.has_collection(COLLECTION_NAME):
        client.drop_collection(COLLECTION_NAME)

    schema = client.create_schema(auto_id=False, enable_dynamic_field=True)
    schema.add_field("id", DataType.VARCHAR, is_primary=True, max_length=100)
    schema.add_field("vector", DataType.FLOAT_VECTOR, dim=settings.embedding_dim)

    index_params = client.prepare_index_params()
    # AUTOINDEX picks a reasonable default for Milvus Lite. Swap for tuned
    # HNSW params (M / efConstruction) once there's real data to benchmark
    # against — master prompt section 16 is explicit not to guess these.
    index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="IP")

    client.create_collection(collection_name=COLLECTION_NAME, schema=schema, index_params=index_params)


def insert_rows(rows: list[dict]) -> None:
    if not rows:
        return
    get_client().insert(collection_name=COLLECTION_NAME, data=rows)


def search(query_vector: list[float], top_k: int) -> list[dict]:
    client = get_client()
    if not client.has_collection(COLLECTION_NAME):
        return []

    results = client.search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        limit=top_k,
        output_fields=OUTPUT_FIELDS,
    )
    hits = results[0] if results else []
    return [{**hit["entity"], "vector_score": hit["distance"]} for hit in hits]
