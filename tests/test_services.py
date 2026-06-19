import pytest

from glpi_core.schemas.governance import GovernanceTag
from glpi_core.schemas.project import ProjectCreateSchema
from glpi_core.schemas.tag import TagAssignSchema, TaggableItemType
from glpi_core.schemas.task import TaskCreateSchema, TaskPhase
from glpi_core.services.project_service import ProjectService
from glpi_core.services.tag_service import TagService
from glpi_core.services.task_service import TaskService


def test_project_service_create_busca_recurso_apos_criar(fake_client):
    fake_client.queue_response("POST", "Project", {"id": 256})
    fake_client.queue_response("GET", "Project/256", {"id": 256, "name": "Projeto 256", "entities_id": 0})

    service = ProjectService(fake_client)
    project = service.create(ProjectCreateSchema(name="Projeto 256"))

    assert project.id == 256
    assert project.name == "Projeto 256"
    assert fake_client.calls[0][0:2] == ("POST", "Project")
    assert fake_client.calls[1][0:2] == ("GET", "Project/256")


def test_task_service_create_with_dod_injeta_checklist_no_content(fake_client):
    fake_client.queue_response("POST", "ProjectTask", {"id": 2740})
    fake_client.queue_response(
        "GET", "ProjectTask/2740", {"id": 2740, "name": "F1 - Teste", "projects_id": 256, "content": "..."}
    )

    service = TaskService(fake_client)
    schema = TaskCreateSchema(name="F1 - Teste", projects_id=256, phase=TaskPhase.F1)
    service.create_with_dod(schema)

    create_call = fake_client.calls[0]
    assert create_call[0:2] == ("POST", "ProjectTask")
    sent_content = create_call[2]["input"]["content"]
    assert sent_content.startswith("DEFINITION OF DONE:")


def test_task_service_create_with_dod_sem_fase_nao_envia_dod(fake_client):
    fake_client.queue_response("POST", "ProjectTask", {"id": 1})
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "Sem fase", "projects_id": 256})

    service = TaskService(fake_client)
    schema = TaskCreateSchema(name="Sem fase", projects_id=256)
    service.create_with_dod(schema)

    sent_input = fake_client.calls[0][2]["input"]
    assert "content" not in sent_input


def test_task_service_append_content_concatena_com_existente(fake_client):
    fake_client.queue_response("GET", "ProjectTask/5", {"id": 5, "name": "X", "projects_id": 1, "content": "base"})
    fake_client.queue_response("PUT", "ProjectTask/5", {"id": 5})
    fake_client.queue_response("GET", "ProjectTask/5", {"id": 5, "name": "X", "projects_id": 1, "content": "base\n\nextra"})

    service = TaskService(fake_client)
    result = service.append_content(5, "extra")

    put_call = fake_client.calls[1]
    assert put_call[0:2] == ("PUT", "ProjectTask/5")
    assert put_call[2]["input"]["content"] == "base\n\nextra"
    assert result.content == "base\n\nextra"


def test_tag_service_list_tags_filtra_por_nome(fake_client):
    fake_client.queue_response(
        "GET",
        "PluginTagTag?range=0-999",
        [{"id": 1, "name": "Analise"}, {"id": 2, "name": "Zabbix"}],
    )

    service = TagService(fake_client)
    result = service.list_tags(name_filter="zab")

    assert len(result) == 1
    assert result[0]["name"] == "Zabbix"


def test_tag_service_assign_monta_payload_correto(fake_client):
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 99})

    service = TagService(fake_client)
    schema = TagAssignSchema(itemtype="Ticket", items_id=27760, tag_id=204)
    result = service.assign(schema)

    sent = fake_client.calls[0][2]["input"]
    assert sent == {"itemtype": "Ticket", "items_id": 27760, "plugin_tag_tags_id": 204}
    assert result == {"id": 99}


def test_task_service_create_milestone_envia_is_milestone_1(fake_client):
    fake_client.queue_response("POST", "ProjectTask", {"id": 3001})
    fake_client.queue_response(
        "GET", "ProjectTask/3001", {"id": 3001, "name": "Homologação Concluída", "projects_id": 256, "is_milestone": 1}
    )

    service = TaskService(fake_client)
    milestone = service.create_milestone(256, "Homologação Concluída")

    sent_input = fake_client.calls[0][2]["input"]
    assert sent_input["is_milestone"] == 1
    assert milestone.is_milestone == 1


