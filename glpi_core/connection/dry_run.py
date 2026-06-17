"""Cliente de simulacao: mesma interface de GLPIClient, mas nunca chama a API real.

Usado pelo CLI com --dry-run para mostrar exatamente os payloads que seriam
enviados ao GLPI, mantendo coerencia entre POST/GET/PUT (um GET apos um POST
devolve o registro "criado" na simulacao, para os services funcionarem sem
modificacao).
"""
from __future__ import annotations

from glpi_core.schemas.governance import GovernanceTag


class DryRunClient:
    def __init__(self):
        self.calls: list[tuple[str, str, dict | None]] = []
        self._store: dict[tuple[str, int], dict] = {}
        self._next_id = 9000

    def request(self, method: str, endpoint: str, body: dict | None = None):
        self.calls.append((method, endpoint, body))

        if method == "POST":
            self._next_id += 1
            new_id = self._next_id
            record = dict(body["input"]) if body and "input" in body else {}
            record["id"] = new_id
            itemtype = endpoint.split("?")[0]
            self._store[(itemtype, new_id)] = record
            return {"id": new_id}

        if method == "GET":
            if endpoint.startswith("PluginTagTag?"):
                # simula as tags de governanca ja existentes no GLPI, para resolve_tag_id funcionar
                return [{"id": 1000 + i, "name": tag.value} for i, tag in enumerate(GovernanceTag)]

            itemtype, _, rest = endpoint.partition("/")
            rest = rest.split("?")[0]
            if rest.isdigit():
                return self._store.get((itemtype, int(rest)), {"id": int(rest)})
            return []

        if method == "PUT":
            itemtype, _, rest = endpoint.partition("/")
            rid = int(rest.split("?")[0])
            record = self._store.setdefault((itemtype, rid), {"id": rid})
            if body and "input" in body:
                record.update(body["input"])
            return {"id": rid}

        if method == "DELETE":
            return {"id": None}

        return None

    def close(self) -> None:
        pass

    def __enter__(self) -> "DryRunClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
