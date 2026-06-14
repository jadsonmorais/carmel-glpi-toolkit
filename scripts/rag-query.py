"""
Interface CLI de consulta RAG para chamados VerdanaDesk.

Modos:
  similar  (padrão) — busca semântica pura
  history            — foca em tickets resolvidos/fechados (como foi resolvido antes?)
  gravity            — ranking por gravidade real (semântica + gravity_score)
  dedup              — detecta duplicatas e tickets similares

Uso:
    py scripts/rag-query.py "planilha Oracle indicador governança"
    py scripts/rag-query.py "Opera PMS upselling" --mode history
    py scripts/rag-query.py "projetos sem responsável" --mode gravity --top 5
    py scripts/rag-query.py --ticket 15099 --mode dedup
    py scripts/rag-query.py "Opera" --local "Carmel Cumbuco" --status "Pendente"
    py scripts/rag-query.py --ticket 27630 --mode dedup --threshold 0.70
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(__file__))
from _env import BASE_DIR, GLPI_TICKET_URL

VECTORDB_PATH = os.path.join(BASE_DIR, "vectordb")


# ---------------------------------------------------------------------------
# Helpers de output
# ---------------------------------------------------------------------------

def _similarity_label(distance: float) -> str:
    """Converte distância cosine (0=idêntico, 2=oposto) em score 0-1."""
    score = 1 - (distance / 2)
    return f"{score:.3f}"


def _status_flags(meta: dict) -> str:
    flags = []
    if meta.get("sem_tecnico"):
        flags.append("SEM TÉCNICO")
    if meta.get("is_projeto"):
        flags.append("PROJETO")
    return f"  [{', '.join(flags)}]" if flags else ""


def _print_result(rank: int, meta: dict, distance: float, doc: str, show_doc: bool = True):
    tid = meta.get("ticket_id", "?")
    gravity = meta.get("gravity_score", 0)
    idle = meta.get("idle_days", 0)
    status = meta.get("status", "")
    local = meta.get("localizacao", "")
    cat = meta.get("categoria", "")
    tecnico = meta.get("tecnico", "")
    sim = _similarity_label(distance)
    flags = _status_flags(meta)

    print(f"\n{'─'*60}")
    print(f"  #{rank}  Ticket #{tid}   Similaridade: {sim}   Gravity: {gravity:.1f}{flags}")
    print(f"       Status: {status} | Local: {local} | Idle: {idle}d")
    print(f"       Técnico: {tecnico}")
    print(f"       Categoria: {cat}")
    print(f"       GLPI: {GLPI_TICKET_URL}{tid}")
    if show_doc and doc:
        # Mostrar primeiras 3 linhas não vazias do documento
        lines = [l for l in doc.splitlines() if l.strip()][:4]
        print(f"\n       {'  '.join(lines[:1])}")
        for line in lines[1:]:
            print(f"       {line}")


# ---------------------------------------------------------------------------
# Modos de query
# ---------------------------------------------------------------------------

def _build_where(args) -> dict | None:
    """Constrói filtro de metadados a partir de flags CLI."""
    conditions = []
    if args.local:
        conditions.append({"localizacao": {"$eq": args.local}})
    if args.status:
        conditions.append({"status": {"$eq": args.status}})
    if args.tecnico:
        conditions.append({"tecnico": {"$eq": args.tecnico}})
    if getattr(args, "sistema", None):
        conditions.append({"sistema": {"$eq": args.sistema}})
    if getattr(args, "requerente", None):
        conditions.append({"requerente": {"$eq": args.requerente}})
    if getattr(args, "tipo", None):
        conditions.append({"tipo_ticket": {"$eq": args.tipo}})
    if getattr(args, "grupo", None):
        conditions.append({"grupo_requerente": {"$eq": args.grupo}})
    if getattr(args, "com_solucao", False):
        conditions.append({"tem_solucao": {"$eq": True}})
    if getattr(args, "com_bloqueio", False):
        conditions.append({"tem_bloqueio": {"$eq": True}})
    if not conditions:
        return None
    return {"$and": conditions} if len(conditions) > 1 else conditions[0]


def query_similar(query_text: str, store, n: int, where: dict | None):
    """Busca semântica pura, deduplica por ticket_id, prioriza chunk context."""
    from rag_lib.embedder import embed

    q_emb = embed(query_text)

    # Busca context chunks primeiro
    context_where = {"chunk_type": {"$eq": "context"}}
    if where:
        context_where = {"$and": [context_where, where]}

    results = store.query(q_emb, n_results=n * 2, where=context_where)

    print(f"\n[RAG] Modo: similar | Query: \"{query_text}\"")
    if where:
        print(f"[RAG] Filtros: {where}")
    print(f"[RAG] Top {n} resultados:\n")

    seen = set()
    rank = 0
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        tid = meta.get("ticket_id")
        if tid in seen:
            continue
        seen.add(tid)
        rank += 1
        _print_result(rank, meta, dist, doc)
        if rank >= n:
            break


def query_history(query_text: str, store, n: int, where: dict | None):
    """Busca em tickets resolvidos/fechados — como o problema foi resolvido antes?"""
    from rag_lib.embedder import embed

    q_emb = embed(query_text)

    resolved_statuses = ["2 - Resolvido", "5 - Solucionado", "6 - Fechado", "Fechado", "Solucionado"]
    status_filter = {"status": {"$in": resolved_statuses}}
    context_filter = {"chunk_type": {"$eq": "context"}}
    history_where = {"$and": [context_filter, status_filter]}
    if where:
        history_where["$and"].append(where)

    results = store.query(q_emb, n_results=n * 2, where=history_where)

    print(f"\n[RAG] Modo: history | Query: \"{query_text}\"")
    print(f"[RAG] Buscando em tickets resolvidos/fechados...\n")

    seen = set()
    rank = 0
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    if not docs:
        print("[RAG] Nenhum ticket resolvido encontrado para esta query.")
        print("      Dica: a maioria dos 164 tickets está aberta. Tente --mode similar.")
        return

    for doc, meta, dist in zip(docs, metas, dists):
        tid = meta.get("ticket_id")
        if tid in seen:
            continue
        seen.add(tid)
        rank += 1
        _print_result(rank, meta, dist, doc)
        if rank >= n:
            break


def query_gravity(query_text: str, store, n: int, where: dict | None):
    """
    Ranking por gravidade real: combina similaridade semântica com gravity_score.
    Score final = 0.5 * similarity + 0.5 * (gravity / 100)
    """
    from rag_lib.embedder import embed

    q_emb = embed(query_text)

    context_where = {"chunk_type": {"$eq": "context"}}
    if where:
        context_where = {"$and": [context_where, where]}

    # Busca mais candidatos para o reranking
    results = store.query(q_emb, n_results=min(50, store.count()), where=context_where)

    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    # Reranking
    scored = []
    seen = set()
    for doc, meta, dist in zip(docs, metas, dists):
        tid = meta.get("ticket_id")
        if tid in seen:
            continue
        seen.add(tid)
        similarity = 1 - (dist / 2)
        gravity_norm = meta.get("gravity_score", 0) / 100
        final_score = 0.5 * similarity + 0.5 * gravity_norm
        scored.append((final_score, dist, meta, doc))

    scored.sort(key=lambda x: x[0], reverse=True)

    print(f"\n[RAG] Modo: gravity | Query: \"{query_text}\"")
    print(f"[RAG] Reranking por: 50% similaridade + 50% gravity_score\n")
    print(f"  {'Rank':<5} {'Ticket':<8} {'Score Final':<13} {'Gravity':<10} {'Sim':<8} {'Idle':<7} {'Flags'}")
    print(f"  {'─'*4} {'─'*7} {'─'*12} {'─'*9} {'─'*7} {'─'*6} {'─'*20}")

    for rank, (final_score, dist, meta, doc) in enumerate(scored[:n], 1):
        tid = meta.get("ticket_id", "?")
        gravity = meta.get("gravity_score", 0)
        idle = meta.get("idle_days", 0)
        sim = 1 - (dist / 2)
        flags = _status_flags(meta).strip()
        print(f"  {rank:<5} #{tid:<7} {final_score:.3f}        {gravity:<10.1f} {sim:<8.3f} {idle:<7} {flags}")

    print()
    # Detalhes dos top 3
    for rank, (final_score, dist, meta, doc) in enumerate(scored[:min(3, n)], 1):
        _print_result(rank, meta, dist, doc, show_doc=True)


def query_dedup(query_text: str, store, threshold: float, n: int, ticket_id: str | None):
    """
    Detecta duplicatas/tickets similares acima do threshold de similaridade cosine.
    Se --ticket for fornecido, usa o texto do ticket como query.
    """
    from rag_lib.embedder import embed
    from rag_lib.parser import parse_ticket_md

    # Se foi passado um ticket_id, usa seu contexto como query
    if ticket_id:
        filepath = os.path.join(BASE_DIR, f"{ticket_id}.md")
        if os.path.exists(filepath):
            ticket = parse_ticket_md(filepath)
            if ticket:
                query_text = f"{ticket.resumo} {ticket.contexto}"[:500]
                print(f"\n[RAG] Modo: dedup | Ticket base: #{ticket_id}")
                print(f"[RAG] Threshold: {threshold} | Buscando tickets similares...\n")
            else:
                print(f"[RAG] Não foi possível parsear #{ticket_id}")
                return
        else:
            print(f"[RAG] Ticket #{ticket_id} não encontrado.")
            return
    else:
        print(f"\n[RAG] Modo: dedup | Query: \"{query_text}\"")
        print(f"[RAG] Threshold: {threshold}\n")

    q_emb = embed(query_text)
    context_where = {"chunk_type": {"$eq": "context"}}
    results = store.query(q_emb, n_results=min(30, store.count()), where=context_where)

    docs  = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0]

    matches = []
    for doc, meta, dist in zip(docs, metas, dists):
        tid = meta.get("ticket_id")
        if ticket_id and tid == ticket_id:
            continue  # não comparar consigo mesmo
        similarity = 1 - (dist / 2)
        if similarity >= threshold:
            matches.append((similarity, meta, doc))

    if not matches:
        print(f"[RAG] Nenhum ticket com similaridade >= {threshold} encontrado.")
        return

    print(f"[RAG] {len(matches)} ticket(s) com similaridade >= {threshold}:\n")
    for rank, (sim, meta, doc) in enumerate(matches[:n], 1):
        dist_equiv = (1 - sim) * 2
        _print_result(rank, meta, dist_equiv, doc)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="RAG de chamados VerdanaDesk — busca semântica e análise de gravidade",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", nargs="?", default="",
                        help="Texto da busca (opcional se --ticket for usado)")
    parser.add_argument("--mode", choices=["similar", "history", "gravity", "dedup"],
                        default="similar", help="Modo de busca (padrão: similar)")
    parser.add_argument("--ticket", metavar="ID",
                        help="ID do ticket para usar como query (útil para dedup)")
    parser.add_argument("--top", type=int, default=5,
                        help="Número de resultados (padrão: 5)")
    parser.add_argument("--threshold", type=float, default=0.75,
                        help="Threshold de similaridade para modo dedup (padrão: 0.75)")
    parser.add_argument("--local", metavar="LOCAL",
                        help="Filtrar por localização (ex: 'Carmel Cumbuco')")
    parser.add_argument("--status", metavar="STATUS",
                        help="Filtrar por status (ex: '4 - Pendente')")
    parser.add_argument("--tecnico", metavar="NOME",
                        help="Filtrar por técnico atribuído")
    parser.add_argument("--sistema", metavar="SISTEMA",
                        help="Filtrar por sistema (ex: 'Opera', 'CMFlex', 'Impressora')")
    parser.add_argument("--requerente", metavar="NOME",
                        help="Filtrar por requerente (ex: 'Sara Bacelar')")
    parser.add_argument("--tipo", metavar="TIPO",
                        help="Filtrar por tipo (ex: 'Incidente', 'Requisição')")
    parser.add_argument("--grupo", metavar="GRUPO",
                        help="Filtrar por grupo requerente (ex: 'Recepcao', 'Governança')")
    parser.add_argument("--com-solucao", action="store_true",
                        help="Apenas tickets com Decisões Técnicas preenchidas")
    parser.add_argument("--com-bloqueio", action="store_true",
                        help="Apenas tickets com Bloqueios documentados")
    args = parser.parse_args()

    if not args.query and not args.ticket:
        parser.error("Informe uma query ou use --ticket ID")

    from rag_lib.store import ChromaStore
    store = ChromaStore(VECTORDB_PATH)

    if store.count() == 0:
        print("[RAG] Índice vazio. Execute primeiro:")
        print("      py scripts/rag-build.py --rebuild")
        sys.exit(1)

    where = _build_where(args)

    if args.mode == "similar":
        query_text = args.query or ""
        if args.ticket and not query_text:
            # Carregar texto do ticket como query
            from rag_lib.parser import parse_ticket_md
            fp = os.path.join(BASE_DIR, f"{args.ticket}.md")
            t = parse_ticket_md(fp) if os.path.exists(fp) else None
            if t:
                query_text = f"{t.resumo} {t.contexto}"[:500]
        query_similar(query_text, store, args.top, where)

    elif args.mode == "history":
        query_history(args.query, store, args.top, where)

    elif args.mode == "gravity":
        query_gravity(args.query or "tickets críticos parados sem resolução", store, args.top, where)

    elif args.mode == "dedup":
        query_dedup(args.query, store, args.threshold, args.top, args.ticket)


if __name__ == "__main__":
    main()
