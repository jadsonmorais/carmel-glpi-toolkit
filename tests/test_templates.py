from glpi_core.schemas.template import ProjectTemplateSchema, TaskTemplateNode
from glpi_core.templates import TemplateRepository


def _count_nodes(nodes: list[TaskTemplateNode]) -> int:
    total = 0
    for node in nodes:
        total += 1 + _count_nodes(node.children)
    return total


def test_list_available_inclui_os_dois_templates_de_partida():
    available = TemplateRepository.list_available()
    assert "fases_padrao" in available
    assert "simphony_pos_rollout" in available


def test_fases_padrao_tem_3_milestones_e_5_fases():
    template = TemplateRepository.load("fases_padrao")
    assert isinstance(template, ProjectTemplateSchema)
    milestones = [n for n in template.nodes if n.is_milestone]
    fases = [n for n in template.nodes if n.phase is not None]
    assert len(milestones) == 3
    assert len(fases) == 5


def test_simphony_pos_rollout_reconstroi_arvore_esperada():
    template = TemplateRepository.load("simphony_pos_rollout")
    assert len(template.nodes) == 5  # F1..F5 no nivel raiz
    total = _count_nodes(template.nodes)
    assert total == 40  # 37 tarefas originais + 3 marcos de portao (F4.G1, F4.G2, F5.G1)


def test_template_inexistente_levanta_filenotfounderror():
    import pytest

    with pytest.raises(FileNotFoundError):
        TemplateRepository.load("nao_existe")
