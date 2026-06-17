#!/usr/bin/env python3
"""
GLPI Tag Manager - Consulta, atribui e remove etiquetas via API REST.

Uso:
  python tag-manager.py list [--itemtype TYPE] [--items-id ID]
  python tag-manager.py assign --itemtype TYPE --items-id ID --tag-id ID
  python tag-manager.py remove --tag-item-id ID
  python tag-manager.py tags [--name NAME]

Exemplos:
  python tag-manager.py tags                           # Listar todas as etiquetas
  python tag-manager.py tags --name Analise            # Filtrar por nome
  python tag-manager.py list --itemtype Ticket --items-id 27760
  python tag-manager.py assign --itemtype Ticket --items-id 27760 --tag-id 204
  python tag-manager.py remove --tag-item-id 16935
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

# Carrega .env do raiz do projeto para os.environ (formato KEY: "VALUE" ou KEY=VALUE)
def _load_dotenv():
    import re
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dotenv_path = os.path.normpath(os.path.join(script_dir, "..", ".env"))
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


# Carrega credenciais do config do Hermes ou de fontes alternativas
def load_credentials():
    """Carrega tokens do GLPI de varias fontes, em ordem de prioridade."""
    import re

    # 1. Variaveis de ambiente (inclui .env carregado acima)
    app_token = os.environ.get("GLPI_APP_TOKEN")
    user_token = os.environ.get("GLPI_USER_TOKEN")
    base_url = os.environ.get("GLPI_URL")

    if app_token and user_token and base_url:
        return {
            "app_token": app_token,
            "user_token": user_token,
            "base_url": base_url.rstrip("/") + "/apirest.php",
        }

    # 2. Arquivo config.json local na skill
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_config = os.path.join(script_dir, "config.json")
    if os.path.exists(local_config):
        try:
            with open(local_config, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            app_token = cfg.get("app_token")
            user_token = cfg.get("user_token")
            base_url = cfg.get("glpi_base_url")
            if app_token and user_token and base_url:
                return {
                    "app_token": app_token,
                    "user_token": user_token,
                    "base_url": base_url.rstrip("/") + "/apirest.php",
                }
        except (json.JSONDecodeError, OSError):
            pass

    # 3. Config.yaml do Hermes
    config_paths = [
        os.path.expanduser("~/AppData/Local/hermes/config.yaml"),
        os.path.expanduser("~/.hermes/config.yaml"),
    ]

    for config_path in config_paths:
        if not os.path.exists(config_path):
            continue
        with open(config_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extrai tokens usando regex simples
        app_match = re.search(r'GLPI_APP_TOKEN:\s*"([^"]+)"', content)
        user_match = re.search(r'GLPI_USER_TOKEN:\s*"([^"]+)"', content)
        url_match = re.search(r'GLPI_URL:\s*"([^"]+)"', content)

        if app_match and user_match and url_match:
            return {
                "app_token": app_match.group(1),
                "user_token": user_match.group(1),
                "base_url": url_match.group(1).rstrip("/") + "/apirest.php",
            }

    print("ERRO: Nao foi possivel encontrar credenciais GLPI.", file=sys.stderr)
    print("       Configure via:", file=sys.stderr)
    print("       - Variaveis de ambiente: GLPI_APP_TOKEN, GLPI_USER_TOKEN, GLPI_URL", file=sys.stderr)
    print("       - Arquivo scripts/config.json (veja config.json.example)", file=sys.stderr)
    print("       - Config.yaml do Hermes (se estiver usando Hermes Agent)", file=sys.stderr)
    sys.exit(1)


class GLPIApiClient:
    """Cliente simples para a API REST do GLPI."""

    def __init__(self, creds):
        self.base_url = creds["base_url"]
        self.app_token = creds["app_token"]
        self.user_token = creds["user_token"]
        self.session_token = None

    def _init_session(self):
        """Inicializa sessão GLPI."""
        url = f"{self.base_url}/initSession"
        req = urllib.request.Request(url, method="GET")
        req.add_header("App-Token", self.app_token)
        req.add_header("Authorization", f"user_token {self.user_token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
                self.session_token = data["session_token"]
        except (urllib.error.URLError, KeyError) as e:
            print(f"ERRO ao inicializar sessão: {e}", file=sys.stderr)
            sys.exit(1)

    def _request(self, method, endpoint, body=None):
        """Faz requisição à API REST."""
        if not self.session_token:
            self._init_session()

        url = f"{self.base_url}/{endpoint}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("App-Token", self.app_token)
        req.add_header("Session-Token", self.session_token)
        if body:
            req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            body_text = e.read().decode() if e.fp else ""
            print(f"ERRO HTTP {e.code}: {body_text}", file=sys.stderr)
            return None
        except urllib.error.URLError as e:
            print(f"ERRO de conexão: {e}", file=sys.stderr)
            return None

    def list_tags(self, name_filter=None):
        """Lista todas as etiquetas disponíveis."""
        result = self._request("GET", "PluginTagTag?range=0-999")
        if not isinstance(result, list):
            return []
        if name_filter:
            name_lower = name_filter.lower()
            result = [t for t in result if name_lower in t.get("name", "").lower()]
        return result

    def list_item_tags(self, itemtype, items_id):
        """Lista etiquetas atribuídas a um item."""
        result = self._request("GET", f"{itemtype}/{items_id}/PluginTagTagItem")
        return result if isinstance(result, list) else []

    def assign_tag(self, itemtype, items_id, tag_id):
        """Atribui uma etiqueta a um item."""
        body = {"input": {"itemtype": itemtype, "items_id": items_id, "plugin_tag_tags_id": tag_id}}
        return self._request("POST", "PluginTagTagItem", body)

    def remove_tag(self, tag_item_id):
        """Remove uma atribuição de etiqueta."""
        return self._request("DELETE", f"PluginTagTagItem/{tag_item_id}")


def cmd_tags(client, args):
    """Lista etiquetas disponíveis."""
    tags = client.list_tags(name_filter=args.name)
    if not tags:
        print("Nenhuma etiqueta encontrada.")
        return

    print(f"{'ID':>5} | {'Nome':<30} | {'Cor':<10} | {'Aplicável a'}")
    print("-" * 80)
    for t in tags:
        menus = t.get("type_menu", "[]")
        try:
            menu_list = json.loads(menus) if isinstance(menus, str) else menus
        except json.JSONDecodeError:
            menu_list = []
        menu_str = ", ".join(menu_list) if menu_list else "—"
        color = t.get("color", "") or "—"
        print(f"{t['id']:>5} | {t['name']:<30} | {color:<10} | {menu_str}")


def cmd_list(client, args):
    """Lista etiquetas de um item."""
    tags = client.list_item_tags(args.itemtype, args.items_id)
    if not tags:
        print(f"Nenhuma etiqueta encontrada para {args.itemtype} #{args.items_id}.")
        return

    print(f"Etiquetas atribuídas a {args.itemtype} #{args.items_id}:")
    print(f"{'Assoc.ID':>8} | {'Tag ID':>6} | {'Nome':<30} | {'Cor'}")
    print("-" * 70)

    # Busca detalhes das tags
    all_tags = {t["id"]: t for t in client.list_tags()}

    for t in tags:
        tag_id = t.get("plugin_tag_tags_id")
        tag_info = all_tags.get(tag_id, {})
        tag_name = tag_info.get("name", f"(tag {tag_id})")
        color = tag_info.get("color", "") or "—"
        assoc_id = t.get("id", "—")
        print(f"{assoc_id:>8} | {tag_id:>6} | {tag_name:<30} | {color}")


def cmd_assign(client, args):
    """Atribui etiqueta."""
    result = client.assign_tag(args.itemtype, args.items_id, args.tag_id)
    if result and "id" in result:
        print(f"✓ Etiqueta {args.tag_id} atribuída a {args.itemtype} #{args.items_id} (assoc. ID: {result['id']})")
    else:
        print(f"✗ Falha ao atribuir etiqueta: {result}")


def cmd_remove(client, args):
    """Remove atribuição de etiqueta."""
    result = client.remove_tag(args.tag_item_id)
    if result:
        print(f"✓ Atribuição {args.tag_item_id} removida com sucesso.")
    else:
        print(f"✗ Falha ao remover atribuição {args.tag_item_id}.")


def main():
    parser = argparse.ArgumentParser(description="GLPI Tag Manager")
    sub = parser.add_subparsers(dest="command")

    # tags - listar etiquetas disponíveis
    p_tags = sub.add_parser("tags", help="Listar etiquetas disponíveis")
    p_tags.add_argument("--name", help="Filtrar por nome (parcial)")
    p_tags.set_defaults(func=cmd_tags)

    # list - listar etiquetas de um item
    p_list = sub.add_parser("list", help="Listar etiquetas de um item")
    p_list.add_argument("--itemtype", required=True, choices=["Ticket", "Problem", "Change", "Computer", "ProjectTask"])
    p_list.add_argument("--items-id", required=True, type=int)
    p_list.set_defaults(func=cmd_list)

    # assign - atribuir etiqueta
    p_assign = sub.add_parser("assign", help="Atribuir etiqueta a um item")
    p_assign.add_argument("--itemtype", required=True, choices=["Ticket", "Problem", "Change", "Computer", "ProjectTask"])
    p_assign.add_argument("--items-id", required=True, type=int)
    p_assign.add_argument("--tag-id", required=True, type=int)
    p_assign.set_defaults(func=cmd_assign)

    # remove - remover atribuição
    p_remove = sub.add_parser("remove", help="Remover atribuição de etiqueta")
    p_remove.add_argument("--tag-item-id", required=True, type=int)
    p_remove.set_defaults(func=cmd_remove)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    creds = load_credentials()
    client = GLPIApiClient(creds)
    args.func(client, args)


if __name__ == "__main__":
    main()
