import pytest
from pydantic import ValidationError

from glpi_core.schemas.project import ProjectCreateSchema
from glpi_core.schemas.tag import TagAssignSchema, TaggableItemType
from glpi_core.schemas.task import DOD_BY_PHASE, TaskCreateSchema, TaskPhase, TaskReadSchema


def test_task_create_to_glpi_payload_minimo():
    schema = TaskCreateSchema(name="F1 - Teste", projects_id=256)
    assert schema.to_glpi_payload() == {
        "input": {"name": "F1 - Teste", "projects_id": 256, "is_milestone": 0}
    }


def test_task_create_to_glpi_payload_completo():
    schema = TaskCreateSchema(
        name="F2 - Config",
        projects_id=256,
        projecttasks_id=10,
        content="conteudo",
        is_milestone=True,
        plan_start_date="2026-01-01",
        plan_end_date="2026-01-10",
    )
    payload = schema.to_glpi_payload()["input"]
    assert payload["projecttasks_id"] == 10
    assert payload["content"] == "conteudo"
    assert payload["is_milestone"] == 1
    assert payload["plan_start_date"] == "2026-01-01"
    assert payload["plan_end_date"] == "2026-01-10"


def test_task_name_nao_pode_iniciar_com_caractere_especial():
    with pytest.raises(ValidationError):
        TaskCreateSchema(name="-invalido", projects_id=256)


def test_task_name_minimo_tres_caracteres():
    with pytest.raises(ValidationError):
        TaskCreateSchema(name="ab", projects_id=256)


@pytest.mark.parametrize("phase", list(TaskPhase))
def test_build_dod_block_para_cada_fase(phase):
    schema = TaskCreateSchema(name=f"F{phase.value} - Teste", projects_id=256, phase=phase)
    block = schema.build_dod_block()
    assert block.startswith("DEFINITION OF DONE:")
    for item in DOD_BY_PHASE[phase]:
        assert f"[ ] {item}" in block


def test_build_dod_block_vazio_sem_fase():
    schema = TaskCreateSchema(name="F1 - Teste", projects_id=256)
    assert schema.build_dod_block() == ""


def test_task_read_is_container():
    container = TaskReadSchema(id=1, name="F1", projects_id=256, projecttasks_id=None)
    leaf = TaskReadSchema(id=2, name="F1.1", projects_id=256, projecttasks_id=1)
    assert container.is_container is True
    assert leaf.is_container is False


def test_project_create_payload_so_inclui_campos_preenchidos():
    schema = ProjectCreateSchema(name="Projeto 256")
    payload = schema.to_glpi_payload()
    assert payload == {"input": {"name": "Projeto 256", "entities_id": 1}}


def test_tag_assign_schema_normaliza_itemtype_enum():
    schema = TagAssignSchema(itemtype="Ticket", items_id=27760, tag_id=204)
    assert schema.itemtype is TaggableItemType.TICKET


def test_tag_assign_schema_rejeita_itemtype_invalido():
    with pytest.raises(ValidationError):
        TagAssignSchema(itemtype="NotAType", items_id=1, tag_id=1)
