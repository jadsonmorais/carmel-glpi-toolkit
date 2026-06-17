"""Cliente HTTP puro para a API REST do GLPI. Responsabilidade unica: autenticacao + transporte."""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from glpi_core.config import GLPICredentials


class GLPIRequestError(RuntimeError):
    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


class GLPIClient:
    """Nao conhece schemas nem regras de negocio — so fala HTTP com o GLPI."""

    def __init__(self, creds: GLPICredentials):
        self._creds = creds
        self._session_token: str | None = None

    def _init_session(self) -> None:
        req = urllib.request.Request(f"{self._creds.base_url}/initSession", method="GET")
        req.add_header("App-Token", self._creds.app_token)
        req.add_header("Authorization", f"user_token {self._creds.user_token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            self._session_token = data["session_token"]

    def close(self) -> None:
        if self._session_token:
            self.request("GET", "killSession")
            self._session_token = None

    def request(self, method: str, endpoint: str, body: dict | None = None) -> dict | list | None:
        if not self._session_token:
            self._init_session()

        url = f"{self._creds.base_url}/{endpoint}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("App-Token", self._creds.app_token)
        req.add_header("Session-Token", self._session_token)
        if body:
            req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            raise GLPIRequestError(e.code, e.read().decode() if e.fp else "") from e

    def __enter__(self) -> "GLPIClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
