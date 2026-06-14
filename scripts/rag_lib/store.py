"""
Interface com ChromaDB — armazenamento e busca vetorial local.
Usa PersistentClient (API >= 0.4) com espaço cosine.
"""


def get_chroma_client(vectordb_path: str):
    try:
        import chromadb
    except ImportError:
        raise ImportError(
            "chromadb não instalado. Execute:\n"
            "  pip install chromadb"
        )
    return chromadb.PersistentClient(path=vectordb_path)


class ChromaStore:
    COLLECTION_NAME = "verdanadesk_tickets"

    def __init__(self, vectordb_path: str):
        self.client = get_chroma_client(vectordb_path)
        self.col = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunk_id: str, text: str, embedding: list[float], metadata: dict):
        """Insere ou atualiza um chunk pelo ID."""
        self.col.upsert(
            ids=[chunk_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
        )

    def upsert_batch(self, chunk_ids: list[str], texts: list[str],
                     embeddings: list[list[float]], metadatas: list[dict]):
        """Upsert em lote — muito mais rápido que chamadas individuais."""
        self.col.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

    def delete_ticket(self, ticket_id: str):
        """Remove os 2 chunks de um ticket pelo ticket_id nos metadados."""
        self.col.delete(where={"ticket_id": {"$eq": ticket_id}})

    def query(
        self,
        query_embedding: list[float],
        n_results: int = 10,
        where: dict = None,
    ) -> dict:
        """
        Busca os n_results mais próximos do query_embedding.
        where: filtro de metadados no formato ChromaDB (ex: {"chunk_type": {"$eq": "context"}})
        """
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, self.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        return self.col.query(**kwargs)

    def get_all_ticket_ids(self) -> set[str]:
        """Retorna todos os ticket_ids presentes no índice."""
        result = self.col.get(include=["metadatas"])
        return {m["ticket_id"] for m in result["metadatas"]}

    def delete_all(self):
        """Apaga toda a coleção e recria."""
        self.client.delete_collection(self.COLLECTION_NAME)
        self.col = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def count(self) -> int:
        """Número total de chunks indexados."""
        return self.col.count()
