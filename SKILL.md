---
name: verdanadesk-chamados
title: "Análise de Chamados VerdanaDesk"
version: "2.0.0"
description: >
  Pipeline completo para processar chamados GLPI (VerdanaDesk): geração de .md
  individuais com análise estruturada, análise quantitativa de backlog, RAG semântico,
  saneamento de órfãos ITIL e gestão de base de conhecimento KCS.
triggers:
  - "Usuário pede para processar ou atualizar chamados"
  - "Usuário quer buscar chamados similares ou por gravidade"
  - "Usuário pede análise do backlog ou plano de ação"
  - "Usuário quer criar Problem, Change ou vincular chamados"
  - "Usuário quer tratar chamados órfãos"
requirements:
  - "Windows: `py` disponível (não `python3`)"
  - "Para RAG: `py -m pip install chromadb sentence-transformers`"
  - "Credenciais em `scripts/config.json` ou `.env` na raiz do projeto"
pitfalls:
  - "Tokens expiram — se 403/404, renovar no GLPI e atualizar scripts/config.json."
  - "Filtro `lessthan` no campo 12 (status) da search API é instável. Consultar cada status (1,2,3,4) individualmente."
  - "Campos de análise do Problem são `symptomcontent`, `causecontent`, `impactcontent` — não `symptoms`/`cause`/`impact`."
  - "Change não tem campo `tickets_id` direto — requer Change_Ticket + Change_Problem + Change_User separados."
  - "Bulk tagging PluginTagTagItem: `Duplicate entry` é benigno (item já tem a tag). Não abortar o loop."
  - "python -c com aspas no PowerShell causa erro de ScriptBlock. Sempre salvar em .py e executar diretamente."
  - "NUNCA commitar scripts/config.json — contém tokens de acesso."
  - "Plugin Tag não tem endpoint nativo — usar REST direto via PluginTagTagItem. Ver references/tags-api.md."
---

# Análise de Chamados VerdanaDesk

## Princípios
- **Texto puro**: sem HTML nas respostas. Usar `---`, tabelas simples, separadores `===`.
- **Foco técnico**: resultado direto, sem prolixidade.
- **Órfãos**: ao encontrar tickets sem Problem, agrupar por sistema antes de criar novos Problems.

## Diretório de trabalho
```
c:\projetos\carmel\glpi\
├── data/          → .md individuais, index.md, insights.md, vectordb/
├── scripts/       → scripts Python + rag_lib/
└── references/    → documentação de decisões e referências técnicas
```

---

## Comandos rápidos

| Comando | O que faz |
|---------|-----------|
| `py scripts/incremental-update.py` | Sincroniza tickets novos/atualizados → .md |
| `py scripts/incremental-update.py --force-all` | Reprocessa todos |
| `py scripts/analyze-backlog.py` | Gera `data/plano-de-acao.md` |
| `py scripts/rag-build.py` | Constrói/atualiza índice vetorial |
| `py scripts/rag-query.py "query" --mode gravity --top 10` | Busca por gravidade |
| `py scripts/tag-manager.py tags` | Lista etiquetas disponíveis |
| `py scripts/tag-manager.py assign --itemtype Ticket --items-id ID --tag-id ID` | Atribui etiqueta |
| `py scripts/_orphans.py` | Lista tickets sem vínculo a Problem |

---

## Fluxo de uso

### 1 — Atualizar tickets
```
py scripts/incremental-update.py
```
Preserva seções analíticas já preenchidas. Atualiza embeddings RAG ao terminar.

### 2 — Analisar ticket (LLM)
Ler `## Linha do Tempo` e preencher: Resumo Executivo, Contexto do Negócio,
Decisões Técnicas, Bloqueios & Dependências, Próximos Passos.

### 3 — Backlog quantitativo
```
py scripts/analyze-backlog.py
```

### 4 — RAG busca semântica
```
py scripts/rag-query.py "descrição" --mode similar
py scripts/rag-query.py "query"     --mode gravity --top 10
py scripts/rag-query.py "problema"  --mode history
py scripts/rag-query.py --ticket ID --mode dedup
```
Filtros: `--local`, `--status`, `--tecnico`, `--sistema`, `--tipo`, `--top N`

### 5 — Etiquetas estratégicas
```
py scripts/tag-manager.py list   --itemtype Ticket --items-id ID
py scripts/tag-manager.py assign --itemtype Ticket --items-id ID --tag-id ID
py scripts/tag-manager.py remove --tag-item-id ID
```
Etiquetas principais: 204=Em Análise, 205=Aguardando Fornecedor, 210=Em Andamento,
217=Em planejamento, 222=Backlog, 235=Acessos. Ver catálogo completo: `references/tags-api.md`

Cadeia ITIL — etiquetar os três níveis com a mesma tag:
```
Ticket → Problem → Change   (todos recebem a mesma tag estratégica)
```

### 6 — ITIL (Problems, Changes, KB)
Ver `references/itil-rest.md` para endpoints completos de Problem/Change/KCS.

---

## Saneamento de Órfãos — Mapeamento de Clusters

| Termo no título/conteúdo | Problem ID | Cluster |
|--------------------------|:----------:|---------|
| "Almoxarifado" | 235 | Ajustes Almoxarifado CMFlex |
| "Compras", "Orçamento" | 247 | Módulo Compras CMFlex |
| "Tablet", "Micros" | 237 | Tablets/Micros |
| "Opera" | 242 | Opera Cloud PMS |
| "FNRH", "SNRHo" | 244 | Compliance FNRH |
| "BI", "Power BI", "Relatório" | 252 | Sustentação BI/DW |
| "Access Points", "Rede", "VPN" | 245 | Infraestrutura de Rede |
| "Telefonia", "Ramal" | 246 | Sistemas de Telefonia |
| "CMFlex lento", "desempenho", "módulo trava" | 260 | CMFlex SaaS — Desempenho intermitente |
| "BPM", "instância duplicada", "aprovação duplicada" | 261 | CMFlex BPM — Múltiplas instâncias |
| "comanda", "integraliza", "cupom não migra" | 262 | Simphony × CMFlex — Integração Fiscal |
| "ponto eletrônico", "batida de ponto", "RHID" | 263 | RHID — Conectividade DP/RH |
| "migração servidor", "servidor resort" | 264 | Infra — Migração servidores resorts |
| "XML Sefaz", "Harmonized", "CAPS" | 265 | Simphony — Payload XML inválido Sefaz |
| Acessos/login/senha (sem Problem obrigatório) | — | Etiqueta "Acessos" (tag 235) |

---

## Referências

| Arquivo | Conteúdo |
|---------|----------|
| `references/itil-rest.md` | Endpoints Problem/Change/KCS, categorias ITIL, busca de órfãos |
| `references/tags-api.md` | Catálogo completo de etiquetas e API PluginTagTagItem |
| `references/mcp-glpi-integration.md` | Ferramentas MCP disponíveis |
| `references/rag-native-windows.md` | RAG no Windows nativo, gravity score, metadados de chunk |
| `references/endpoint-types.md` | Tipos de retorno dos endpoints VerdanaDesk |
| `references/saneamento-backlog-maio-2026.md` | Estratégia de clusterização de órfãos |
| `references/portability-cross-agent.md` | Setup para Claude Code, Roo Code, CLI puro |
| `references/incremental-processing-recipe.md` | Algoritmo incremental e formato index.md v2 |
