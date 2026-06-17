"""Schemas de template: descrevem uma arvore de ProjectTasks (e opcionalmente um
Project) em JSON, para serem aplicados pela macro generica `apply_template_to_project`
em vez de macros Python hardcoded por projeto. Ver glpi_core/rules.md secao "Templates".
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from glpi_core.schemas.governance import GovernanceTag
from glpi_core.schemas.task import TaskCreateSchema, TaskPhase

# Campos espelhados 1:1 de TaskCreateSchema (alem de name/content/is_milestone/phase/tag/children).
_MIRRORED_TASK_FIELDS = (
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


class TaskTemplateNode(BaseModel):
    """Um no da arvore de tarefas de um template. Pode ter filhos (subtarefas)."""

    name: str = Field(..., min_length=3, max_length=255)
    content: Optional[str] = None
    comment: Optional[str] = None
    is_milestone: bool = False
    phase: Optional[TaskPhase] = None
    tag: Optional[GovernanceTag] = None

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

    children: list["TaskTemplateNode"] = Field(default_factory=list)

    def to_task_create_schema(self, projects_id: int, parent_id: Optional[int]) -> TaskCreateSchema:
        """Mapeia este no para o schema usado por TaskService, atrelado ao projeto/pai dados."""
        fields = {f: getattr(self, f) for f in _MIRRORED_TASK_FIELDS if getattr(self, f) is not None}
        return TaskCreateSchema(
            name=self.name,
            projects_id=projects_id,
            projecttasks_id=parent_id,
            phase=self.phase,
            content=self.content,
            is_milestone=self.is_milestone,
            **fields,
        )


TaskTemplateNode.model_rebuild()


class ProjectTemplateSchema(BaseModel):
    """Template completo: metadados + arvore de tarefas a aplicar."""

    template_name: str = Field(..., min_length=1)
    description: Optional[str] = None
    project_defaults: Optional[dict] = None
    nodes: list[TaskTemplateNode] = Field(default_factory=list)
