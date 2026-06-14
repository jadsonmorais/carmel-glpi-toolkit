# Decisão: Onde armazenar dados da skill

## Decisão

Dados da skill (tickets .md, index.md, insights.md) ficam em:
```
skills/productivity/verdanadesk-chamados/data/
```

**NÃO** em `~/.hermes/memories/`.

## Por quê

- `memories/` é para contexto do usuário (preferências, projetos, feedback)
- `data/` da skill é output operacional — grande volume, substituível via reprocessamento
- Separação evita poluir o índice MEMORY.md com centenas de entradas de tickets

## Checklist de migração (se mover dados)

1. `grep -r "memories/" .` na raiz da skill para achar paths hardcoded
2. Atualizar `DATA_DIR` em `scripts/incremental-update.py`
3. Atualizar `## Diretório de trabalho` no SKILL.md
4. Atualizar `## Templates de referência` no SKILL.md
