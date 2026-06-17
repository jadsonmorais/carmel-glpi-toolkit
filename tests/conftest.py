"""Fixtures compartilhadas: cliente GLPI falso, sem rede, para testar services/macros."""
from __future__ import annotations

import pytest


class FakeGLPIClient:
    """Substitui GLPIClient nos testes: registra chamadas e devolve respostas pre-programadas.

    Uso: fake.queue_response("POST", "Project", {"id": 256})
         fake.queue_response("GET", "Project/256", {"id": 256, "name": "...", "entities_id": 0})
    """

    def __init__(self):
        self.calls: list[tuple[str, str, dict | None]] = []
        self._responses: dict[tuple[str, str], list] = {}

    def queue_response(self, method: str, endpoint: str, response) -> None:
        self._responses.setdefault((method, endpoint), []).append(response)

    def request(self, method: str, endpoint: str, body: dict | None = None):
        self.calls.append((method, endpoint, body))
        key = (method, endpoint)
        if key not in self._responses or not self._responses[key]:
            raise AssertionError(f"nenhuma resposta programada para {method} {endpoint}")
        return self._responses[key].pop(0)

    def close(self) -> None:
        pass


@pytest.fixture
def fake_client() -> FakeGLPIClient:
    return FakeGLPIClient()
