#!/usr/bin/env python3
"""
Script de processamento em lote de chamados GLPI (VerdanaDesk).
Gera arquivos .md individuais para tickets ainda nao processados.

Uso (WSL/Linux):  python3 scripts/process_bulk.py
Uso (Windows):    py scripts/process_bulk.py

NOTA: Para processamento incremental (so o que mudou), usar incremental-update.py.
      Este script processa apenas tickets NOVOS (nao existentes no diretorio data/).
"""

import json, html, re, os, sys, datetime
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from _env import BASE_DIR, URL_BULK, fetch_json

def limpar_conteudo(raw_html: str) -> str:
    t = html.unescape(raw_html)
    t = re.sub(r'<\/?p>', '\n', t)
    t = re.sub(r'<br\s*\/?>', '\n', t)
    t = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>[^<]*<\/a>', r'\1', t)
    t = re.sub(r'<img[^>]*>', '[imagem]', t)
    t = re.sub(r'<[^>]+>', '', t)
    t = t.replace('\u00a0', ' ')
    return ' '.join(t.split())

def load_existing_ids(base_dir: str) -> set:
    return {
        f.replace('.md', '')
        for f in os.listdir(base_dir)
        if f.endswith('.md') and f not in ('insights.md', 'index.md', 'chamados.md')
    }

def generate_ticket_md(ticket_id: str, items: list, default_title: str) -> str:
    items.sort(key=lambda x: x['date'])
    title = items[0].get('ticket_name', default_title)
    lines = [
        f"# Chamado #{ticket_id} — {title}\n",
        "## Metadados\n| Campo | Valor |\n|-------|-------|",
        f"| Ticket | {ticket_id} |",
        f"| Total | {len(items)} |",
        f"| Periodo | {items[0]['date']} a {items[-1]['date']} |\n",
        "## Linha do Tempo\n",
    ]
    for it in items:
        c = limpar_conteudo(it['content'])
        lines.append(f"**[{it['date']}]** ({it['tipo']}, user {it['users_id']})")
        lines.append(f"> {c}\n")
    return '\n'.join(lines)

def update_index(base_dir: str, processed: list, existing: set):
    idx_path = os.path.join(base_dir, 'index.md')
    hoje = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    rows = []
    if os.path.exists(idx_path):
        with open(idx_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('|') and 'Ticket' not in line and '---' not in line and line.strip():
                    rows.append(line.rstrip())

    for tid in processed:
        rows.append(f"| {tid} | {hoje} | Processado |")

    for tid in existing:
        if not any(r.startswith(f"| {tid} ") for r in rows):
            rows.append(f"| {tid} | Anterior | Processado |")

    header = [
        "# Indice de Chamados Processados\n",
        f"Ultima atualizacao: {hoje}\n",
        "| Ticket | Data de processamento | Status |\n|--------|----------------------|--------|",
    ]

    with open(idx_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(header + rows) + '\n')

def main():
    os.makedirs(BASE_DIR, exist_ok=True)
    data = fetch_json(URL_BULK)

    tickets = defaultdict(list)
    for item in data.get('data', []):
        tickets[str(item['Ticket'])].append(item)

    existing = load_existing_ids(BASE_DIR)
    new_ids = [tid for tid in tickets if tid not in existing]

    processed = []
    for tid in new_ids:
        md = generate_ticket_md(tid, tickets[tid], data.get('name', ''))
        with open(os.path.join(BASE_DIR, f"{tid}.md"), 'w', encoding='utf-8') as f:
            f.write(md)
        processed.append(tid)

    update_index(BASE_DIR, processed, existing)

    print(f"Processados: {len(processed)}. Total na base: {len(existing) + len(processed)}")

if __name__ == '__main__':
    main()
