# glpi_core

Biblioteca Python para automação determinística da API REST do GLPI. Cria projetos,
tarefas e tags via comandos versionados, sem dependência de IA ou interação manual.

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração de credenciais

A biblioteca resolve credenciais nesta ordem de prioridade:

**1. Variáveis de ambiente**
```bash
set GLPI_APP_TOKEN=seu_app_token
set GLPI_USER_TOKEN=seu_user_token
set GLPI_URL=https://glpi.exemplo.com
```

**2. Arquivo `scripts/config.json`** (não versionado)
```json
{
  "app_token": "seu_app_token",
  "user_token": "seu_user_token",
  "glpi_base_url": "https://glpi.exemplo.com"
}
```

**3. Arquivo `.env` na raiz do repositório**
```env
GLPI_APP_TOKEN="seu_app_token"
GLPI_USER_TOKEN="seu_user_token"
GLPI_URL="https://glpi.exemplo.com"
```

Se nenhuma fonte encontrar as credenciais, o script encerra com mensagem de erro.

---

## CLI

```
python glpi_core/cli.py <comando> [--payload '{"chave": "valor"}'] [--payload-file payload.json] [--dry-run]
```

| Flag | Descrição |
|------|-----------|
| `--list` | Lista todos os comandos disponíveis |
| `--payload` | Payload JSON inline |
| `--payload-file` | Caminho para arquivo `.json` com o payload |
| `--dry-run` | Simula sem chamar a API real; imprime as chamadas HTTP que seriam feitas |

### Listar comandos disponíveis

```bash
python glpi_core/cli.py --list
```

---

## Comandos disponíveis

### `project_overview`

Retorna o estado atual de um projeto: tarefas por status, milestones pendentes,
tarefas sem DoD, sem tag de governança e tarefas bloqueadas.

```bash
python glpi_core/cli.py project_overview \
  --payload '{"project_id": 256, "id_range": [100, 200]}'
```

**Retorno:**
```json
{
  "project_id": 256,
  "tasks_total": 18,
  "tasks_by_status": {"1": [...], "sem_status": [...]},
  "milestones_pending": ["Rollout Realizado"],
  "tasks_missing_dod": [{"id": 112, "name": "..."}],
  "tasks_missing_tag": [{"id": 118, "name": "..."}],
  "tasks_blocked": []
}
```

Use como primeiro passo antes de qualquer operação em massa para entender o estado real do projeto.

---

### `apply_template_to_project`

Aplica um template JSON criando a árvore de `ProjectTask` dentro de um projeto
existente ou novo.

