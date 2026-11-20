"""Parse an OpenAPI spec and load endpoint chunks into ChromaDB."""
import json
import hashlib
import httpx
import chromadb

COLLECTION_NAME = "openapi_endpoints"


def _chunk_endpoints(spec: dict) -> list[dict]:
    """Return one chunk per path+method with its schema flattened to text."""
    chunks = []
    base = spec.get("info", {})
    for path, methods in spec.get("paths", {}).items():
        for method, details in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            text = (
                f"API: {base.get('title', '')}\n"
                f"Endpoint: {method.upper()} {path}\n"
                f"Summary: {details.get('summary', '')}\n"
                f"Description: {details.get('description', '')}\n"
                f"Parameters: {json.dumps(details.get('parameters', []))}\n"
                f"Request body: {json.dumps(details.get('requestBody', {}))}\n"
                f"Responses: {json.dumps(details.get('responses', {}))}"
            )
            chunk_id = hashlib.md5(f"{method}{path}".encode()).hexdigest()
            chunks.append({"id": chunk_id, "text": text, "method": method.upper(), "path": path})
    return chunks


def ingest(spec_url: str, chroma_path: str = "./chroma_db") -> int:
    """Fetch spec from URL, chunk it, upsert into ChromaDB. Returns chunk count."""
    resp = httpx.get(spec_url, timeout=10)
    resp.raise_for_status()
    spec = resp.json()

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    chunks = _chunk_endpoints(spec)
    if not chunks:
        return 0

    collection.upsert(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"method": c["method"], "path": c["path"]} for c in chunks],
    )
    return len(chunks)


def retrieve(query: str, n: int = 3, chroma_path: str = "./chroma_db") -> list[str]:
    """Return the top-n relevant endpoint chunks for a query."""
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(COLLECTION_NAME)
    results = collection.query(query_texts=[query], n_results=min(n, collection.count()))
    return results["documents"][0] if results["documents"] else []