def test_tag_service_resolve_tag_id_encontra_por_nome_exato(fake_client):
    fake_client.queue_response(
        "GET",
        "PluginTagTag?range=0-999",
        [{"id": 10, "name": "Break-Fix"}, {"id": 11, "name": "Planejado"}],
    )

    service = TagService(fake_client)
    assert service.resolve_tag_id("Planejado") == 11


def test_tag_service_resolve_tag_id_levanta_erro_se_nao_existir(fake_client):
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 10, "name": "Break-Fix"}])

    service = TagService(fake_client)
    with pytest.raises(ValueError):
        service.resolve_tag_id("Inexistente")


def test_tag_service_assign_governance_tag_resolve_e_atribui(fake_client):
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 777})

    service = TagService(fake_client)
    result = service.assign_governance_tag(TaggableItemType.PROJECT_TASK, 2740, GovernanceTag.PLANEJADO)

    sent = fake_client.calls[1][2]["input"]
    assert sent == {"itemtype": "ProjectTask", "items_id": 2740, "plugin_tag_tags_id": 50}
    assert result == {"id": 777}


def test_tag_service_bulk_assign_governance_tag_resolve_id_uma_vez(fake_client):
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 1})
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 2})

    service = TagService(fake_client)
    results = service.bulk_assign_governance_tag(TaggableItemType.PROJECT_TASK, [10, 11], GovernanceTag.PLANEJADO)

    get_calls = [c for c in fake_client.calls if c[0] == "GET"]
    assert len(get_calls) == 1  # resolve_tag_id chamado so uma vez
    assert results == [{"id": 1}, {"id": 2}]


def test_task_service_bulk_rename_idempotente_pula_ja_prefixado(fake_client):
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "[Sistema] F1 - Ja prefixado", "projects_id": 256})
    fake_client.queue_response("GET", "ProjectTask/2", {"id": 2, "name": "F2 - Nao prefixado", "projects_id": 256})
    fake_client.queue_response("PUT", "ProjectTask/2", {"id": 2})
    fake_client.queue_response("GET", "ProjectTask/2", {"id": 2, "name": "[Sistema] F2 - Nao prefixado", "projects_id": 256})

    service = TaskService(fake_client)
    results = service.bulk_rename([1, 2], "[Sistema]")

    assert results[0].name == "[Sistema] F1 - Ja prefixado"  # nao reenviou PUT
    assert results[1].name == "[Sistema] F2 - Nao prefixado"
    put_calls = [c for c in fake_client.calls if c[0] == "PUT"]
    assert len(put_calls) == 1


def test_task_service_bulk_apply_dod_injeta_quando_phase_informada(fake_client):
    # 1a GET: checagem inicial em bulk_apply_dod; 2a GET: dentro de append_content (current);
    # 3a GET: dentro de append_content (apos o PUT).
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "F1 - Tarefa", "projects_id": 256, "content": "descricao"})
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "F1 - Tarefa", "projects_id": 256, "content": "descricao"})
    fake_client.queue_response("PUT", "ProjectTask/1", {"id": 1})
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "F1 - Tarefa", "projects_id": 256, "content": "descricao\n\nDEFINITION OF DONE:\n..."})

    service = TaskService(fake_client)
    result = service.bulk_apply_dod([1], phase=TaskPhase.F1)

    assert len(result["updated"]) == 1
    assert "DEFINITION OF DONE" in result["updated"][0].content


def test_task_service_bulk_apply_dod_pula_quando_ja_tem_checklist(fake_client):
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "F1 - Tarefa", "projects_id": 256, "content": "[ ] ja tem"})

    service = TaskService(fake_client)
    result = service.bulk_apply_dod([1], phase=TaskPhase.F1)

    put_calls = [c for c in fake_client.calls if c[0] == "PUT"]
    assert len(put_calls) == 0
    assert result["updated"] == []
    assert result["skipped"][0]["reason"] == "dod_already_present"


def test_task_service_discover_project_tasks_filtra_por_projects_id(fake_client):
    fake_client.queue_response("GET", "ProjectTask/10", {"id": 10, "name": "Pertence", "projects_id": 256})
    fake_client.queue_response("GET", "ProjectTask/11", {"id": 11, "name": "Outro projeto", "projects_id": 1})

    service = TaskService(fake_client)
    found = service.discover_project_tasks(256, (10, 11))

    assert [t.id for t in found] == [10]
