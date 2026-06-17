import pytest

from glpi_core.schemas.governance import ApprovalMilestone, GovernanceTag, build_task_name


def test_build_task_name_monta_padrao_sistema_acao_contexto():
    name = build_task_name("POS/Simphony", "Instalar Workstation", "Restaurante")
    assert name == "[POS/Simphony] - Instalar Workstation - Restaurante"


def test_build_task_name_remove_espacos_extremos():
    name = build_task_name("  Opera PMS  ", " Atualização de Versão ", " Servidor Principal ")
    assert name == "[Opera PMS] - Atualização de Versão - Servidor Principal"


@pytest.mark.parametrize("campo", ["sistema_area", "acao_principal", "contexto_local"])
def test_build_task_name_rejeita_campo_vazio(campo):
    valores = {"sistema_area": "Opera PMS", "acao_principal": "Atualização", "contexto_local": "Servidor"}
    valores[campo] = "   "
    with pytest.raises(ValueError):
        build_task_name(**valores)


def test_governance_tag_valores_esperados():
    assert GovernanceTag.BREAK_FIX.value == "Break-Fix"
    assert GovernanceTag.PLANEJADO.value == "Planejado"
    assert GovernanceTag.PROJETO.value == "Projeto"
    assert GovernanceTag.BLOCKED.value == "Blocked"


def test_approval_milestone_ordem_dos_portoes():
    fases = [m.value for m in ApprovalMilestone]
    assert fases == ["Homologação Concluída", "Rollout Realizado", "Operação Assistida"]
