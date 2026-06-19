from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from glpi_core.schemas.project import ProjectCreateSchema
from glpi_core.schemas.tag import TaggableItemType
from glpi_core.schemas.template import ProjectTemplateSchema, TaskTemplateNode

if TYPE_CHECKING:
    from glpi_core.services.project_service import ProjectService
    from glpi_core.services.tag_service import TagService
    from glpi_core.services.task_service import TaskService


class TemplateService:
    """Aplica um ProjectTemplateSchema: cria (ou reaproveita) um Project e cria a
    arvore de ProjectTasks descrita pelo template, pai antes de filho, injetando
    DoD e atribuindo tags conforme cada no.
    """

    def __init__(self, projects: "ProjectService", tasks: "TaskService", tags: "TagService"):
        self._projects = projects
        self._tasks = tasks
        self._tags = tags

    def apply(
        self,
        template: ProjectTemplateSchema,
        *,
        project_id: Optional[int] = None,
        project_overrides: Optional[dict] = None,
    ) -> dict:
        if project_id is not None:
            project = self._projects.get(project_id)
        else:
            defaults = dict(template.project_defaults or {})
            defaults.update(project_overrides or {})
            project_schema = ProjectCreateSchema(**defaults)
            project = self._projects.create(project_schema)

        created: list[dict] = []
        for node in template.nodes:
            self._apply_node(node, projects_id=project.id, parent_id=None, created=created)

        return {"project_id": project.id, "created": created}

    def _apply_node(self, node: TaskTemplateNode, *, projects_id: int, parent_id: Optional[int], created: list[dict]) -> None:
        schema = node.to_task_create_schema(projects_id, parent_id)
        if node.is_milestone:
            task = self._tasks.create_milestone(projects_id, schema.name, parent_id=parent_id)
        else:
            task = self._tasks.create_with_dod(schema)

        if node.tag is not None:
            self._tags.assign_governance_tag(TaggableItemType.PROJECT_TASK, task.id, node.tag)

        created.append({"id": task.id, "name": task.name, "parent_id": parent_id})

        for child in node.children:
            self._apply_node(child, projects_id=projects_id, parent_id=task.id, created=created)
