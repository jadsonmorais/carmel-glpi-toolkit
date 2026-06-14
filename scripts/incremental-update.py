"""
Processamento incremental de chamados VerdanaDesk/GLPI.

Uso:
    py scripts/incremental-update.py               # só tickets novos/atualizados no GLPI
    py scripts/incremental-update.py --force-all   # reprocessa todos (preserva seções analíticas)

O script:
  1. Busca endpoint de lista (metadados) e bulk (acompanhamentos)
  2. Compara Data da Ultima Atualizacao do GLPI com o index.md
  3. Gera/atualiza apenas os .md dos tickets modificados
  4. Preserva seções analíticas preenchidas manualmente (Resumo, Decisões, Bloqueios, etc.)
  5. Atualiza index.md com novos timestamps
"""

import json
import html
import re
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from _env import BASE_DIR, URL_LIST, URL_BULK, fetch_json, GLPI_BASE_URL

DATA_DIR   = BASE_DIR
INDEX_PATH = os.path.join(DATA_DIR, "index.md")

ENDPOINT_LISTA = URL_LIST
ENDPOINT_BULK  = URL_BULK
TIMESTAMP_FMT  = "%Y-%m-%d %H:%M"

GLPI_TICKET_URL = f"{GLPI_BASE_URL.rstrip('/')}/front/ticket.form.php?id="


# Seções cujo conteúdo analítico deve ser preservado se já foi preenchido
ANALYTICAL_SECTIONS = [
    "Resumo Executivo",
    "Contexto do Negócio",
    "Decisões Técnicas",
    "Bloqueios & Dependências",
    "Próximos Passos / Status Atual",
]

# Textos que indicam seção ainda não preenchida (placeholder)
PLACEHOLDERS = {
    "*(extrair das interações conforme necessário)*",
    "*(registrar se identificados nas interações)*",
    "- [ ] verificar status atual no glpi",
    "- [ ] confirmar resolução ou escalonar",
}


def _extract_section_md(content: str, header: str) -> str:
    """Extrai texto de uma seção ## do markdown."""
    lines = content.splitlines()
    collecting = False
    result = []
    for line in lines:
        if line.startswith("## "):
            if line[3:].strip() == header:
                collecting = True
                continue
            elif collecting:
                break
        elif collecting:
            result.append(line)
    return "\n".join(result).strip()


def _is_placeholder(text: str) -> bool:
    """Retorna True se o texto é apenas placeholder genérico."""
    normalized = text.lower().strip()
    if not normalized:
        return True
    lines = [l.strip().lower() for l in normalized.splitlines() if l.strip()]
    return all(l in PLACEHOLDERS for l in lines)


def ler_secoes_existentes(filepath: str) -> dict:
    """
    Lê um .md existente e retorna dict {secao: conteudo} para as seções analíticas
    que já foram preenchidas com conteúdo real (não placeholder).
    """
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return {}

    preserved = {}
    for section in ANALYTICAL_SECTIONS:
        text = _extract_section_md(content, section)
        if text and not _is_placeholder(text):
            preserved[section] = text
    return preserved


def limpar(raw_html):
    if not raw_html:
        return ""
    txt = html.unescape(raw_html)
    txt = re.sub(r"</?p>", "\n", txt)
    txt = re.sub(r"<br\s*/?>", "\n", txt)
    txt = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>[^<]*</a>', r"[\1]", txt)
    txt = re.sub(r"<img[^>]*>", "[imagem]", txt)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = txt.replace(" ", " ")
    return txt.strip()


def ler_index():
    """Retorna dict {ticket_id: {'proc_ts': str, 'glpi_ts': str}}"""
    idx = {}
    if not os.path.exists(INDEX_PATH):
        return idx
    with open(INDEX_PATH, encoding="utf-8") as f:
        for line in f:
            if line.startswith("|") and "Processado" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 5:
                    # formato: | ticket | proc_ts | glpi_ts | status |
                    tid = parts[1]
                    proc_ts = parts[2]
                    glpi_ts = parts[3]
                    idx[tid] = {"proc_ts": proc_ts, "glpi_ts": glpi_ts}
                elif len(parts) >= 4:
                    # formato legado: | ticket | proc_ts | status |
                    tid = parts[1]
                    proc_ts = parts[2]
                    idx[tid] = {"proc_ts": proc_ts, "glpi_ts": ""}
    return idx


