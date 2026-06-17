from __future__ import annotations

from typing import Optional

from glpi_core.schemas.task import TaskCreateSchema, TaskPhase, TaskReadSchema

# Prefixos de nomenclatura ja aplicados (idempotencia em bulk_rename). Ver rules.md.
_PHASE_NAME_RE = __import__("re").compile(r"^F\d+(\.\d+)*\s*-\s*.+")


class TaskService:
    def __init__(self, client):
        self._client = client

    def create(self, schema: TaskCreateSchema) -> TaskReadSchema:
        """Cria a ProjectTask exatamente como veio no schema, sem injetar DoD."""
        raw = self._client.request("POST", "ProjectTask", schema.to_glpi_payload())
        return self.get(raw["id"])

    def create_with_dod(self, schema: TaskCreateSchema) -> TaskReadSchema:
        """Cria a ProjectTask injetando o checklist de DoD da fase no content."""
        dod_block = schema.build_dod_block()
        if dod_block:
            schema.content = f"{schema.content}\n\n{dod_block}" if schema.content else dod_block
        return self.create(schema)

    def create_milestone(self, projects_id: int, name: str, parent_id: Optional[int] = None) -> TaskReadSchema:
        """Cria uma ProjectTask marcada como milestone — portao de aprovacao, sem DoD."""
        schema = TaskCreateSchema(
            name=name, projects_id=projects_id, is_milestone=True, projecttasks_id=parent_id
        )
        return self.create(schema)

    def get(self, task_id: int) -> TaskReadSchema:
        raw = self._client.request("GET", f"ProjectTask/{task_id}")
        return TaskReadSchema.model_validate(raw)

    def append_content(self, task_id: int, extra_content: str) -> TaskReadSchema:
        current = self.get(task_id)
        new_content = f"{current.content}\n\n{extra_content}" if current.content else extra_content
        self._client.request("PUT", f"ProjectTask/{task_id}", {"input": {"id": task_id, "content": new_content}})
        return self.get(task_id)

    def bulk_rename(self, task_ids: list[int], prefix: str) -> list[TaskReadSchema]:
        """Aplica um prefixo de nomenclatura (ex.: "[POS/Simphony]") em massa.

        Idempotente: tarefas que ja comecam com o prefixo, ou cujo nome nao segue o
        padrao "F<n>... - Acao", sao puladas sem erro. Equivalente ao que
        scripts/_apply_naming_256.py fazia manualmente via API direta.
        """
        results = []
        for task_id in task_ids:
            current = self.get(task_id)
            if current.name.startswith(prefix) or not _PHASE_NAME_RE.match(current.name):
                results.append(current)
                continue
            new_name = f"{prefix} {current.name}"
            self._client.request(
                "PUT", f"ProjectTask/{task_id}", {"input": {"id": task_id, "name": new_name}}
            )
            results.append(self.get(task_id))
        return results

    def bulk_apply_dod(self, task_ids: list[int], phase: Optional[TaskPhase] = None) -> list[TaskReadSchema]:
        """Injeta o checklist de DoD em massa em tarefas ja existentes.

        Usa `phase` explicito quando informado (tarefas criadas fora deste pacote,
        sem o campo `phase` no schema original); senao, pula a tarefa. Idempotente:
        tarefas que ja tem "[ ]" no content sao puladas. Equivalente ao que
        scripts/_apply_dod_256.py fazia manualmente.
        """
        results = []
        for task_id in task_ids:
            current = self.get(task_id)
            content = current.content or ""
            if "[ ]" in content or "[x]" in content.lower():
                results.append(current)
                continue
            if phase is None:
                results.append(current)
                continue
            dod_schema = TaskCreateSchema(name=current.name, projects_id=current.projects_id, phase=phase)
            dod_block = dod_schema.build_dod_block()
            if not dod_block:
                results.append(current)
                continue
            results.append(self.append_content(task_id, dod_block))
        return results

    def discover_project_tasks(self, project_id: int, id_range: tuple[int, int]) -> list[TaskReadSchema]:
        """Descobre as ProjectTasks reais de um projeto varrendo um range de IDs.

        Workaround necessario nesta instancia GLPI: o endpoint
        `GET Project/{id}/ProjectTask` (e `GET ProjectTask?range=...`) devolve um
        subconjunto incompleto e nao confiavel das tarefas (ver memoria de projeto
        "Quirks API GLPI"). Por isso a descoberta e feita por GET individual
        (`ProjectTask/{id}`) filtrando por `projects_id`, em vez de usar o
        sub-recurso de listagem.
        """
        start, end = id_range
        found = []
        for task_id in range(start, end + 1):
            try:
                raw = self._client.request("GET", f"ProjectTask/{task_id}")
            except Exception:
                continue
            if not isinstance(raw, dict) or raw.get("projects_id") != project_id:
                continue
            found.append(TaskReadSchema.model_validate(raw))
        return found
