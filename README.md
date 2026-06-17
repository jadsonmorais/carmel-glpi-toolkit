# VerdanaDesk Chamados — Pipeline de Análise GLPI

Pipeline completo para processar chamados GLPI/VerdanaDesk: geração de `.md`
individuais com análise estruturada, base central de insights, análise
quantitativa de backlog, RAG semântico para busca por similaridade/gravidade,
e sistema de etiquetas para filtragem e categorização estratégica.

---

## Estrutura

```
.
├── data/                    → arquivos .md individuais, index.md, insights.md
│   └── vectordb/            → índice ChromaDB (RAG) — gerado localmente
├── scripts/                 → scripts Python pontuais (sem validação/CRUD estruturado)
│   ├── _env.py              → configuração de ambiente (URLs, tokens)
│   ├── config.json.example  → template de configuração
│   ├── incremental-update.py → processamento incremental de tickets
│   ├── analyze-backlog.py   → análise quantitativa de backlog
│   ├── rag-build.py         → constrói/atualiza índice vetorial
│   ├── rag-query.py         → busca semântica e por gravidade
│   ├── tag-manager.py       → gerencia etiquetas GLPI via REST
│   └── rag_lib/             → módulos internos do RAG
├── glpi_core/                → CRUD/macros determinístico para Projetos e ProjectTasks (ver seção própria abaixo)
│   ├── schemas/              → contratos Pydantic (Project, ProjectTask, Tag, Governança, Template)
│   ├── connection/           → cliente HTTP do GLPI (real e dry-run)
│   ├── services/             → CRUD + regras de negócio (Project, Task, Tag, Template)
│   ├── macros/               → orquestração de comandos compostos (templates, operações em massa)
│   ├── templates/             → templates JSON reutilizáveis de projeto/tarefas
│   ├── command_handler.py    → dispatcher único de comandos
│   ├── cli.py                → entrypoint `python -m glpi_core.cli`
│   └── rules.md              → regras de governança, nomenclatura e fluxo p/ novas macros/templates
├── tests/                    → testes do glpi_core (pytest, sem chamadas HTTP reais)
├── templates/               → templates markdown para geração de conteúdo
├── references/              → documentação arquitetural e decisões
├── requirements.txt         → dependências Python
└── README.md                → este arquivo
```

---

## Setup Rápido

### 1. Clone ou copie a skill

```bash
cp -r verdanadesk-chamados ~/projetos/
cd ~/projetos/carmel/glpi
```

### 2. Configure o acesso ao GLPI

Copie o template e preencha com seus dados:

```bash
cp scripts/config.json.example scripts/config.json
```

Edite `scripts/config.json`:

```json
{
  "url_list": "https://SEU-GLPI/plugins/utilsdashboards/front/ajax/graphic.json.php?token=SEU_TOKEN_LISTA",
  "url_bulk": "https://SEU-GLPI/plugins/utilsdashboards/front/ajax/graphic.json.php?token=SEU_TOKEN_BULK",
  "glpi_base_url": "https://SEU-GLPI",
  "app_token": "SEU_APP_TOKEN_REST",
  "user_token": "SEU_USER_TOKEN_REST"
}
```

**IMPORTANTE:** Nunca commite `scripts/config.json`. Ele já está no `.gitignore`.

#### Alternativa: variáveis de ambiente

Se preferir não usar o arquivo `config.json`, exporte:

```bash
export VERDANADESK_URL_LIST="https://..."
export VERDANADESK_URL_BULK="https://..."
export GLPI_BASE_URL="https://SEU-GLPI"
export GLPI_APP_TOKEN="..."
export GLPI_USER_TOKEN="..."
export GLPI_URL="https://SEU-GLPI"   # usado pelo tag-manager.py
```

### 3. Instale dependências (apenas para RAG)

Os scripts core (`incremental-update.py`, `analyze-backlog.py`, `tag-manager.py`)
usam apenas a biblioteca padrão do Python. As dependências extras são só para
RAG (busca semântica):

```bash
pip install -r requirements.txt
```

Ou, se preferir instalar só o core:

```bash
# Nada a instalar — usa apenas stdlib
```

---

## Migração entre máquinas / Compartilhamento com devs

Este repositório não contém `.env`, `scripts/config.json` nem `data/` (tickets,
índice RAG etc.) — tudo isso é ignorado pelo git por conter credenciais e dados
de negócio. Para levar esse conteúdo de uma máquina para outra (ou compartilhar
com outro dev), use os scripts de export/import:

### Na máquina de origem (gerar o pacote)

```bash
py scripts/export-local-data.py
```

Gera `dumps/glpi-local-data_<timestamp>.zip` com tudo que está fora do git
(`.env`, `data/`, dumps `_*.txt`). Envie esse zip para o destino (Drive,
pendrive, etc.).

### Na máquina de destino (restaurar)

```bash
# 1. Clonar o repositório
git clone git@github.com:jadsonmorais/carmel-glpi-toolkit.git carmel/glpi
cd carmel/glpi

# 2. Instalar dependências
py -m pip install -r requirements.txt

# 3. Copiar o zip recebido para dumps/ e restaurar
py scripts/import-local-data.py
```

