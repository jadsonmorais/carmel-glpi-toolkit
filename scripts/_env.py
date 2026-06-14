"""
Configuracao de ambiente compartilhada entre os scripts da skill.
Auto-detecta se esta rodando em WSL/Linux ou Windows e ajusta os paths.

Importar em qualquer script com:
    from _env import BASE_DIR, fetch_json

Configuracao:
    1. Variaveis de ambiente (maior prioridade):
       - VERDANADESK_URL_LIST
       - VERDANADESK_URL_BULK
       - GLPI_BASE_URL
    2. Arquivo scripts/config.json (segunda prioridade):
       {"url_list": "...", "url_bulk": "...", "glpi_base_url": "..."}
    3. Fallback hardcoded (mantido para compatibilidade com ambiente atual)
"""
import json
import os
import re
import sys
import urllib.request

# --- Deteccao de ambiente ---
_IS_WINDOWS = sys.platform == "win32"

# Path relativo ao diretorio do script — funciona em qualquer maquina
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "data"))

# --- Carrega .env do raiz do projeto (formato KEY: "VALUE" ou KEY=VALUE) ---
def _load_dotenv():
    dotenv_path = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", ".env"))
    if not os.path.exists(dotenv_path):
        return
    with open(dotenv_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Formato YAML: KEY: "VALUE"
            m = re.match(r'^(\w+):\s*"([^"]*)"', line)
            if not m:
                # Formato .env padrão: KEY=VALUE ou KEY="VALUE"
                m = re.match(r'^(\w+)=(?:"([^"]*)"|(.*))$', line)
                if m:
                    key = m.group(1)
                    val = m.group(2) if m.group(2) is not None else m.group(3)
                else:
                    continue
            else:
                key, val = m.group(1), m.group(2)
            if key not in os.environ:
                os.environ[key] = val

_load_dotenv()

# --- Carrega configuracao ---
def _load_config():
    """Tenta carregar URLs de varias fontes, com fallback hardcoded."""
    # 1. Variaveis de ambiente (GLPI_URL é alias de GLPI_BASE_URL)
    url_list = os.environ.get("VERDANADESK_URL_LIST")
    url_bulk = os.environ.get("VERDANADESK_URL_BULK")
    url_assets = os.environ.get("VERDANADESK_URL_ASSETS")
    glpi_base = os.environ.get("GLPI_BASE_URL") or os.environ.get("GLPI_URL")

    # 2. Arquivo config.json local
    config_path = os.path.join(_SCRIPT_DIR, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if not url_list:
                url_list = cfg.get("url_list")
            if not url_bulk:
                url_bulk = cfg.get("url_bulk")
            if not url_assets:
                url_assets = cfg.get("url_assets")
            if not glpi_base:
                glpi_base = cfg.get("glpi_base_url")
        except (json.JSONDecodeError, OSError):
            pass

    # 3. Fallback hardcoded (ambiente Carmel Hoteis / VerdanaDesk)
    if not url_list:
        url_list = "https://carmelhoteis.verdanadesk.com/plugins/utilsdashboards/front/ajax/graphic.json.php?token=***"
    if not url_bulk:
        url_bulk = "https://carmelhoteis.verdanadesk.com/plugins/utilsdashboards/front/ajax/graphic.json.php?token=***"
    if not glpi_base:
        glpi_base = "https://carmelhoteis.verdanadesk.com"

    return url_list, url_bulk, url_assets, glpi_base


URL_LIST, URL_BULK, URL_ASSETS, GLPI_BASE_URL = _load_config()

# URL do ticket no frontend GLPI (usado por rag-query.py)
GLPI_TICKET_URL = f"{GLPI_BASE_URL.rstrip('/')}/front/ticket.form.php?id="


def fetch_json(url: str) -> dict:
    """Busca JSON de uma URL. Usa urllib (sem dependencias externas)."""
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERRO] Falha ao buscar {url}: {e}")
        print("       Verifique se o token ainda e valido no GLPI.")
        return {"data": []}
