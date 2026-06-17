"""Tipos de governanca: tags de escopo, marcos de aprovacao e padrao de nomenclatura.

Ver rules.md para o racional completo. Resumo:
- GovernanceTag separa incidente (Break-Fix) de evolucao (Planejado/Projeto) e
  marca impedimentos (Blocked), para nao misturar fila/SLA de suporte com projeto.
- ApprovalMilestone sao os "portoes" que dao visibilidade executiva sem precisar
  investigar tarefa por tarefa.
- build_task_name padroniza o titulo de tarefas no formato
  "[Sistema/Area] - Acao Principal - Contexto/Local".
"""
from __future__ import annotations

from enum import Enum


class GovernanceTag(str, Enum):
    BREAK_FIX = "Break-Fix"       # suporte reativo, concorre na fila/SLA de incidente
    PLANEJADO = "Planejado"       # entrega de engenharia/evolucao, fora da fila de incidente
    PROJETO = "Projeto"           # mesmo espirito de PLANEJADO, usado quando ja existe Project no GLPI
    BLOCKED = "Blocked"           # impedimento por dependencia externa (fornecedor, acesso etc.)


class ApprovalMilestone(str, Enum):
    HOMOLOGACAO_CONCLUIDA = "Homologação Concluída"
    ROLLOUT_REALIZADO = "Rollout Realizado"
    OPERACAO_ASSISTIDA = "Operação Assistida"


def build_task_name(sistema_area: str, acao_principal: str, contexto_local: str) -> str:
    """Monta o titulo de tarefa no padrao "[Sistema/Area] - Acao Principal - Contexto/Local".

    Ex: build_task_name("POS/Simphony", "Instalar Workstation", "Restaurante")
        -> "[POS/Simphony] - Instalar Workstation - Restaurante"
    """
    for label, value in (("sistema_area", sistema_area), ("acao_principal", acao_principal), ("contexto_local", contexto_local)):
        if not value or not value.strip():
            raise ValueError(f"{label} nao pode ser vazio")
    return f"[{sistema_area.strip()}] - {acao_principal.strip()} - {contexto_local.strip()}"
