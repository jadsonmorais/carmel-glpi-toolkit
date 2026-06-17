"""Resolucao de credenciais GLPI: env vars > scripts/config.json > config.yaml do Hermes."""
from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass

_PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_PACKAGE_DIR, ".."))


def _load_dotenv() -> None:
    dotenv_path = os.path.join(_REPO_ROOT, ".env")
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            m = re.match(r'^(\w+):\s*"([^"]*)"', line)
            if not m:
                m = re.match(r'^(\w+)=(?:"([^"]*)"|(.*))$', line)
                if not m:
                    continue
                key, val = m.group(1), m.group(2) if m.group(2) is not None else m.group(3)
            else:
                key, val = m.group(1), m.group(2)
            os.environ.setdefault(key, val)


_load_dotenv()


@dataclass(frozen=True)
class GLPICredentials:
    app_token: str
    user_token: str
    base_url: str  # ja inclui /apirest.php


def load_credentials() -> GLPICredentials:
    """Carrega tokens do GLPI de varias fontes, em ordem de prioridade."""
    app_token = os.environ.get("GLPI_APP_TOKEN")
    user_token = os.environ.get("GLPI_USER_TOKEN")
    base_url = os.environ.get("GLPI_URL")

    if app_token and user_token and base_url:
        return GLPICredentials(app_token, user_token, base_url.rstrip("/") + "/apirest.php")

    local_config = os.path.join(_REPO_ROOT, "scripts", "config.json")
    if os.path.exists(local_config):
        try:
            with open(local_config, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            app_token = cfg.get("app_token")
            user_token = cfg.get("user_token")
            base_url = cfg.get("glpi_base_url")
            if app_token and user_token and base_url:
                return GLPICredentials(app_token, user_token, base_url.rstrip("/") + "/apirest.php")
        except (json.JSONDecodeError, OSError):
            pass

    for config_path in (
        os.path.expanduser("~/AppData/Local/hermes/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ):
        if not os.path.exists(config_path):
            continue
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()
        app_match = re.search(r'GLPI_APP_TOKEN:\s*"([^"]+)"', content)
        user_match = re.search(r'GLPI_USER_TOKEN:\s*"([^"]+)"', content)
        url_match = re.search(r'GLPI_URL:\s*"([^"]+)"', content)
        if app_match and user_match and url_match:
            return GLPICredentials(
                app_match.group(1),
                user_match.group(1),
                url_match.group(1).rstrip("/") + "/apirest.php",
            )

    print("ERRO: Nao foi possivel encontrar credenciais GLPI.", file=sys.stderr)
    print("       Configure via GLPI_APP_TOKEN/GLPI_USER_TOKEN/GLPI_URL ou scripts/config.json", file=sys.stderr)
    sys.exit(1)
