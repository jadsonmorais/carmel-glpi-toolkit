from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TaskPhase(str, Enum):
    F1 = "1"
    F2 = "2"
    F3 = "3"
    F4 = "4"
    F5 = "5"


# Definition of Done por fase. Ver rules.md para o fluxo de adicionar/alterar fases.
DOD_BY_PHASE: dict[TaskPhase, list[str]] = {
    TaskPhase.F1: [
        "Anexar evidência (print/export do GLPI ou log) confirmando a execução",
        "Responsável e data registrados",
    ],
    TaskPhase.F2: [
        "Anexar evidência (print/export do GLPI ou log) confirmando a execução",
        "Responsável e data registrados",
    ],
    TaskPhase.F3: [
        "Documento de definição aprovado anexado",
        "Validação registrada com o responsável",
    ],
    TaskPhase.F4: [
        "Log/print do teste funcional anexado",
        "Horário e responsável da execução registrados",
    ],
    TaskPhase.F5: [
        "Artigo de KB publicado / trilha disponibilizada",
        "Link do artigo/trilha anexado",
    ],
}

# Campos graváveis de ProjectTask na API GLPI (fora de name/content/is_milestone/
# projects_id/projecttasks_id, já tratados separadamente). Ver glpi_core/rules.md
# secao "Campos suportados".
_WRITABLE_OPTIONAL_FIELDS = (
    "comment",
    "percent_done",
    "auto_percent_done",
    "plan_start_date",
    "plan_end_date",
    "real_start_date",
    "real_end_date",
    "planned_duration",
    "projectstates_id",
    "projecttasktypes_id",
    "projecttasktemplates_id",
    "users_id",
    "entities_id",
    "is_recursive",
    "is_template",
    "template_name",
)


class TaskCreateSchema(BaseModel):
    """Payload validado para criacao de uma ProjectTask no GLPI.

    Cobre todos os campos graváveis reais da API (levantados via GET ProjectTask/{id}
    numa instância real) — campos somente-leitura (id, date_creation, date_mod, uuid,
    links) ficam de fora e só aparecem em TaskReadSchema.
    """
    name: str = Field(..., min_length=3, max_length=255)
    projects_id: int
    projecttasks_id: Optional[int] = None
    phase: Optional[TaskPhase] = None
    content: Optional[str] = None
    is_milestone: bool = False

    comment: Optional[str] = None
    percent_done: Optional[int] = None
    auto_percent_done: Optional[int] = None
    plan_start_date: Optional[str] = None
    plan_end_date: Optional[str] = None
    real_start_date: Optional[str] = None
    real_end_date: Optional[str] = None
    planned_duration: Optional[int] = None
    projectstates_id: Optional[int] = None
    projecttasktypes_id: Optional[int] = None
    projecttasktemplates_id: Optional[int] = None
    users_id: Optional[int] = None
    entities_id: Optional[int] = None
    is_recursive: Optional[bool] = None
    is_template: Optional[bool] = None
    template_name: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_must_follow_convention(cls, v: str) -> str:
        if not v[:1].isalnum():
            raise ValueError("nome de tarefa nao pode iniciar com caractere especial")
        return v

    def to_glpi_payload(self) -> dict:
        payload = {
            "name": self.name,
            "projects_id": self.projects_id,
            "is_milestone": int(self.is_milestone),
        }
        if self.projecttasks_id:
            payload["projecttasks_id"] = self.projecttasks_id
        if self.content:
            payload["content"] = self.content
        for field in _WRITABLE_OPTIONAL_FIELDS:
            value = getattr(self, field)
            if value is None:
                continue
            payload[field] = int(value) if isinstance(value, bool) else value
        return {"input": payload}

    def build_dod_block(self) -> str:
        if not self.phase:
            return ""
        items = DOD_BY_PHASE[self.phase]
        checklist = "\n".join(f"[ ] {i}" for i in items)
        return f"DEFINITION OF DONE:\n{checklist}"


class TaskReadSchema(BaseModel):
    """Espelha o retorno da API GLPI para uma ProjectTask (campos relevantes)."""
    id: int
    name: str
    projects_id: int
    projecttasks_id: Optional[int] = None
    is_milestone: int = 0
    content: Optional[str] = None
    comment: Optional[str] = None
    percent_done: Optional[int] = None
    auto_percent_done: Optional[int] = None
    plan_start_date: Optional[str] = None
    plan_end_date: Optional[str] = None
    real_start_date: Optional[str] = None
    real_end_date: Optional[str] = None
    planned_duration: Optional[int] = None
    projectstates_id: Optional[int] = None
    projecttasktypes_id: Optional[int] = None
    users_id: Optional[int] = None
    entities_id: Optional[int] = None

    @property
    def is_container(self) -> bool:
        return self.projecttasks_id is None
