"""
Constrói/atualiza o índice vetorial ChromaDB a partir dos .md de tickets.

Uso:
    py scripts/rag-build.py                    # indexa apenas novos/modificados
    py scripts/rag-build.py --rebuild          # apaga tudo e reindexa todos
    py scripts/rag-build.py --ticket 15099     # reindexar 1 ticket específico
    py scripts/rag-build.py --stats            # mostra estatísticas do índice
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from _env import BASE_DIR

VECTORDB_PATH = os.path.join(BASE_DIR, "vectordb")


def index_ticket(filepath: str, store, force: bool = False) -> bool:
    """
    Indexa um ticket. Retorna True se indexou, False se já estava atualizado.
    """
    from rag_lib.parser import parse_ticket_md
    from rag_lib.chunker import build_chunks
    from rag_lib.embedder import embed_batch

    ticket = parse_ticket_md(filepath)
    if ticket is None:
        return False

    if not force:
        existing = store.get_all_ticket_ids()
        if ticket.ticket_id in existing:
            return False

    store.delete_ticket(ticket.ticket_id)
    chunks = build_chunks(ticket)
    texts = [c[0] for c in chunks]
    metas = [c[1] for c in chunks]
    embeddings = embed_batch(texts)

    chunk_ids = [f"{ticket.ticket_id}_{m['chunk_type']}" for m in metas]
    store.upsert_batch(chunk_ids, texts, embeddings, metas)
    return True


def main():
    parser = argparse.ArgumentParser(description="Constrói índice RAG dos chamados VerdanaDesk")
    parser.add_argument("--rebuild", action="store_true",
                        help="Apaga o índice existente e reindexa todos os tickets")
    parser.add_argument("--ticket", nargs="+", metavar="ID",
                        help="Reindexar ticket(s) específico(s) pelo ID")
    parser.add_argument("--stats", action="store_true",
                        help="Exibe estatísticas do índice atual e sai")
    args = parser.parse_args()

    from rag_lib.store import ChromaStore
    store = ChromaStore(VECTORDB_PATH)

    if args.stats:
        total = store.count()
        tickets = store.get_all_ticket_ids()
        print(f"[RAG] Índice em: {VECTORDB_PATH}")
        print(f"[RAG] Chunks indexados: {total}")
        print(f"[RAG] Tickets distintos: {len(tickets)}")
        return

    if args.rebuild:
        print("[RAG] Modo --rebuild: apagando índice existente...")
        store.delete_all()

    if args.ticket:
        # Reindexar ticket(s) específico(s)
        for tid in args.ticket:
            filepath = os.path.join(BASE_DIR, f"{tid}.md")
            if not os.path.exists(filepath):
                print(f"[RAG] Ticket {tid} não encontrado em {BASE_DIR}")
                continue
            result = index_ticket(filepath, store, force=True)
            if result:
                print(f"[RAG] #{tid} reindexado.")
        return

    # Indexação incremental (ou completa se --rebuild)
    md_files = [
        f for f in os.listdir(BASE_DIR)
        if f.endswith(".md") and f.replace(".md", "").isdigit()
    ]

    total = len(md_files)
    indexados = 0
    ignorados = 0

    print(f"[RAG] {total} tickets encontrados em {BASE_DIR}")

    for filename in sorted(md_files):
        filepath = os.path.join(BASE_DIR, filename)
        result = index_ticket(filepath, store, force=args.rebuild)
        if result:
            indexados += 1
            if indexados % 20 == 0:
                print(f"[RAG] {indexados}/{total} indexados...")
        else:
            ignorados += 1

    print(f"\n[RAG] Concluído. Indexados: {indexados} | Já presentes: {ignorados}")
    print(f"[RAG] Total de chunks no índice: {store.count()}")


if __name__ == "__main__":
    main()
