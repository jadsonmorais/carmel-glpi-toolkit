from glpi_core.command_handler import CommandContext
from glpi_core.schemas.template import ProjectTemplateSchema, TaskTemplateNode
from glpi_core.services.template_service import TemplateService


def _simple_template() -> ProjectTemplateSchema:
    return ProjectTemplateSchema(
        template_name="teste",
        project_defaults={"name": "Projeto Teste"},
        nodes=[
            TaskTemplateNode(
                name="F1 - Fase",
                phase="1",
                tag="Planejado",
                children=[TaskTemplateNode(name="F1.1 - Subtarefa", phase="1", tag="Planejado")],
            )
        ],
    )


def test_apply_cria_project_quando_project_id_nao_informado(fake_client):
    fake_client.queue_response("POST", "Project", {"id": 100})
    fake_client.queue_response("GET", "Project/100", {"id": 100, "name": "Projeto Teste", "entities_id": 1})
    fake_client.queue_response("POST", "ProjectTask", {"id": 1})
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "F1 - Fase", "projects_id": 100})
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 900})
    fake_client.queue_response("POST", "ProjectTask", {"id": 2})
    fake_client.queue_response("GET", "ProjectTask/2", {"id": 2, "name": "F1.1 - Subtarefa", "projects_id": 100, "projecttasks_id": 1})
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 901})

    ctx = CommandContext(fake_client)
    service = TemplateService(ctx)
    result = service.apply(_simple_template(), project_id=None, project_overrides=None)

    assert result["project_id"] == 100
    assert fake_client.calls[0][0:2] == ("POST", "Project")
    assert [c["id"] for c in result["created"]] == [1, 2]
    assert result["created"][1]["parent_id"] == 1  # filho criado com parent = id do pai


def test_apply_reaproveita_project_existente_sem_criar_novo(fake_client):
    fake_client.queue_response("GET", "Project/256", {"id": 256, "name": "Projeto 256", "entities_id": 1})
    fake_client.queue_response("POST", "ProjectTask", {"id": 1})
    fake_client.queue_response("GET", "ProjectTask/1", {"id": 1, "name": "F1 - Fase", "projects_id": 256})
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 900})
    fake_client.queue_response("POST", "ProjectTask", {"id": 2})
    fake_client.queue_response("GET", "ProjectTask/2", {"id": 2, "name": "F1.1 - Subtarefa", "projects_id": 256, "projecttasks_id": 1})
    fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
    fake_client.queue_response("POST", "PluginTagTagItem", {"id": 901})

    ctx = CommandContext(fake_client)
    service = TemplateService(ctx)
    result = service.apply(_simple_template(), project_id=256, project_overrides=None)

    assert result["project_id"] == 256
    assert ("POST", "Project") not in [(m, e) for m, e, _ in fake_client.calls]
