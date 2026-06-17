from __future__ import annotations

from glpi_core.connection.client import GLPIClient
from glpi_core.schemas.project import ProjectCreateSchema, ProjectReadSchema


class ProjectService:
    def __init__(self, client: GLPIClient):
        self._client = client

    def create(self, schema: ProjectCreateSchema) -> ProjectReadSchema:
        raw = self._client.request("POST", "Project", schema.to_glpi_payload())
        return self.get(raw["id"])

    def get(self, project_id: int) -> ProjectReadSchema:
        raw = self._client.request("GET", f"Project/{project_id}")
        return ProjectReadSchema.model_validate(raw)
