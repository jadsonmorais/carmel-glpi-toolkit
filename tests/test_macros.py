import pytest

from glpi_core.command_handler import CommandContext, available_commands, dispatch
from glpi_core.macros import apply_template, bulk_ops  # noqa: F401  (registram macros no dispatcher)


def test_macro_apply_template_to_project_esta_registrada():
    assert "apply_template_to_project" in available_commands()


def test_macro_bulk_ops_estao_registradas():
    assert "bulk_rename_tasks" in available_commands()
    assert "bulk_apply_dod" in available_commands()
    assert "bulk_tag_tasks" in available_commands()


def test_apply_template_to_project_cria_projeto_novo_a_partir_do_template(fake_client):
    fake_client.queue_response("POST", "Project", {"id": 256})
    fake_client.queue_response("GET", "Project/256", {"id": 256, "name": "Projeto 256", "entities_id": 1})

    # fases_padrao.json: 3 milestones + 5 fases (cada fase com tag Planejado)
    for milestone_id in (3001, 3002, 3003):
        fake_client.queue_response("POST", "ProjectTask", {"id": milestone_id})
        fake_client.queue_response(
            "GET",
            f"ProjectTask/{milestone_id}",
            {"id": milestone_id, "name": "Marco", "projects_id": 256, "is_milestone": 1},
        )

    for task_id in range(2740, 2745):
        fake_client.queue_response("POST", "ProjectTask", {"id": task_id})
        fake_client.queue_response(
            "GET",
            f"ProjectTask/{task_id}",
            {"id": task_id, "name": "F - Fase", "projects_id": 256, "content": "..."},
        )
        fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
        fake_client.queue_response("POST", "PluginTagTagItem", {"id": 9000 + task_id})

    ctx = CommandContext(fake_client)
    result = dispatch(
        "apply_template_to_project",
        {"template": "fases_padrao", "project_overrides": {"name": "Projeto 256"}},
        ctx,
    )

    assert result["project_id"] == 256
    assert len(result["created"]) == 8  # 3 milestones + 5 fases
    assert fake_client.calls[0][0:2] == ("POST", "Project")


def test_apply_template_to_project_com_project_id_nao_cria_project_novo(fake_client):
    fake_client.queue_response("GET", "Project/256", {"id": 256, "name": "Projeto 256", "entities_id": 1})

    for milestone_id in (3001, 3002, 3003):
        fake_client.queue_response("POST", "ProjectTask", {"id": milestone_id})
        fake_client.queue_response(
            "GET",
            f"ProjectTask/{milestone_id}",
            {"id": milestone_id, "name": "Marco", "projects_id": 256, "is_milestone": 1},
        )

    for task_id in range(2740, 2745):
        fake_client.queue_response("POST", "ProjectTask", {"id": task_id})
        fake_client.queue_response(
            "GET",
            f"ProjectTask/{task_id}",
            {"id": task_id, "name": "F - Fase", "projects_id": 256, "content": "..."},
        )
        fake_client.queue_response("GET", "PluginTagTag?range=0-999", [{"id": 50, "name": "Planejado"}])
        fake_client.queue_response("POST", "PluginTagTagItem", {"id": 9000 + task_id})

    ctx = CommandContext(fake_client)
    result = dispatch("apply_template_to_project", {"template": "fases_padrao", "project_id": 256}, ctx)

    assert result["project_id"] == 256
    assert ("POST", "Project") not in [(m, e) for m, e, _ in fake_client.calls]


def test_dispatch_comando_desconhecido_levanta_keyerror(fake_client):
    ctx = CommandContext(fake_client)
    with pytest.raises(KeyError):
        dispatch("comando_inexistente", {}, ctx)


def test_register_macro_duplicada_levanta_valueerror():
    from glpi_core.command_handler import register_macro

    @register_macro("macro_unica_de_teste")
    def _f(ctx, payload):
        return None

    with pytest.raises(ValueError):
        @register_macro("macro_unica_de_teste")
        def _g(ctx, payload):
            return None
