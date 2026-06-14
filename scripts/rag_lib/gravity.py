"""
Calcula o gravity score de um ticket: 0.0 – 100.0.
Vai além dos campos numéricos do GLPI (urgencia/prioridade 1-5)
incorporando idle_days, ausência de técnico, projetos travados e
keywords de alto impacto operacional.
"""

from datetime import datetime

IMPACT_KEYWORDS = [
    # Urgência operacional
    "indicador", "urgente", "prazo", "sla", "crítico", "critico",
    "indisponível", "indisponivel", "falha total", "parado", "bloqueado", "escalado",
    # Impacto humano/negócio
    "cliente", "reclamação", "reclamacao", "insatisfeito", "gestão", "gestao",
    "diretoria", "reunião", "reuniao", "apresentação", "apresentacao",
    # Tempo
    "meses", "sem retorno", "sem resposta",
    # Técnico
    "integração", "integracao", "nota fiscal",
    # Impacto financeiro
    "producao", "produção",
]

PROJECT_KEYWORDS = [
    "tornou-se um projeto",
    "virou projeto",
    "escalado para projeto",
    "convertido em projeto",
    "se tornará um projeto",
    "demanda de projeto",
    "fora do escopo do chamado",
]


def is_projeto_travado(text: str) -> bool:
    tl = text.lower()
    return any(kw in tl for kw in PROJECT_KEYWORDS)


def compute_idle_days(ultima_atualizacao: str) -> int:
    """Aceita 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS'. Retorna 0 se inválido."""
    if not ultima_atualizacao:
        return 0
    try:
        date_str = ultima_atualizacao[:10]
        last = datetime.strptime(date_str, "%Y-%m-%d")
        return max(0, (datetime.now() - last).days)
    except ValueError:
        return 0


def count_impact_keywords(text: str) -> int:
    tl = text.lower()
    return sum(1 for kw in IMPACT_KEYWORDS if kw in tl)


def compute_gravity(
    idle_days: int,
    urgencia: int,
    prioridade: int,
    sem_tecnico: bool,
    is_projeto: bool,
    texto_completo: str,
) -> float:
    """
    Retorna score 0.0–100.0.

    Componentes:
      idle_component    — até 40pts (idle_days * 0.12, cap 40)
      urgency_component — até 20pts (urgencia*0.6 + prioridade*0.4) * 4
      no_tech_component — 15pts se sem técnico atribuído
      project_component — 20pts se identificado como projeto travado
      keyword_component — até 5pts por keywords de alto impacto
    """
    idle_component = min(40.0, idle_days * 0.12)

    urgency_raw = (urgencia * 0.6) + (prioridade * 0.4)
    urgency_component = urgency_raw * 4.0

    no_tech_component = 15.0 if sem_tecnico else 0.0
    project_component = 20.0 if is_projeto else 0.0

    kw_count = count_impact_keywords(texto_completo)
    keyword_component = min(5.0, float(kw_count))

    total = idle_component + urgency_component + no_tech_component + project_component + keyword_component
    return round(min(100.0, total), 2)
