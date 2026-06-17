"""Macro generica: aplica um template JSON (glpi_core/templates/*.json) criando a
arvore de ProjectTasks descrita, num Project novo ou num Project ja existente.
Substitui macros hardcoded por projeto (ex.: o antigo apply_macro_projeto_256_fases_1_a_5).
"""
from __future__ import annotations

from glpi_core.command_handler import CommandContext, register_macro
from glpi_core.templates import TemplateRepository


@register_macro("apply_template_to_project")
def apply_template_to_project(ctx: CommandContext, payload: dict) -> dict:
    """
    payload esperado:
        {"template": "<nome do arquivo .json em glpi_core/templates/, sem extensao>",
         "project_id": <int, opcional>,        # aplica a arvore dentro de um projeto ja existente
         "project_overrides": {<campos de ProjectCreateSchema>, opcional}}  # so usado se project_id nao vier

    Determinístico: mesmo template + mesmos overrides/project_id -> mesma sequencia de chamadas.
    """
    template = TemplateRepository.load(payload["template"])
    return ctx.templates.apply(
        template,
        project_id=payload.get("project_id"),
        project_overrides=payload.get("project_overrides"),
    )
