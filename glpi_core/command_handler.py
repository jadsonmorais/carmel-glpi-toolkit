"""Dispatcher de comandos: recebe um nome de macro + payload bruto e executa de forma previsivel."""
from __future__ import annotations

from typing import Any, Callable

from glpi_core.connection.client import GLPIClient
from glpi_core.services.project_service import ProjectService
from glpi_core.services.tag_service import TagService
from glpi_core.services.task_service import TaskService
from glpi_core.services.template_service import TemplateService


class CommandContext:
    """Agrega os services disponiveis para uma macro."""

    def __init__(self, client: GLPIClient):
        self.client = client
        self.projects = ProjectService(client)
        self.tasks = TaskService(client)
        self.tags = TagService(client)
        self.templates = TemplateService(self)


_REGISTRY: dict[str, Callable[[CommandContext, dict], Any]] = {}


def register_macro(command_name: str):
    """Decorator para registrar uma macro no dispatcher. Ver rules.md p/ convencao de nomes."""

    def wrapper(fn: Callable[[CommandContext, dict], Any]):
        if command_name in _REGISTRY:
            raise ValueError(f"comando '{command_name}' ja registrado")
        _REGISTRY[command_name] = fn
        return fn

    return wrapper


def dispatch(command_name: str, payload: dict, ctx: CommandContext) -> Any:
    """Ponto unico de entrada: recebe nome do comando + payload bruto, valida e executa."""
    if command_name not in _REGISTRY:
        raise KeyError(f"comando desconhecido: '{command_name}'. Disponiveis: {sorted(_REGISTRY)}")
    return _REGISTRY[command_name](ctx, payload)


def available_commands() -> list[str]:
    return sorted(_REGISTRY)
