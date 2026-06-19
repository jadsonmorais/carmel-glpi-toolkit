"""Macros finas de operacao em massa sobre tarefas/tags ja existentes no GLPI.
Toda a logica vive em services/ (TaskService, TagService) — aqui so se valida o
payload e se despacha. Ver rules.md secao "Operacoes em massa".
"""
from __future__ import annotations

from glpi_core.command_handler import CommandContext, register_macro
from glpi_core.schemas.governance import GovernanceTag
from glpi_core.schemas.tag import TaggableItemType
from glpi_core.schemas.task import TaskPhase


@register_macro("bulk_rename_tasks")
def bulk_rename_tasks(ctx: CommandContext, payload: dict) -> dict:
    """payload: {"task_ids": [int, ...], "prefix": "[Sistema/Area]"}"""
    results = ctx.tasks.bulk_rename(payload["task_ids"], payload["prefix"])
    return {"renamed": [t.model_dump() for t in results]}


@register_macro("bulk_apply_dod")
def bulk_apply_dod(ctx: CommandContext, payload: dict) -> dict:
    """payload: {"task_ids": [int, ...], "phase": "1".."5" (opcional)}

    Se "project_id" e "id_range" vierem em vez de "task_ids", descobre as tarefas
    do projeto antes (ver TaskService.discover_project_tasks — necessario quando o
    projeto nao foi criado por este pacote, como o Projeto #256 real).
    """
    if "task_ids" in payload:
        task_ids = payload["task_ids"]
    else:
        discovered = ctx.tasks.discover_project_tasks(payload["project_id"], tuple(payload["id_range"]))
        task_ids = [t.id for t in discovered]

    phase = TaskPhase(payload["phase"]) if payload.get("phase") else None
    result = ctx.tasks.bulk_apply_dod(task_ids, phase=phase)
    return {
        "updated": [t.model_dump() for t in result["updated"]],
        "skipped": result["skipped"],
    }


@register_macro("bulk_tag_tasks")
def bulk_tag_tasks(ctx: CommandContext, payload: dict) -> dict:
    """payload: {"items_ids": [int, ...], "tag": "Planejado"|"Break-Fix"|"Projeto"|"Blocked",
    "itemtype": "ProjectTask" (opcional, default ProjectTask)}"""
    itemtype = TaggableItemType(payload.get("itemtype", "ProjectTask"))
    tag = GovernanceTag(payload["tag"])
    results = ctx.tags.bulk_assign_governance_tag(itemtype, payload["items_ids"], tag)
    return {"tagged": results}