def gerar_md(tid, meta, items, preserved=None):
    titulo = meta.get("Categoria", "Sem categoria")
    localizacao = meta.get("Localizacao", "")
    status = meta.get("Status", "")
    requerente = meta.get("Requerente", "")
    tecnico = meta.get("Tecnico Atribuido") or "Não atribuído"
    abertura_data = meta.get("Data da Abertura", "")
    ultima_atualizacao = meta.get("Data da Ultima Atualizacao", "")
    urgencia = meta.get("Urgencia", "")
    prioridade = meta.get("Prioridade", "")
    tipo_chamado = meta.get("Tipo", "")
    grupo_requerente = meta.get("Grupo Requerente", "")

    p = preserved or {}
    items_sorted = sorted(items, key=lambda x: x.get("date", ""))
    followups = [i for i in items_sorted if i.get("tipo") != "abertura"]

    linhas_tempo = []
    for i in items_sorted:
        tipo_label = {"abertura": "Abertura", "followup": "Acompanhamento", "task": "Tarefa"}.get(
            i.get("tipo", ""), i.get("tipo", "")
        )
        conteudo = limpar(i.get("content", ""))
        data = i.get("date", "")
        autor = i.get("users_id", "")
        if conteudo:
            linhas_tempo.append(
                f"- **{data}** [{tipo_label}] (user_id:{autor}): {conteudo[:400]}"
            )

    # Seções analíticas: usa conteúdo preservado se existir, senão placeholder
    resumo = p.get("Resumo Executivo") or (
        f"Chamado aberto em {localizacao} na categoria {titulo}. "
        f"Status atual: {status}. Total de {len(items_sorted)} interações "
        f"({len(followups)} acompanhamentos/tarefas)."
    )
    contexto = p.get("Contexto do Negócio") or (
        f"- **Localização:** {localizacao}\n"
        f"- **Requerente:** {requerente}\n"
        f"- **Categoria:** {titulo}"
    )
    decisoes   = p.get("Decisões Técnicas")          or "- *(Extrair das interações conforme necessário)*"
    bloqueios  = p.get("Bloqueios & Dependências")    or "- *(Registrar se identificados nas interações)*"
    proximos   = p.get("Próximos Passos / Status Atual") or (
        "- [ ] Verificar status atual no GLPI\n"
        "- [ ] Confirmar resolução ou escalonar"
    )

    return f"""# Chamado #{tid} — {titulo}

## Metadados

| Campo | Valor |
|-------|-------|
| ID | {tid} |
| Status | {status} |
| Localização | {localizacao} |
| Requerente | {requerente} |
| Técnico Atribuído | {tecnico} |
| Data de Abertura | {abertura_data} |
| Última Atualização GLPI | {ultima_atualizacao} |
| Urgência | {urgencia} |
| Prioridade | {prioridade} |
| Categoria | {titulo} |
| Tipo de Chamado | {tipo_chamado} |
| Grupo Requerente | {grupo_requerente} |

## Resumo Executivo

{resumo}

## Contexto do Negócio

{contexto}

## Participantes

| Papel | Nome |
|-------|------|
| Requerente | {requerente} |
| Técnico | {tecnico} |

## Linha do Tempo

{chr(10).join(linhas_tempo) if linhas_tempo else "*(sem interações registradas)*"}

## Decisões Técnicas

{decisoes}

## Bloqueios & Dependências

{bloqueios}

## Próximos Passos / Status Atual

{proximos}

## Referências Cruzadas

- [GLPI Ticket #{tid}]({GLPI_TICKET_URL}{tid})
"""


