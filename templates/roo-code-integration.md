# VerdanaDesk Chamados

## Contexto
Pipeline de análise GLPI/VerdanaDesk localizado em: {{DIRETORIO_COMPLETO_DA_SKILL}}

## Scripts principais
| Script | Propósito |
|--------|-----------|
| `incremental-update.py` | Sincroniza tickets do GLPI para arquivos .md individuais |
| `analyze-backlog.py` | Gera relatório quantitativo (plano-de-acao.md) |
| `rag-build.py` | Constrói/atualiza índice vetorial ChromaDB |
| `rag-query.py` | Busca semântica nos tickets (similar, gravity, history, dedup) |
| `tag-manager.py` | CRUD de etiquetas GLPI via REST API |

## Configuração
- Arquivo: `scripts/config.json` (não versionar — veja `scripts/config.json.example`)
- Alternativa: variáveis de ambiente (`VERDANADESK_URL_LIST`, `VERDANADESK_URL_BULK`, `GLPI_BASE_URL`, `GLPI_APP_TOKEN`, `GLPI_USER_TOKEN`, `GLPI_URL`)

## Dados
- Diretório: `data/` (não versionar)
- Contém: arquivos `.md` por ticket, `index.md`, `insights.md`, `plano-de-acao.md`, `vectordb/`

## Convenções
- Usar `py` no Windows, `python3` no Linux/macOS
- Seções analíticas dos `.md` são preenchidas pela LLM e preservadas em reprocessamentos
- Tokens expiram — renovar no GLPI se retornar 403/404
- Nunca commite `scripts/config.json`
