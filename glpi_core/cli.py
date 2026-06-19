"""Entrypoint CLI: executa uma macro registrada por nome com payload JSON."""
from __future__ import annotations

import argparse
import json
import sys

from glpi_core.command_handler import CommandContext, available_commands, dispatch
from glpi_core.config import load_credentials
from glpi_core.connection.client import GLPIClient
from glpi_core.connection.dry_run import DryRunClient

# importar os modulos de macro registra seus comandos no dispatcher
from glpi_core.macros import apply_template, bulk_ops, query_ops  # noqa: F401


def main() -> None:
    parser = argparse.ArgumentParser(description="GLPI Core - dispatcher de comandos/macros")
    parser.add_argument("command", nargs="?", help="nome do comando registrado")
    parser.add_argument("--payload", help="payload JSON do comando (cuidado com escaping no shell)", default="{}")
    parser.add_argument("--payload-file", help="caminho de um arquivo .json com o payload do comando")
    parser.add_argument("--list", action="store_true", help="lista comandos disponiveis")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="simula a execucao sem chamar a API real do GLPI; mostra os payloads que seriam enviados",
    )
    args = parser.parse_args()

    if args.list or not args.command:
        print("Comandos disponiveis:")
        for name in available_commands():
            print(f"  - {name}")
        sys.exit(0 if args.list else 1)

    if args.payload_file:
        with open(args.payload_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    else:
        payload = json.loads(args.payload)

    if args.dry_run:
        client = DryRunClient()
    else:
        client = GLPIClient(load_credentials())

    with client:
        ctx = CommandContext(client)
        result = dispatch(args.command, payload, ctx)

        if args.dry_run:
            print("=== Chamadas que seriam feitas ao GLPI ===")
            for method, endpoint, body in client.calls:
                body_str = json.dumps(body, ensure_ascii=False) if body else ""
                print(f"  {method} {endpoint} {body_str}")
            print()

        print("=== Resultado ===")
        print(json.dumps(result, default=lambda o: getattr(o, "model_dump", lambda: str(o))(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
