#!/usr/bin/env python3
"""
Script reutilizável para análise de backlog GLPI/VerdanaDesk.
Gera: plano-de-acao.md, chamados-parados-detalhado.md, chamados-antigos-detalhado.md

Uso (WSL/Linux):  python3 scripts/analyze-backlog.py
Uso (Windows):    py scripts/analyze-backlog.py
"""
import json, os, sys
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from _env import BASE_DIR, URL_LIST, URL_BULK, fetch_json

THRESHOLD_PARADO = 30   # dias sem interação
THRESHOLD_ANTIGO = 90   # dias desde abertura


def main():
    meta = {str(item['id']): item for item in fetch_json(URL_LIST).get('data', [])}
    bulk = fetch_json(URL_BULK)

    interactions = defaultdict(list)
    for item in bulk.get('data', []):
        interactions[str(item.get('Ticket'))].append(item)

    tickets = []
    for f in os.listdir(BASE_DIR):
        if not f.endswith('.md') or f in ('insights.md', 'index.md', 'chamados.md',
                                           'plano-de-acao.md', 'chamados-parados-detalhado.md',
                                           'chamados-antigos-detalhado.md'):
            continue
        tid = f.replace('.md', '')
        m = meta.get(tid, {})
        its = interactions.get(tid, [])
        dates = [i['date'] for i in its if i.get('date')]
        if not dates:
            continue
        first = datetime.strptime(min(dates)[:10], '%Y-%m-%d')
        last = datetime.strptime(max(dates)[:10], '%Y-%m-%d')
        age = (datetime.now() - first).days
        idle = (datetime.now() - last).days
        tickets.append({
            'id': tid, 'idade': age, 'idle': idle,
            'status': m.get('Status', 'N/A'),
            'categoria': str(m.get('Categoria', '')).split('>')[0].strip(),
            'local': m.get('Localizacao', ''),
            'tecnico': m.get('Tecnico Atribuido', 'Ninguém'),
            'interacoes': len(its),
            'abertura': min(dates)[:10],
            'ultima': max(dates)[:10]
        })

    stuck = [t for t in tickets if t['idle'] > THRESHOLD_PARADO]
    old = [t for t in tickets if t['idade'] > THRESHOLD_ANTIGO]
    status_c = Counter(t['status'] for t in tickets)
    cat_c = Counter(t['categoria'] for t in tickets)
    tec_c = Counter(t['tecnico'] for t in tickets)

    # Gera plano-de-acao.md
    lines = [
        f"# Plano de Ação — Chamados (Gerado em {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        "", "## 1. Panorama Geral",
        f"- **Total analisado:** {len(tickets)}",
        f"- **Sem movimentação {THRESHOLD_PARADO}+ dias:** {len(stuck)}",
        f"- **Abertos há {THRESHOLD_ANTIGO}+ dias:** {len(old)}",
        "", "## 2. Distribuição por Status", "| Status | Qtd |", "|--------|-----|"
    ]
    for st, q in status_c.most_common():
        lines.append(f"| {st} | {q} |")

    lines += ["", "## 3. Distribuição por Categoria", "| Categoria | Qtd |", "|----------|-----|"]
    for cat, q in cat_c.most_common(10):
        lines.append(f"| {cat} | {q} |")

    lines += ["", "## 4. Top Técnicos", "| Técnico | Qtd |", "|---------|-----|"]
    for tec, q in tec_c.most_common(10):
        lines.append(f"| {tec} | {q} |")

    lines += ["", f"## 5. Chamados Parados (>{THRESHOLD_PARADO} dias)",
                "| Ticket | Idle | Status | Categoria | Técnico |",
                "|--------|------|--------|-----------|---------|"]
    for t in sorted(stuck, key=lambda x: x['idle'], reverse=True)[:20]:
        lines.append(f"| {t['id']} | {t['idle']} | {t['status']} | {t['categoria']} | {t['tecnico']} |")

    lines += ["", f"## 6. Chamados Antigos (>{THRESHOLD_ANTIGO} dias)",
                "| Ticket | Idade | Status | Categoria | Última |",
                "|--------|-------|--------|-----------|--------|"]
    for t in sorted(old, key=lambda x: x['idade'], reverse=True)[:20]:
        lines.append(f"| {t['id']} | {t['idade']} | {t['status']} | {t['categoria']} | {t['ultima']} |")

    with open(os.path.join(BASE_DIR, 'plano-de-acao.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f"[OK] plano-de-acao.md gerado. Parados={len(stuck)}, Antigos={len(old)}")


if __name__ == '__main__':
    main()
