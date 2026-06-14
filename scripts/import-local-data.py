"""
Restaura na maquina local o conteudo gerado por export-local-data.py
(.env, data/, dumps _*.txt etc).

Uso:
    py scripts/import-local-data.py [caminho/para/glpi-local-data_TIMESTAMP.zip]

Sem argumento, usa o zip mais recente em dumps/.
Pede confirmacao antes de sobrescrever arquivos existentes.
"""
import glob
import os
import sys
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(SCRIPT_DIR, ".."))


def find_latest_zip():
    candidates = sorted(glob.glob(os.path.join(ROOT, "dumps", "glpi-local-data_*.zip")))
    return candidates[-1] if candidates else None


def main():
    if len(sys.argv) > 1:
        zip_path = sys.argv[1]
    else:
        zip_path = find_latest_zip()
        if not zip_path:
            print("Nenhum zip encontrado em dumps/. Informe o caminho como argumento.")
            return 1

    if not os.path.exists(zip_path):
        print(f"Arquivo nao encontrado: {zip_path}")
        return 1

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        print(f"Pacote: {zip_path}")
        print(f"{len(names)} arquivo(s):")
        for n in names:
            existing = " (sera SOBRESCRITO)" if os.path.exists(os.path.join(ROOT, n)) else ""
            print(f"  {n}{existing}")

        resp = input(f"\nExtrair para {ROOT}? [s/N] ").strip().lower()
        if resp != "s":
            print("Cancelado.")
            return 0

        zf.extractall(ROOT)

    print("OK: arquivos restaurados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
