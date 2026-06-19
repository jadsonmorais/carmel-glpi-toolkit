# glpi_core — Regra de Uso pelo Agente de IA

**NUNCA crie tarefas, projetos ou atribua tags via script ad-hoc ou chamada HTTP direta.**
Sempre use o pacote `glpi_core`. Ele valida entradas com Pydantic, garante nomenclatura
padrao, injeta DoD por fase e suporta `--dry-run` para simular sem risco.

## Descoberta

```bash
# Listar todos os comandos disponiveis
python -m glpi_core --list

# Listar templates de projeto disponiveis
python -c "from glpi_core.templates import TemplateRepository; print(TemplateRepository.list_available())"
```

## Comandos mais usados

| Comando | Quando usar |
|---------|-------------|
| `apply_template_to_project` | Criar arvore de tarefas num projeto existente ou novo |
| `project_overview` | Ver estado atual de um projeto: DoD pendente, tags ausentes, milestones |
| `bulk_tag_project` | Taguear todas as tarefas de um projeto de uma vez |
| `bulk_apply_dod_to_project` | Injetar DoD em todas as tarefas que ainda nao tem checklist |
| `bulk_apply_dod` | Injetar DoD em uma lista especifica de task IDs |
| `bulk_rename_tasks` | Aplicar prefixo de nomenclatura em massa |
| `bulk_tag_tasks` | Taguear lista especifica de task IDs |

## Exemplos de payload

```bash
# Ver estado de um projeto
python -m glpi_core project_overview \
  --payload '{"project_id": 256, "id_range": [100, 200]}'

# Taguear todo o projeto como Planejado
python -m glpi_core bulk_tag_project \
  --payload '{"project_id": 256, "id_range": [100, 200], "tag": "Planejado"}'

# Injetar DoD em todas as tarefas sem checklist
python -m glpi_core bulk_apply_dod_to_project \
  --payload '{"project_id": 256, "id_range": [100, 200]}'

# Criar projeto de rollout Simphony
python -m glpi_core apply_template_to_project \
  --payload '{"template": "simphony_pos_rollout", "project_id": 256}'

# Criar projeto de infraestrutura novo
python -m glpi_core apply_template_to_project \
  --payload '{"template": "infra_deploy", "project_overrides": {"name": "[Infra] Migração Switch Core"}}'
```

Sempre teste com `--dry-run` antes de executar contra o GLPI real.

---

# Skill: VerdanaDesk Chamados

Diretório: C:\projetos\carmel\glpi

## Propósito
Pipeline de análise de chamados GLPI/VerdanaDesk: geração de .md individuais,
base central de insights, análise quantitativa de backlog, RAG semântico para
busca por similaridade/gravidade, e sistema de etiquetas.

## Comandos principais

| Comando | Descrição |
|---------|-----------|
| `py scripts/incremental-update.py` | Sincroniza tickets do GLPI para .md (só novos/atualizados) |
| `py scripts/incremental-update.py --force-all` | Reprocessa todos os tickets |
| `py scripts/analyze-backlog.py` | Gera `data/plano-de-acao.md` com panorama quantitativo |
| `py scripts/rag-build.py --rebuild` | Constrói índice vetorial para busca semântica |
| `py scripts/rag-query.py "query"` | Busca semântica nos tickets |
| `py scripts/rag-query.py "query" --mode gravity --top 10` | Ranking por gravidade real |
| `py scripts/tag-manager.py tags` | Lista etiquetas disponíveis no GLPI |
| `py scripts/tag-manager.py list --itemtype Ticket --items-id ID` | Lista etiquetas de um ticket |
| `py scripts/tag-manager.py assign --itemtype Ticket --items-id ID --tag-id ID` | Atribui etiqueta |

## Regras

1. **Nunca commite `scripts/config.json`** — contém tokens de acesso. O arquivo já está no `.gitignore`.
2. **Dados processados ficam em `data/`** — não versionar. Contém .md individuais, index.md, insights.md, vectordb/.
3. **Seções analíticas dos .md** (`Resumo Executivo`, `Decisões Técnicas`, `Bloqueios & Dependências`, `Próximos Passos`) são preenchidas pela LLM e **preservadas** pelo script incremental em reprocessamentos.
4. **Tokens expiram** — se retornar 403/404, renovar no GLPI e atualizar `scripts/config.json`.
5. **RAG funciona nativamente no Windows** com Python 3.13+. Em caso de falha, usar `wsl python3 scripts/rag-build.py`.
6. **Todos os scripts resolvem paths relativos ao próprio arquivo** — funcionam em qualquer local do filesystem.

## Estrutura do diretório

```
.
├── data/                    → dados gerados (.md, index, vectordb)
├── scripts/                 → scripts Python
│   ├── _env.py              → configuração de ambiente
│   ├── config.json          → credenciais (não versionar)
│   ├── config.json.example  → template de configuração
│   ├── incremental-update.py
│   ├── analyze-backlog.py
│   ├── rag-build.py
│   ├── rag-query.py
│   ├── tag-manager.py
│   └── rag_lib/             → módulos internos do RAG
├── templates/               → templates de saída
├── references/              → documentação arquitetural
├── requirements.txt         → dependências Python
└── README.md                → documentação completa
```

## Variáveis de ambiente suportadas

| Variável | Usada em | Descrição |
|----------|----------|-----------|
| `VERDANADESK_URL_LIST` | `_env.py` | Endpoint de lista de tickets |
| `VERDANADESK_URL_BULK` | `_env.py` | Endpoint bulk de interações |
| `GLPI_BASE_URL` | `_env.py` | URL base do GLPI |
| `GLPI_APP_TOKEN` | `tag-manager.py` | App token REST API |
| `GLPI_USER_TOKEN` | `tag-manager.py` | User token REST API |
| `GLPI_URL` | `tag-manager.py` | URL base do GLPI (REST) |

Todas são opcionais se `scripts/config.json` estiver preenchido.