**Usar projeto existente (ex.: Projeto #256):**
```bash
python glpi_core/cli.py apply_template_to_project \
  --payload '{"template": "fases_padrao", "project_id": 256}'
```

**Criar projeto novo:**
```bash
python glpi_core/cli.py apply_template_to_project \
  --payload '{"template": "infra_deploy", "project_overrides": {"name": "[Infra] Migração Switch Core"}}'
```

**Simular antes de executar (recomendado):**
```bash
python glpi_core/cli.py apply_template_to_project \
  --payload '{"template": "fases_padrao", "project_id": 256}' \
  --dry-run
```

**Templates disponíveis:**

| Nome | Descrição |
|------|-----------|
| `fases_padrao` | 5 fases genéricas (F1–F5) com 3 marcos de aprovação e DoD padrão |
| `simphony_pos_rollout` | Árvore completa de rollout POS/Simphony com sub-fases |
| `infra_deploy` | Projeto de infraestrutura (rede, servidor, migração): 4 marcos + F1–F5 |

---

### `bulk_tag_project`

Atribui uma tag de governança a **todas** as tarefas de um projeto de uma vez,
sem precisar listar IDs manualmente.

```bash
python glpi_core/cli.py bulk_tag_project \
  --payload '{"project_id": 256, "id_range": [100, 200], "tag": "Planejado"}'
```

---

### `bulk_apply_dod_to_project`

Injeta o checklist de Definition of Done em todas as tarefas de um projeto que
ainda não têm checklist. A fase é inferida automaticamente pelo prefixo `F<n>`
do nome da tarefa. Milestones são ignorados.

```bash
python glpi_core/cli.py bulk_apply_dod_to_project \
  --payload '{"project_id": 256, "id_range": [100, 200]}'
```

**Retorno:**
```json
{
  "project_id": 256,
  "updated": [{"id": 112, "name": "..."}],
  "skipped": [{"id": 101, "name": "...", "reason": "dod_already_present"}]
}
```

Motivos de `skipped`: `dod_already_present`, `phase_not_inferred`, `is_milestone`.

---

### `bulk_apply_dod`

Injeta DoD em uma lista específica de task IDs. Idempotente: tarefas que já têm
`[ ]` no conteúdo são ignoradas.

**Por lista de IDs:**
```bash
python glpi_core/cli.py bulk_apply_dod \
  --payload '{"task_ids": [101, 102, 103], "phase": "1"}'
```

**Por range de IDs do projeto** (útil quando o projeto não foi criado por este pacote):
```bash
python glpi_core/cli.py bulk_apply_dod \
  --payload '{"project_id": 256, "id_range": [100, 150], "phase": "2"}'
```

**Fases e seus DoD:**

| Fase | Critérios |
|------|-----------|
| F1 | Evidência anexada, responsável e data registrados |
| F2 | Evidência anexada, responsável e data registrados |
| F3 | Documento de definição aprovado, validação registrada |
| F4 | Log/print do teste funcional, horário e responsável |
| F5 | Artigo de KB publicado, link anexado |

---

### `bulk_rename_tasks`

Aplica um prefixo de nomenclatura em massa em tarefas existentes. Idempotente:
tarefas que já têm o prefixo são ignoradas.

```bash
python glpi_core/cli.py bulk_rename_tasks \
  --payload '{"task_ids": [101, 102, 103], "prefix": "[POS/Simphony]"}'
```

O prefixo é aplicado apenas em tarefas cujo nome segue o padrão `F<n> - Descrição`.

---

### `bulk_tag_tasks`

Atribui uma tag de governança a uma lista específica de itens. Resolve o ID da
tag uma única vez.

```bash
python glpi_core/cli.py bulk_tag_tasks \
  --payload '{"items_ids": [101, 102, 103], "tag": "Planejado", "itemtype": "ProjectTask"}'
```

**Tags disponíveis:**

| Tag | Uso |
|-----|-----|
| `Break-Fix` | Suporte reativo — concorre na fila/SLA de incidente crítico |
| `Planejado` | Entrega de engenharia/evolução — não mistura com incidente |
| `Projeto` | Mesmo espírito de `Planejado`, para quando já existe um `Project` no GLPI |
| `Blocked` | Impedimento por dependência externa (fornecedor, acesso não liberado) |

O campo `itemtype` é opcional; padrão: `"ProjectTask"`. Aceita também `"Ticket"`,
`"Problem"`, `"Change"`.

---

## Templates JSON

Templates ficam em `glpi_core/templates/*.json` e descrevem uma árvore de tarefas
validada pelo schema `ProjectTemplateSchema`.

**Estrutura básica:**
```json
{
  "template_name": "meu_template",
  "description": "Descrição do template",
  "project_defaults": {
    "name": "Nome Padrão do Projeto",
    "entities_id": 1
  },
  "nodes": [
    {
      "name": "Marco de Aprovação",
      "is_milestone": true
    },
    {
      "name": "F1 - Levantamento",
      "phase": "1",
      "tag": "Planejado",
      "content": "Descrição da tarefa.\nMáximo 80 chars por linha.",
      "children": [
        {
          "name": "[Sistema] F1.1 - Tarefa Filha - Contexto",
          "phase": "1",
          "tag": "Planejado"
        }
      ]
    }
  ]
}
```

**Campos de um nó (`TaskTemplateNode`):**

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `name` | string | Obrigatório. Padrão: `F<n> - Desc` (fase) ou `[Sistema] F<n> - Acao` (leaf) |
| `phase` | `"1"`–`"5"` | Define qual DoD será injetado ao criar a tarefa |
| `tag` | `GovernanceTag` | Tag de governança a atribuir após a criação |
| `is_milestone` | bool | Marco de aprovação; não recebe DoD |
| `content` | string | Conteúdo inicial. Máximo 80 chars por linha — use `\n` para quebrar |
| `children` | lista | Sub-tarefas (recursivo) |
| demais campos | — | Campos graváveis da API: `plan_start_date`, `users_id`, `projectstates_id`, etc. |

**Carregar e validar um template via Python:**
```python
from glpi_core.templates import TemplateRepository

template = TemplateRepository.load("infra_deploy")
print(template.template_name, len(template.nodes), "nós")
```

**Adicionar um template novo:**
1. Copie um `.json` existente como base.
2. Ajuste `nodes` (com `children` recursivos se necessário).
3. Mantenha `content` em no máximo 80 chars por linha (quebras com `\n`).
4. Valide com `TemplateRepository.load("nome_do_arquivo")`.
5. Teste com `--dry-run` antes de rodar contra o GLPI real.

---

## Uso via Python

```python
from glpi_core.command_handler import CommandContext, dispatch
from glpi_core.config import load_credentials
from glpi_core.connection.client import GLPIClient
from glpi_core.macros import apply_template, bulk_ops, query_ops  # registra os comandos

creds = load_credentials()
with GLPIClient(creds) as client:
    ctx = CommandContext(client)

    # Ver estado atual do projeto
    overview = dispatch("project_overview", {"project_id": 256, "id_range": [100, 200]}, ctx)

    # Aplicar template num projeto existente
    result = dispatch(
        "apply_template_to_project",
        {"template": "infra_deploy", "project_id": 256},
        ctx,
    )
    print(result)
```

---

## Nomenclatura de tarefas

Regra definida em `rules.md` e validada em `TaskCreateSchema`:

- **Fase (container):** `F<n> - Descrição curta`
  Ex: `F1 - Levantamento de Requisitos`

- **Tarefa leaf (execução):** `[Sistema/Área] F<n>.<sub> - Ação - Contexto`
  Ex: `[POS/Simphony] F2.1 - Inventario GLPI - Impressoras`

Use `build_task_name` para montar o título no formato padrão:
```python
from glpi_core.schemas.governance import build_task_name

nome = build_task_name("POS/Simphony", "Instalar Workstation", "Restaurante")
# "[POS/Simphony] - Instalar Workstation - Restaurante"
```

A fase é inferida automaticamente do nome pelo prefixo `F<n>` (usado por
`bulk_apply_dod_to_project`). Nomes sem esse prefixo não recebem DoD automático.

---

## Arquitetura resumida

```
cli.py                → entrypoint CLI
command_handler.py    → dispatcher (register_macro / dispatch)
config.py             → resolução de credenciais
connection/
  client.py           → HTTP puro (autenticação + transporte)
  dry_run.py          → cliente de simulação (--dry-run)
schemas/
  task.py             → TaskCreateSchema, TaskReadSchema, DOD_BY_PHASE
  project.py          → ProjectCreateSchema, ProjectReadSchema
  governance.py       → GovernanceTag, ApprovalMilestone, build_task_name
  template.py         → ProjectTemplateSchema, TaskTemplateNode
  tag.py              → TagAssignSchema, TaggableItemType
services/
  task_service.py     → CRUD de ProjectTask + operações em massa + infer_phase_from_name
  project_service.py  → CRUD de Project
  tag_service.py      → resolução e atribuição de tags
  template_service.py → aplicação de templates
macros/
  apply_template.py   → apply_template_to_project
  bulk_ops.py         → bulk_rename_tasks, bulk_apply_dod, bulk_tag_tasks
  query_ops.py        → project_overview, bulk_tag_project, bulk_apply_dod_to_project
templates/
  fases_padrao.json         → 5 fases genéricas + 3 marcos
  simphony_pos_rollout.json → rollout POS/Simphony completo
  infra_deploy.json         → projeto de infraestrutura (rede/servidor/migração)
```

---

## Fluxo para adicionar uma nova macro

1. Definir o schema de entrada em `schemas/` (Pydantic).
2. Implementar a lógica em `services/` — sem chamadas HTTP diretas na macro.
3. Criar a macro em `macros/<contexto>.py` com `@register_macro("nome_do_comando")`.
4. Importar o módulo em `cli.py` para que o decorator seja executado.
5. Adicionar teste em `tests/` cobrindo o caminho feliz e ao menos uma falha de validação.

---

## Tokens expirados

Se a API retornar `403` ou `401`, renove os tokens no GLPI e atualize a fonte de
credenciais configurada (`scripts/config.json`, `.env` ou variáveis de ambiente).
