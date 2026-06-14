"""
Parseia arquivos .md de tickets gerados pelo incremental-update.py.
Extrai campos estruturados de metadados e seções de conteúdo.
"""

import re
import os
from dataclasses import dataclass, field
from typing import Optional

SKIP_FILES = {
    "index.md", "insights.md", "plano-de-acao.md", "plano-sem-tecnico.md",
    "chamados-parados-detalhado.md", "chamados-antigos-detalhado.md",
    "chamados-projetos-detalhado.md",
}


@dataclass
class TicketData:
    ticket_id: str
    status: str = ""
    localizacao: str = ""
    requerente: str = ""
    tecnico: str = ""
    data_abertura: str = ""
    ultima_atualizacao: str = ""
    urgencia: int = 3
    prioridade: int = 3
    categoria: str = ""
    tipo_ticket: str = ""
    grupo_requerente: str = ""
    resumo: str = ""
    contexto: str = ""
    participantes: str = ""
    decisoes: str = ""
    bloqueios: str = ""
    proximos_passos: str = ""
    timeline_text: str = ""


def _extract_section(lines: list[str], header: str) -> str:
    """Extrai texto entre um header ## e o próximo header ##."""
    collecting = False
    result = []
    header_norm = header.lower().strip()
    for line in lines:
        if line.startswith("## "):
            current = line[3:].lower().strip()
            if current == header_norm:
                collecting = True
                continue
            elif collecting:
                break
        elif collecting:
            result.append(line)
    return "\n".join(result).strip()


def _parse_metadata_table(lines: list[str]) -> dict:
    """Extrai campos da tabela de metadados."""
    meta = {}
    in_meta = False
    for line in lines:
        if line.startswith("## Metadados"):
            in_meta = True
            continue
        if in_meta and line.startswith("## "):
            break
        if in_meta and line.startswith("|") and "|" in line[1:]:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3 and parts[1] not in ("Campo", "-----"):
                key = parts[1]
                value = parts[2] if len(parts) > 2 else ""
                meta[key] = value
    return meta


def parse_ticket_md(filepath: str) -> Optional[TicketData]:
    """
    Lê um .md de ticket e retorna TicketData.
    Retorna None para arquivos de controle/síntese.
    """
    filename = os.path.basename(filepath)
    if filename in SKIP_FILES or not filename.endswith(".md"):
        return None

    # Só processa se o nome do arquivo for numérico (ID do ticket)
    ticket_id = filename.replace(".md", "")
    if not ticket_id.isdigit():
        return None

    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    lines = content.splitlines()
    meta = _parse_metadata_table(lines)

    def safe_int(val: str, default: int = 3) -> int:
        try:
            return int(str(val).strip())
        except (ValueError, TypeError):
            return default

    ticket = TicketData(
        ticket_id=ticket_id,
        status=meta.get("Status", ""),
        localizacao=meta.get("Localização", meta.get("Localizacao", "")),
        requerente=meta.get("Requerente", ""),
        tecnico=meta.get("Técnico Atribuído", meta.get("Tecnico Atribuido", "")),
        data_abertura=(meta.get("Data de Abertura", "") or "")[:10],
        ultima_atualizacao=(meta.get("Última Atualização GLPI", meta.get("Ultima Atualizacao GLPI", "")) or "")[:10],
        urgencia=safe_int(meta.get("Urgência", meta.get("Urgencia", "3"))),
        prioridade=safe_int(meta.get("Prioridade", "3")),
        categoria=meta.get("Categoria", ""),
        tipo_ticket=meta.get("Tipo de Chamado", ""),
        grupo_requerente=meta.get("Grupo Requerente", ""),
        resumo=_extract_section(lines, "Resumo Executivo"),
        contexto=_extract_section(lines, "Contexto do Negócio"),
        participantes=_extract_section(lines, "Participantes"),
        decisoes=_extract_section(lines, "Decisões Técnicas"),
        bloqueios=_extract_section(lines, "Bloqueios & Dependências"),
        proximos_passos=_extract_section(lines, "Próximos Passos / Status Atual"),
        timeline_text=_extract_section(lines, "Linha do Tempo"),
    )

    # Limpar placeholders genéricos
    placeholders = {"*(extrair das interações conforme necessário)*", "*(registrar se identificados nas interações)*"}
    for attr in ("decisoes", "bloqueios", "proximos_passos"):
        val = getattr(ticket, attr).lower().strip()
        if val in placeholders:
            setattr(ticket, attr, "")

    return ticket
