"""Repositorio de templates JSON: carrega e valida arquivos de glpi_core/templates/*.json
contra ProjectTemplateSchema. Ver glpi_core/rules.md secao "Templates".
"""
from __future__ import annotations

import json
import os

from glpi_core.schemas.template import ProjectTemplateSchema

_TEMPLATES_DIR = os.path.dirname(os.path.abspath(__file__))


class TemplateRepository:
    @staticmethod
    def load(name: str) -> ProjectTemplateSchema:
        """Carrega e valida um template pelo nome (sem extensao .json)."""
        path = os.path.join(_TEMPLATES_DIR, f"{name}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"template '{name}' nao encontrado em {_TEMPLATES_DIR}. "
                f"Disponiveis: {TemplateRepository.list_available()}"
            )
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return ProjectTemplateSchema.model_validate(raw)

    @staticmethod
    def list_available() -> list[str]:
        return sorted(
            os.path.splitext(f)[0]
            for f in os.listdir(_TEMPLATES_DIR)
            if f.endswith(".json")
        )
