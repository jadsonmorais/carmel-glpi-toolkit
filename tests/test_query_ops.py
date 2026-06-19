"""Testes das macros de consulta e visibilidade de projetos (query_ops)."""
from __future__ import annotations

import pytest

from glpi_core.command_handler import CommandContext, dispatch
from glpi_core.macros import query_ops  # noqa: F401 — registra os comandos
from glpi_core.services.task_service import TaskService
from glpi_core.schemas.task import TaskPhase
from tests.conftest import FakeGLPIClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _task(id: int, name: str, projects_id: int = 1, is_milestone: int = 0,
          content: str | None = None, percent_done: int | None = None,
          projectstates_id: int | None = None) -> dict:
    return {
        "id": id,
        "name": name,
        "projects_id": projects_id,
        "is_milestone": is_milestone,
        "content": content,
        "percent_done": percent_done,
        "projectstates_id": projectstates_id,
    }


def _queue_task_discovery(client: FakeGLPIClient, project_id: int,
                           tasks: list[dict], id_range: tuple[int, int]) -> None:
    """Programa respostas para discover_project_tasks: GET para cada ID no range."""
    from glpi_core.connection.client import GLPIRequestError
    task_map = {t["id"]: t for t in tasks}
    for i in range(id_range[0], id_range[1] + 1):
        if i in task_map:
            client.queue_response("GET", f"ProjectTask/{i}", task_map[i])
        else:
            client.queue_response("GET", f"ProjectTask/{i}", {"id": i, "projects_id": 0, "name": ""})


# ---------------------------------------------------------------------------
# infer_phase_from_name
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("F1 - Levantamento", TaskPhase.F1),
    ("F3 - Definicao Tecnica", TaskPhase.F3),
    ("[POS/Simphony] F2 - Inventario", TaskPhase.F2),
    ("[Infra] F4.1 - Executar mudanca", TaskPhase.F4),
    ("Homologacao Concluida", None),          # milestone sem prefixo F
    ("Tarefa sem fase", None),
    ("F9 - Fase inexistente", None),           # fase fora do enum (1-5)
])
def test_infer_phase_from_name(name, expected):
    assert TaskService.infer_phase_from_name(name) == expected


# ---------------------------------------------------------------------------
# project_overview
# ---------------------------------------------------------------------------

def test_project_overview_basic(fake_client: FakeGLPIClient):
    project_id = 1
    id_range = (10, 12)

    tasks = [
        _task(10, "F1 - Levantamento", project_id, content="[ ] item", projectstates_id=1),
        _task(11, "F2 - Planejamento", project_id, content=None, projectstates_id=2),
        _task(12, "Marco de Aprovacao", project_id, is_milestone=1, percent_done=0),
    ]
    _queue_task_discovery(fake_client, project_id, tasks, id_range)

    # list_item_tags para cada tarefa: task 10 tem tag Planejado, demais nao tem
    fake_client.queue_response("GET", "ProjectTask/10/PluginTagTagItem", [{"name": "Planejado"}])
    fake_client.queue_response("GET", "ProjectTask/11/PluginTagTagItem", [])
    fake_client.queue_response("GET", "ProjectTask/12/PluginTagTagItem", [])

    ctx = CommandContext(fake_client)
    result = dispatch("project_overview", {"project_id": project_id, "id_range": list(id_range)}, ctx)

    assert result["tasks_total"] == 3
    assert result["milestones_pending"] == ["Marco de Aprovacao"]
    # task 11 nao tem DoD
    assert any(t["id"] == 11 for t in result["tasks_missing_dod"])
    # task 10 tem DoD ([ ] item), nao deve estar em missing_dod
    assert all(t["id"] != 10 for t in result["tasks_missing_dod"])
    # tasks 11 e 12 nao tem tag de governanca
    missing_tag_ids = {t["id"] for t in result["tasks_missing_tag"]}
    assert 11 in missing_tag_ids
    assert 12 in missing_tag_ids
    assert 10 not in missing_tag_ids


# ---------------------------------------------------------------------------
# bulk_tag_project
# ---------------------------------------------------------------------------

def test_bulk_tag_project(fake_client: FakeGLPIClient):
    project_id = 1
    id_range = (20, 21)

    tasks = [
        _task(20, "F1 - Tarefa A", project_id),
        _task(21, "F2 - Tarefa B", project_id),
    ]
    _queue_task_discovery(fake_client, project_id, tasks, id_range)

    # resolve_tag_id busca lista de tags
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 5, "name": "Planejado"}])
    # assign para cada tarefa
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 100})
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 101})

    ctx = CommandContext(fake_client)
    result = dispatch("bulk_tag_project", {
        "project_id": project_id,
        "id_range": list(id_range),
        "tag": "Planejado",
    }, ctx)

    assert result["tagged"] == 2
    assert result["tag"] == "Planejado"


# ---------------------------------------------------------------------------
# bulk_apply_dod_to_project
# ---------------------------------------------------------------------------

def test_bulk_apply_dod_to_project_updates_leaf_tasks(fake_client: FakeGLPIClient):
    project_id = 1
    id_range = (30, 32)

    tasks = [
        _task(30, "F1 - Levantamento", project_id, content=None),
        _task(31, "F2 - Planejamento", project_id, content="[ ] ja tem dod"),
        _task(32, "Marco Aprovacao", project_id, is_milestone=1),
    ]
    _queue_task_discovery(fake_client, project_id, tasks, id_range)

    task_30_updated = {**tasks[0], "content": "DEFINITION OF DONE:\n[ ] Anexar evidencia"}
    # Para cada tarefa leaf, bulk_apply_dod chama get() antes de decidir o que fazer.
    # Tarefa 30: GET (verificar) + GET (append_content.get) + PUT + GET (retorno) = 3 GETs
    # Tarefa 31: GET (verificar content — ja tem DoD, para por aqui)
    # Tarefa 32: milestone, interceptada antes de chegar em bulk_apply_dod
    fake_client.queue_response("GET", "ProjectTask/30", tasks[0])        # bulk_apply_dod.get()
    fake_client.queue_response("GET", "ProjectTask/30", tasks[0])        # append_content.get()
    fake_client.queue_response("PUT", "ProjectTask/30", {"id": 30})
    fake_client.queue_response("GET", "ProjectTask/30", task_30_updated) # append_content retorno
    fake_client.queue_response("GET", "ProjectTask/31", tasks[1])        # bulk_apply_dod.get() — skipped

    ctx = CommandContext(fake_client)
    result = dispatch("bulk_apply_dod_to_project", {
        "project_id": project_id,
        "id_range": list(id_range),
    }, ctx)

    updated_ids = {t["id"] for t in result["updated"]}
    skipped_reasons = {s["id"]: s["reason"] for s in result["skipped"]}

    assert 30 in updated_ids
    assert skipped_reasons.get(31) == "dod_already_present"
    assert skipped_reasons.get(32) == "is_milestone"


def test_bulk_apply_dod_to_project_skips_uninferred_phase(fake_client: FakeGLPIClient):
    project_id = 1
    id_range = (40, 40)

    tasks = [_task(40, "Tarefa sem padrao de fase", project_id, content=None)]
    _queue_task_discovery(fake_client, project_id, tasks, id_range)

    ctx = CommandContext(fake_client)
    result = dispatch("bulk_apply_dod_to_project", {
        "project_id": project_id,
        "id_range": list(id_range),
    }, ctx)

    assert result["updated"] == []
    assert result["skipped"][0]["reason"] == "phase_not_inferred"
