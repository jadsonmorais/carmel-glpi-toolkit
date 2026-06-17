from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

# Campos graváveis de Project na API GLPI (fora de name/content/entities_id, já
# tratados separadamente). Ver glpi_core/rules.md secao "Campos suportados".
_WRITABLE_OPTIONAL_FIELDS = (
    "comment",
    "code",
    "priority",
    "percent_done",
    "auto_percent_done",
    "plan_start_date",
    "plan_end_date",
    "real_start_date",
    "real_end_date",
    "projectstates_id",
    "projecttypes_id",
    "projecttemplates_id",
    "users_id",
    "groups_id",
    "is_recursive",
    "is_template",
    "show_on_global_gantt",
    "template_name",
)


class ProjectCreateSchema(BaseModel):
    """Payload validado para criacao de um Project no GLPI.

    Cobre todos os campos graváveis reais da API (levantados via GET Project/{id}
    numa instância real) — campos somente-leitura (id, date, date_creation,
    date_mod, is_deleted, links) ficam de fora e só aparecem em ProjectReadSchema.
    """
    name: str = Field(..., min_length=3, max_length=255)
    content: Optional[str] = None
    entities_id: int = 1  # entidade "TI" — perfil ativo so tem direito de escrita aqui, nao na raiz (0)

    comment: Optional[str] = None
    code: Optional[str] = None
    priority: Optional[int] = None
    percent_done: Optional[int] = None
    auto_percent_done: Optional[int] = None
    plan_start_date: Optional[str] = None
    plan_end_date: Optional[str] = None
    real_start_date: Optional[str] = None
    real_end_date: Optional[str] = None
    projectstates_id: Optional[int] = None
    projecttypes_id: Optional[int] = None
    projecttemplates_id: Optional[int] = None
    users_id: Optional[int] = None
    groups_id: Optional[int] = None
    is_recursive: Optional[bool] = None
    is_template: Optional[bool] = None
    show_on_global_gantt: Optional[bool] = None
    template_name: Optional[str] = None

    def to_glpi_payload(self) -> dict:
        payload = {"name": self.name, "entities_id": self.entities_id}
        if self.content:
            payload["content"] = self.content
        for field in _WRITABLE_OPTIONAL_FIELDS:
            value = getattr(self, field)
            if value is None:
                continue
            payload[field] = int(value) if isinstance(value, bool) else value
        return {"input": payload}


class ProjectReadSchema(BaseModel):
    """Espelha o retorno da API GLPI para um Project (campos relevantes)."""
    id: int
    name: str
    content: Optional[str] = None
    entities_id: int = 0
    comment: Optional[str] = None
    code: Optional[str] = None
    priority: Optional[int] = None
    percent_done: Optional[int] = None
    auto_percent_done: Optional[int] = None
    plan_start_date: Optional[str] = None
    plan_end_date: Optional[str] = None
    real_start_date: Optional[str] = None
    real_end_date: Optional[str] = None
    projectstates_id: Optional[int] = None
    projecttypes_id: Optional[int] = None
    users_id: Optional[int] = None
    groups_id: Optional[int] = None