O script lista o conteúdo do zip e pede confirmação antes de extrair
(`.env`, `data/*.md`, vectordb etc.).

### Validar

```bash
py scripts/_orphans.py
# ou
py scripts/analyze-backlog.py
```

Se rodar sem erro de token/config, a restauração funcionou.

---

## Uso

### Processamento incremental de tickets

```bash
# Windows
py scripts/incremental-update.py

# Linux/macOS
python3 scripts/incremental-update.py
```

Reprocessa todos (preservando seções analíticas preenchidas):

```bash
py scripts/incremental-update.py --force-all
```

### Análise de backlog

```bash
py scripts/analyze-backlog.py
```

Gera `data/plano-de-acao.md` com panorama quantitativo.

### Busca semântica (RAG)

```bash
# Construir índice
py scripts/rag-build.py --rebuild

# Buscar
py scripts/rag-query.py "descrição do problema"

# Modos disponíveis
py scripts/rag-query.py "query" --mode similar      # padrão
py scripts/rag-query.py "query" --mode gravity --top 10
py scripts/rag-query.py "query" --mode history
py scripts/rag-query.py --ticket 12345 --mode dedup
```

### Gerenciamento de etiquetas

```bash
# Listar etiquetas disponíveis
py scripts/tag-manager.py tags

# Atribuir etiqueta
py scripts/tag-manager.py assign --itemtype Ticket --items-id 12345 --tag-id 204

# Listar etiquetas de um ticket
py scripts/tag-manager.py list --itemtype Ticket --items-id 12345
```

---

## glpi_core — CRUD/macros determinístico para Projetos e Tarefas

Pacote Python separado dos scripts soltos de `scripts/`, focado em **criar e
manter em massa a estrutura de Projetos/ProjectTasks do GLPI** (fases,
milestones de aprovação, Definition of Done e tags de governança) de forma
validada (Pydantic) e 100% determinística — sem depender de IA em runtime.
Ver `glpi_core/rules.md` para o racional completo de nomenclatura, tags e DoD.

### Templates JSON

Em vez de escrever uma macro Python nova para cada projeto, descreva a árvore
de tarefas em JSON (`glpi_core/templates/*.json`) e aplique com a macro
genérica `apply_template_to_project`:

```bash
# Cria um Project novo a partir do template "fases_padrao" (3 marcos + 5 fases)
py -m glpi_core.cli apply_template_to_project \
  --payload-file payload_demo_256.json --dry-run

# Aplica o template "simphony_pos_rollout" (árvore completa de 40 tarefas)
# dentro de um Project que já existe no GLPI (project_id), sem criar um novo
py -m glpi_core.cli apply_template_to_project \
  --payload-file payload_demo_simphony_existing.json --dry-run
```

Remova `--dry-run` para executar de fato contra o GLPI (usa as credenciais de
`glpi_core/config.py`, mesma lógica de resolução de `_env.py`/`config.json`).

Templates disponíveis: `glpi_core/templates/fases_padrao.json` (genérico) e
`glpi_core/templates/simphony_pos_rollout.json` (rollout de PDV com sub-fases
e marcos de aprovação). Para criar um novo, copie um existente, ajuste `nodes`
(cada nó pode ter `children` recursivos, `phase` para herdar o Definition of
Done da fase, e `tag` para a etiqueta de governança a aplicar) e valide com:

```python
from glpi_core.templates import TemplateRepository
TemplateRepository.load("nome_do_template")  # levanta erro se o JSON for inválido
```

### Operações em massa em tarefas já existentes

```bash
# Lista os comandos disponíveis
py -m glpi_core.cli --list

# Renomeia em massa aplicando um prefixo de nomenclatura
py -m glpi_core.cli bulk_rename_tasks --payload '{"task_ids":[2740,2741],"prefix":"[POS/Simphony]"}' --dry-run

# Atribui uma tag de governança (Planejado/Break-Fix/Projeto/Blocked) em massa
py -m glpi_core.cli bulk_tag_tasks --payload '{"items_ids":[2740,2741],"tag":"Planejado"}' --dry-run

# Injeta o checklist de Definition of Done em tarefas que ainda não têm
py -m glpi_core.cli bulk_apply_dod --payload '{"task_ids":[2740],"phase":"1"}' --dry-run
```

### Testes

```bash
pip install -r requirements.txt   # inclui pydantic e pytest
pytest tests/
```

Os testes usam um `FakeClient`/`DryRunClient` — nenhum chama a API real do
GLPI.

---

## Tokens e Segurança

- `scripts/config.json` está no `.gitignore` — nunca será commitado acidentalmente
- Tokens de dashboard (`graphic.json.php`) são diferentes dos tokens de API REST (`apirest.php`)
- Tokens expiram periodicamente — renove-os no GLPI se receber erros 403/404

---

## Licença

Uso interno. Desenvolvido para gestão ITIL de chamados GLPI/VerdanaDesk.