def atualizar_index(idx, processados):
    """
    processados: lista de (tid, proc_ts, glpi_ts)
    Reescreve o index.md mantendo entradas existentes e atualizando/adicionando as novas.
    """
    # Ler linhas atuais
    linhas_atuais = []
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH, encoding="utf-8") as f:
            linhas_atuais = f.readlines()

    # Montar dict das novas entradas
    novos = {tid: (proc_ts, glpi_ts) for tid, proc_ts, glpi_ts in processados}

    novas_linhas = []
    cabecalho_encontrado = False
    for linha in linhas_atuais:
        if linha.startswith("| Ticket |"):
            cabecalho_encontrado = True
            novas_linhas.append("| Ticket | Data de processamento | Última atualização GLPI | Status |\n")
            novas_linhas.append("|--------|----------------------|------------------------|--------|\n")
            continue
        if linha.startswith("|--------|"):
            continue  # já adicionado acima
        if linha.startswith("| ") and "Processado" in linha:
            parts = [p.strip() for p in linha.split("|")]
            tid = parts[1]
            if tid in novos:
                proc_ts, glpi_ts = novos.pop(tid)
                novas_linhas.append(f"| {tid} | {proc_ts} | {glpi_ts} | Processado |\n")
            else:
                # manter linha existente, normalizar para novo formato se necessário
                if len(parts) >= 5:
                    novas_linhas.append(f"| {parts[1]} | {parts[2]} | {parts[3]} | Processado |\n")
                else:
                    novas_linhas.append(f"| {parts[1]} | {parts[2]} | | Processado |\n")
            continue
        if linha.startswith("Última atualização:"):
            novas_linhas.append(f"Última atualização: {datetime.now().strftime(TIMESTAMP_FMT)}\n")
            continue
        novas_linhas.append(linha)

    # Adicionar tickets novos que não estavam no index
    for tid, (proc_ts, glpi_ts) in sorted(novos.items(), key=lambda x: int(x[0])):
        novas_linhas.append(f"| {tid} | {proc_ts} | {glpi_ts} | Processado |\n")

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.writelines(novas_linhas)


# --- Main ---

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-all", action="store_true",
                        help="Reprocessa todos os tickets (preserva seções analíticas preenchidas)")
    args = parser.parse_args()

    agora = datetime.now().strftime(TIMESTAMP_FMT)
    print(f"[{agora}] Buscando endpoints GLPI...")

    lista_data = fetch_json(ENDPOINT_LISTA)
    bulk_data  = fetch_json(ENDPOINT_BULK)

    lista_items = lista_data.get("data", [])
    bulk_items  = bulk_data.get("data", [])

    print(f"  Lista: {len(lista_items)} tickets | Bulk: {len(bulk_items)} interações")

    # Metadados por ticket
    meta = {str(i["id"]): i for i in lista_items}

    # Agrupar bulk por Ticket
    grupos = defaultdict(list)
    for item in bulk_items:
        tid = str(item.get("Ticket", ""))
        if tid:
            grupos[tid].append(item)

    # Ler index atual
    idx = ler_index()

    # Determinar tickets a processar
    a_processar = []
    for item in lista_items:
        tid = str(item["id"])
        glpi_upd = item.get("Data da Ultima Atualizacao") or ""
        entrada = idx.get(tid, {})
        glpi_ts_index = entrada.get("glpi_ts", "")

        if args.force_all:
            a_processar.append((tid, glpi_upd, "force"))
        elif not entrada:
            a_processar.append((tid, glpi_upd, "novo"))
        elif glpi_upd and glpi_ts_index and glpi_upd > glpi_ts_index:
            a_processar.append((tid, glpi_upd, "atualizado"))
        elif not glpi_ts_index:
            # entrada legada sem glpi_ts — reprocessar para preencher
            a_processar.append((tid, glpi_upd, "legado"))

    print(f"  Tickets a processar: {len(a_processar)}")
    if not a_processar:
        print("  Nenhuma atualização necessária.")
        return

    processados = []
    preservados_count = 0
    for tid, glpi_upd, motivo in a_processar:
        m = meta.get(tid, {})
        items = grupos.get(tid, [])
        out_path = os.path.join(DATA_DIR, f"{tid}.md")
        preserved = ler_secoes_existentes(out_path)
        if preserved:
            preservados_count += 1
        md = gerar_md(tid, m, items, preserved)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md)
        processados.append((tid, agora, glpi_upd))
        flag = " [preservado]" if preserved else ""
        print(f"  [{motivo}] #{tid} - {len(items)} interacoes{flag}")

    atualizar_index(idx, processados)
    print(f"\nConcluído. {len(processados)} ticket(s) processado(s). index.md atualizado.")
    if preservados_count:
        print(f"  Seções analíticas preservadas em {preservados_count} ticket(s).")

    # Hook RAG: atualizar embeddings dos tickets processados (falha silenciosa)
    try:
        import subprocess
        rag_script = os.path.join(os.path.dirname(__file__), "rag-build.py")
        if os.path.exists(rag_script):
            args = [sys.executable, rag_script]
            for tid, _, _ in processados:
                args += ["--ticket", tid]
            result = subprocess.run(args, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"[RAG] Embeddings atualizados para {len(processados)} ticket(s).")
            else:
                # Deps não instaladas — não bloquear o fluxo
                pass
    except Exception:
        pass


if __name__ == "__main__":
    main()
