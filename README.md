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
├── scripts/                 → todos os scripts Python
│   ├── _env.py              → configuração de ambiente (URLs, tokens)
│   ├── config.json.example  → template de configuração
│   ├── incremental-update.py → processamento incremental de tickets
│   ├── analyze-backlog.py   → análise quantitativa de backlog
│   ├── rag-build.py         → constrói/atualiza índice vetorial
│   ├── rag-query.py         → busca semântica e por gravidade
│   ├── tag-manager.py       → gerencia etiquetas GLPI via REST
│   └── rag_lib/             → módulos internos do RAG
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

## Tokens e Segurança

- `scripts/config.json` está no `.gitignore` — nunca será commitado acidentalmente
- Tokens de dashboard (`graphic.json.php`) são diferentes dos tokens de API REST (`apirest.php`)
- Tokens expiram periodicamente — renove-os no GLPI se receber erros 403/404

---

## Licença

Uso interno. Desenvolvido para gestão ITIL de chamados GLPI/VerdanaDesk.
