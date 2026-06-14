"""
Gera os chunks de texto e metadados a partir de um TicketData.
Cada ticket produz 2 chunks: context e timeline.
"""

from .parser import TicketData
from .gravity import compute_idle_days, is_projeto_travado, compute_gravity

SEM_TECNICO_VALUES = {"não atribuído", "nao atribuido", "none", ""}

_SERVICOS_PREFIXES = ("servi", "serví")


def _extrair_sistema(categoria: str) -> str:
    """
    Extrai o sistema principal da categoria hierárquica.
    "Serviços de Sistemas > Opera > Cloud PMS" → "Opera"
    "Impressora > Falha" → "Impressora"
    """
    parts = [p.strip() for p in categoria.split(">")]
    if len(parts) >= 2 and any(parts[0].lower().startswith(p) for p in _SERVICOS_PREFIXES):
        return parts[1]
    return parts[0] if parts else ""


def build_chunks(ticket: TicketData) -> list[tuple[str, dict]]:
    """
    Retorna [(texto_para_embedding, metadados_dict), ...].
    Sempre produz 2 chunks: {id}_context e {id}_timeline.
    """
    idle_days = compute_idle_days(ticket.ultima_atualizacao)
    sem_tecnico = ticket.tecnico.strip().lower() in SEM_TECNICO_VALUES

    texto_completo = " ".join(filter(None, [
        ticket.resumo, ticket.contexto, ticket.decisoes,
        ticket.bloqueios, ticket.proximos_passos, ticket.timeline_text,
    ]))

    is_projeto = is_projeto_travado(texto_completo)
    gravity = compute_gravity(
        idle_days, ticket.urgencia, ticket.prioridade,
        sem_tecnico, is_projeto, texto_completo,
    )

    base_meta = {
        # Identificação
        "ticket_id": ticket.ticket_id,
        # Metadados GLPI
        "status": ticket.status,
        "localizacao": ticket.localizacao,
        "requerente": ticket.requerente,
        "tecnico": ticket.tecnico or "Não atribuído",
        "categoria": ticket.categoria,
        "sistema": _extrair_sistema(ticket.categoria),
        "tipo_ticket": ticket.tipo_ticket,
        "grupo_requerente": ticket.grupo_requerente,
        "urgencia": ticket.urgencia,
        "prioridade": ticket.prioridade,
        "data_abertura": ticket.data_abertura,
        "ultima_atualizacao": ticket.ultima_atualizacao,
        # Métricas calculadas
        "idle_days": idle_days,
        "sem_tecnico": sem_tecnico,
        "is_projeto": is_projeto,
        "gravity_score": gravity,
        "num_interacoes": ticket.timeline_text.count("- **"),
        "tem_solucao": bool(ticket.decisoes.strip()),
        "tem_bloqueio": bool(ticket.bloqueios.strip()),
    }

    context_parts = [f"Chamado #{ticket.ticket_id} — {ticket.categoria}"]
    if ticket.status or ticket.localizacao:
        context_parts.append(
            f"Status: {ticket.status} | Local: {ticket.localizacao} | Técnico: {ticket.tecnico or 'Não atribuído'}"
        )
    for label, value in [
        ("Resumo", ticket.resumo),
        ("Contexto", ticket.contexto),
        ("Decisões Técnicas", ticket.decisoes),
        ("Bloqueios", ticket.bloqueios),
        ("Próximos Passos", ticket.proximos_passos),
    ]:
        if value.strip():
            context_parts.append(f"\n{label}:\n{value}")

    context_text = "\n".join(context_parts)

    timeline_header = f"Chamado #{ticket.ticket_id} — histórico de interações:"
    timeline_text = f"{timeline_header}\n{ticket.timeline_text}" if ticket.timeline_text else timeline_header

    return [
        (context_text, {**base_meta, "chunk_type": "context"}),
        (timeline_text, {**base_meta, "chunk_type": "timeline"}),
    ]
