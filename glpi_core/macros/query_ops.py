"""Macros de consulta e visibilidade de projetos.

Trabalham em escopo de projeto (project_id + id_range), sem exigir que o caller
liste IDs de tarefas manualmente. Ver rules.md secao "Operacoes em massa".
"""
from __future__ import annotations

from glpi_core.command_handler import CommandContext, register_macro
from glpi_core.schemas.governance import GovernanceTag
from glpi_core.schemas.tag import TaggableItemType
from glpi_core.services.task_service import TaskService


def _parse_id_range(payload: dict) -> tuple[int, int]:
    r = payload["id_range"]
    return (int(r[0]), int(r[1]))


@register_macro("project_overview")
def project_overview(ctx: CommandContext, payload: dict) -> dict:
    """Retorna o estado atual de um projeto: tarefas por status, milestones pendentes,
    tarefas sem DoD e tarefas sem tag de governanca.

    payload: {"project_id": <int>, "id_range": [<start>, <end>]}
    """
    project_id = int(payload["project_id"])
    id_range = _parse_id_range(payload)

    tasks = ctx.tasks.discover_project_tasks(project_id, id_range)

    tasks_by_status: dict[str, list[dict]] = {}
    milestones_pending: list[str] = []
    tasks_missing_dod: list[dict] = []
    tasks_missing_tag: list[dict] = []
    tasks_blocked: list[dict] = []

    governance_tag_names = {tag.value for tag in GovernanceTag}

    for task in tasks:
        stub = {"id": task.id, "name": task.name}

        # agrupa por status (projectstates_id como proxy; None = sem status)
        status_key = str(task.projectstates_id) if task.projectstates_id else "sem_status"
        tasks_by_status.setdefault(status_key, []).append(stub)

        # milestones sem percent_done = 100 sao considerados pendentes
        if task.is_milestone and (task.percent_done or 0) < 100:
            milestones_pending.append(task.name)

        # tarefas leaf sem DoD
        if not task.is_milestone:
            content = task.content or ""
            if "[ ]" not in content and "[x]" not in content.lower():
                tasks_missing_dod.append(stub)

        # tarefas sem tag de governanca
        item_tags = ctx.tags.list_item_tags(TaggableItemType.PROJECT_TASK.value, task.id)
        tag_names = {t.get("name", "") for t in item_tags}
        if not tag_names.intersection(governance_tag_names):
            tasks_missing_tag.append(stub)

        # tarefas bloqueadas
        if any(t.get("name") == GovernanceTag.BLOCKED.value for t in item_tags):
            tasks_blocked.append(stub)

    return {
        "project_id": project_id,
        "tasks_total": len(tasks),
        "tasks_by_status": {k: v for k, v in tasks_by_status.items()},
        "milestones_pending": milestones_pending,
        "tasks_missing_dod": tasks_missing_dod,
        "tasks_missing_tag": tasks_missing_tag,
        "tasks_blocked": tasks_blocked,
    }


@register_macro("bulk_tag_project")
def bulk_tag_project(ctx: CommandContext, payload: dict) -> dict:
    """Atribui uma tag de governanca a todas as tarefas de um projeto.

    Nao exige listar IDs manualmente: descobre as tarefas pelo id_range.

    payload: {"project_id": <int>, "id_range": [<start>, <end>], "tag": "Planejado"|...}
    """
    project_id = int(payload["project_id"])
    id_range = _parse_id_range(payload)
    tag = GovernanceTag(payload["tag"])

    tasks = ctx.tasks.discover_project_tasks(project_id, id_range)
    task_ids = [t.id for t in tasks]
    results = ctx.tags.bulk_assign_governance_tag(TaggableItemType.PROJECT_TASK, task_ids, tag)
    return {"project_id": project_id, "tagged": len(results), "tag": tag.value}


@register_macro("bulk_apply_dod_to_project")
def bulk_apply_dod_to_project(ctx: CommandContext, payload: dict) -> dict:
    """Injeta DoD em todas as tarefas de um projeto que ainda nao tem checklist.

    A fase e inferida automaticamente pelo prefixo do nome da tarefa
    ("F<n>" ou "[Sistema] F<n>"). Tarefas cujo nome nao segue o padrao
    sao puladas com reason "phase_not_inferred".

    payload: {"project_id": <int>, "id_range": [<start>, <end>]}
    """
    project_id = int(payload["project_id"])
    id_range = _parse_id_range(payload)

    tasks = ctx.tasks.discover_project_tasks(project_id, id_range)

    updated: list[dict] = []
    skipped: list[dict] = []

    for task in tasks:
        if task.is_milestone:
            skipped.append({"id": task.id, "name": task.name, "reason": "is_milestone"})
            continue

        phase = TaskService.infer_phase_from_name(task.name)
        if phase is None:
            skipped.append({"id": task.id, "name": task.name, "reason": "phase_not_inferred"})
            continue

        result = ctx.tasks.bulk_apply_dod([task.id], phase=phase)
        updated.extend({"id": t.id, "name": t.name} for t in result["updated"])
        skipped.extend({"id": s["id"], "name": task.name, "reason": s["reason"]} for s in result["skipped"])

    return {
        "project_id": project_id,
        "updated": updated,
        "skipped": skipped,
    }
