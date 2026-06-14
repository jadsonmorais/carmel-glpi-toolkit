"""
Empacota em .zip tudo que existe localmente mas nao vai pro repositorio
(arquivos ignorados pelo git: .env, data/, dumps _*.txt etc).

Uso:
    py scripts/export-local-data.py

Gera dumps/glpi-local-data_<timestamp>.zip na raiz do projeto.
Envie esse zip pro dev / use pra restaurar em outra maquina com
import-local-data.py.
"""
import datetime
import os
import subprocess
import sys
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))

# Diretorios/arquivos que sao ignorados pelo git mas nao fazem sentido
# levar no dump (cache, venv, IDE etc).
EXCLUDE_DIR_NAMES = {"__pycache__", "venv", "env", "ENV", ".venv", ".vscode", ".idea", "dumps"}
EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".swp", ".swo")
EXCLUDE_NAMES = {"Thumbs.db", ".DS_Store"}


def list_ignored_files():
    out = subprocess.run(
        ["git", "ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
        cwd=ROOT, capture_output=True, check=True,
    ).stdout
    files = [f for f in out.decode("utf-8").split("\0") if f]

    result = []
    for f in files:
        parts = f.split("/")
        if any(p in EXCLUDE_DIR_NAMES for p in parts):
            continue
        if os.path.basename(f) in EXCLUDE_NAMES:
            continue
        if f.endswith(EXCLUDE_SUFFIXES):
            continue
        result.append(f)
    return result


def main():
    files = list_ignored_files()
    if not files:
        print("Nenhum arquivo ignorado encontrado para empacotar.")
        return

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(ROOT, "dumps")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"glpi-local-data_{ts}.zip")

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(os.path.join(ROOT, f), f)

    print(f"OK: {len(files)} arquivo(s) -> {out_path}\n")
    for f in files:
        print(f"  {f}")


if __name__ == "__main__":
    sys.exit(main())
