# Portabilidade Cross-Agent — VerdanaDesk Chamados

## Contexto

A skill `verdanadesk-chamados` foi projetada para funcionar no **Hermes Agent**, mas o usuário solicitou portabilidade para outros agentes de código (Claude Code, Roo Code/VSCode) e uso standalone via CLI. Este documento captura os ajustes necessários e o estado atual da portabilidade.

---

## Arquitetura de Configuracao (fallback em camadas)

Todos os scripts usam a mesma hierarquia de configuracao — prioridade decrescente:

```
1. Variaveis de ambiente (maior prioridade)
   VERDANADESK_URL_LIST, VERDANADESK_URL_BULK, GLPI_BASE_URL
   GLPI_APP_TOKEN, GLPI_USER_TOKEN, GLPI_URL

2. Arquivo scripts/config.json (segunda prioridade)
   Copiar de scripts/config.json.example e preencher

3. Fallback hardcoded (ultimo recurso)
   Aponta para ambiente Carmel Hoteis / VerdanaDesk legado
```

---

## Arquivos de Portabilidade Criados

| Arquivo | Proposito |
|---------|-----------|
| `scripts/config.json.example` | Template de configuracao com placeholders |
| `.gitignore` | Exclui config.json, dados processados, cache Python |
| `requirements.txt` | Dependencias minimas (core = stdlib; RAG = chromadb + sentence-transformers) |
| `README.md` | Instrucoes completas de setup para qualquer ambiente |

---

## Correcoes Aplicadas

### incremental-update.py — URL hardcoded removida
- **Problema:** A secao `## Referencias Cruzadas` usava URL fixa `https://carmelhoteis.verdanadesk.com/front/ticket.form.php?id={tid}`.
- **Solucao:** Importar `GLPI_BASE_URL` de `_env.py` e construir `GLPI_TICKET_URL` dinamicamente.
- **Commit relevante:** `gerar_md()` agora usa `f"{GLPI_TICKET_URL}{tid}"`.

### tag-manager.py — mensagem de erro desnecessariamente especifica
- **Problema:** Mensagem de erro mencionava "Config.yaml do Hermes" como opcao obrigatoria, dando impressao de dependencia exclusiva.
- **Solucao:** Generalizado para "Config.yaml do Hermes (se estiver usando Hermes Agent)" — preserva funcionalidade sem exigir Hermes.

### _env.py — auto-deteccao de paths
- Ja funcionava corretamente em qualquer ambiente via `os.path.dirname(os.path.abspath(__file__))`.
- Nenhuma mudanca necessaria.

---

## Checklist de Setup em Novo Ambiente

```bash
# 1. Clone ou copie o diretorio da skill
cp -r verdanadesk-chamados ~/projetos/
cd ~/projetos/verdanadesk-chamados

# 2. Configure credenciais
cp scripts/config.json.example scripts/config.json
# Edite scripts/config.json com URLs e tokens do seu GLPI

# 3. (Opcional) Instale deps RAG
pip install chromadb sentence-transformers

# 4. Teste basico
py scripts/incremental-update.py --help
py scripts/_env.py  # valida importacao
```

---

## Integracao com Agentes Especificos

### Claude Code
Criar arquivo `.claude/CLAUDE.md` no workspace do usuario. O README.md contem template completo. Resumo:

```markdown
# Skill: VerdanaDesk Chamados
Diretorio: /caminho/completo/para/verdanadesk-chamados
Comandos: py scripts/incremental-update.py, py scripts/analyze-backlog.py, etc.
Regra principal: nunca commite scripts/config.json
```

### Roo Code / VSCode
Criar arquivo `.roo/rules/verdanadesk.md`. O README.md contem template completo. Resumo:

```markdown
# VerdanaDesk Chamados
Contexto: pipeline GLPI em /caminho/verdanadesk-chamados
Scripts: incremental-update.py, analyze-backlog.py, rag-build.py, rag-query.py, tag-manager.py
Config: scripts/config.json (nao versionar)
```

---

## Portabilidade de Paths (testado)

| Ambiente | Path base | Resultado |
|----------|-----------|-----------|
| Windows nativo | `C:\Users\jadson.morais\...` | OK — `os.path.expanduser()` e `os.path.abspath(__file__)` resolvem corretamente |
| WSL | `/mnt/c/Users/...` | OK — mesma logica de path relativo |
| macOS/Linux | `/Users/jadson/...` ou `/home/jadson/...` | OK — forward slash funciona em Python em todos os OS |

Pitfall conhecido: nunca usar formato MSYS/Git Bash `/c/Users/...` em scripts Python nativos Windows — resulta em path invalido `C:\c\Users\...`.

---

## Variaveis de Ambiente — Mapeamento Completo

| Variavel | Script(s) | Descricao |
|----------|-----------|-----------|
| `VERDANADESK_URL_LIST` | `_env.py` → `incremental-update.py`, `analyze-backlog.py`, `process_bulk.py` | Endpoint lista de tickets (dashboard plugin) |
| `VERDANADESK_URL_BULK` | `_env.py` → `incremental-update.py`, `analyze-backlog.py`, `process_bulk.py` | Endpoint bulk de interacoes (dashboard plugin) |
| `GLPI_BASE_URL` | `_env.py` → todos os scripts de dados | URL base do GLPI (frontend + construcao de links) |
| `GLPI_APP_TOKEN` | `tag-manager.py` | App token REST API (`apirest.php`) |
| `GLPI_USER_TOKEN` | `tag-manager.py` | User token REST API (`apirest.php`) |
| `GLPI_URL` | `tag-manager.py` | URL base do GLPI via REST (sinonimo de GLPI_BASE_URL para REST) |

---

## Notas de Versionamento

- **v1.10.0** — Adicionada secao completa de portabilidade cross-agent no SKILL.md.
- Arquivos adicionados: README.md, requirements.txt, .gitignore.
- Skill funciona 100% standalone sem Hermes desde que `scripts/config.json` ou variaveis de ambiente estejam configuradas.
