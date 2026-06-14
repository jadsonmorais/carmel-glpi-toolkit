# API REST do Plugin Tag (GLPI)

## Visão Geral

O plugin **Tag** do GLPI permite atribuir etiquetas coloridas a diversos tipos de itens (Ticket, Problem, Change, Computer, etc.). Como não há suporte nativo no MCP GLPI, a manipulação deve ser feita via API REST direta.

**Script utilitário:** `scripts/tag-manager.py` — interface CLI completa para operações com etiquetas.

---

## Estrutura de Dados

### PluginTagTag (Definição da Etiqueta)
```json
{
  "id": 204,
  "entities_id": 0,
  "is_recursive": 1,
  "is_active": 1,
  "name": "Em Análise",
  "comment": "Sendo investigada pela equipe.",
  "color": "#45818e",
  "type_menu": "[\"Ticket\",\"Problem\",\"Change\"]"
}
```

### PluginTagTagItem (Associação Etiqueta ↔ Item)
```json
{
  "id": 16935,
  "plugin_tag_tags_id": 204,
  "itemtype": "Ticket",
  "items_id": 27760
}
```

**Importante:** O `id` do `PluginTagTagItem` é diferente do `plugin_tag_tags_id`. Para remover uma etiqueta, use o `id` da associação, não o ID da etiqueta.

---

## Endpoints da API REST

### 1. Listar todas as etiquetas disponíveis

```bash
curl -s \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Session-Token: $SESSION_TOKEN" \
  "https://SEU_GLPI/apirest.php/PluginTagTag?range=0-999"
```

**Resposta:** Array de `PluginTagTag`

---

### 2. Consultar etiquetas atribuídas a um item

```bash
# Para Ticket
curl -s \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Session-Token: $SESSION_TOKEN" \
  "https://SEU_GLPI/apirest.php/Ticket/{ticket_id}/PluginTagTagItem"

# Para Problem
curl -s \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Session-Token: $SESSION_TOKEN" \
  "https://SEU_GLPI/apirest.php/Problem/{problem_id}/PluginTagTagItem"

# Para Change
curl -s \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Session-Token: $SESSION_TOKEN" \
  "https://SEU_GLPI/apirest.php/Change/{change_id}/PluginTagTagItem"
```

**Resposta:** Array de `PluginTagTagItem` (apenas associações, sem detalhes da etiqueta)

---

### 3. Atribuir etiqueta a um item

```bash
curl -s \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Session-Token: $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d '{
    "input": {
      "itemtype": "Ticket",
      "items_id": 27760,
      "plugin_tag_tags_id": 204
    }
  }' \
  "https://SEU_GLPI/apirest.php/PluginTagTagItem"
```

**Resposta de sucesso:**
```json
{
  "id": 16935,
  "message": "Item adicionado com sucesso: Etiqueta - ID 16935"
}
```

**Nota:** Um item pode ter múltiplas etiquetas simultaneamente. Chamar este endpoint múltiplas vezes com tags diferentes adiciona todas.

---

### 4. Remover etiqueta de um item

```bash
curl -s \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Session-Token: $SESSION_TOKEN" \
  -X DELETE \
  "https://SEU_GLPI/apirest.php/PluginTagTagItem/{tag_item_id}"
```

**Resposta de sucesso:**
```json
[{"16935": true, "message": ""}]
```

**Cuidado:** Use o `id` da associação (retornado no passo 2 ou 3), não o `id` da etiqueta.

---

## Autenticação

### Inicializar sessão

```bash
curl -s \
  -H "App-Token: SEU_APP_TOKEN" \
  -H "Authorization: user_token SEU_USER_TOKEN" \
  "https://SEU_GLPI/apirest.php/initSession"
```

**Resposta:**
```json
{
  "session_token": "cnVLSExzaXdBUWZWRTVIQ0pPK2tGcTRaMk1LcHlJT1MvSXZWOGw1WDJqcHphOTBJUFpYWGhvVEtPczJDVW9sTVByUGdMN3RhVEFvZkFlWEtHZDdFMW9WZw=="
}
```

Use este `session_token` em todas as requisições subsequentes.

---

## Script `tag-manager.py`

### Instalação
O script já está pronto em `scripts/tag-manager.py`. Não requer instalação adicional — usa apenas bibliotecas padrão do Python.

### Uso

```bash
# Listar catálogo completo de etiquetas
py scripts/tag-manager.py tags

# Filtrar etiquetas por nome
py scripts/tag-manager.py tags --name Analise

# Consultar etiquetas de um ticket
py scripts/tag-manager.py list --itemtype Ticket --items-id 27760

# Atribuir etiqueta
py scripts/tag-manager.py assign --itemtype Ticket --items-id 27760 --tag-id 204

# Remover atribuição
py scripts/tag-manager.py remove --tag-item-id 16935
```

### Como funciona

1. **Carrega credenciais** automaticamente de `~/.hermes/config.yaml` (GLPI_APP_TOKEN, GLPI_USER_TOKEN, GLPI_URL)
2. **Inicializa sessão** GLPI via API REST
3. **Executa operação** solicitada (list/assign/remove)
4. **Formata saída** em tabela legível

### Exemplo de saída

```
$ py scripts/tag-manager.py tags
ID  | Nome                           | Cor       | Aplicável a
--------------------------------------------------------------------------------
 203 | Aberta                         | #45818e   | Ticket, Problem, Change
 204 | Em Análise                     | —         | Ticket, Problem, Change
 205 | Aguardando Fornecedor          | #f1c232   | Ticket, Problem, Change
```

---

## Catálogo Completo de Etiquetas

### Etiquuetas de Fluxo de Trabalho (Ticket/Problem/Change)

| ID  | Nome                           | Cor       | Comentário                                      |
|-----|--------------------------------|-----------|-------------------------------------------------|
| 203 | Aberta                         | #45818e   | Recém-registrada, aguardando análise ou ação    |
| 204 | Em Análise                     | —         | Sendo investigada pela equipe                   |
| 205 | Aguardando Fornecedor          | #f1c232   | A ação depende de um fornecedor externo         |
| 206 | Aguardando Requerente          | #8e7cc3   | A ação depende do requerente (ex: mais info)    |
| 207 | Em Homologação/Testes          | —         | A solução está pronta e aguardando validação    |
| 208 | Concluída                      | #6aa84f   | A demanda foi totalmente resolvida              |
| 209 | Cancelada                      | #cc0000   | A demanda foi descartada                        |
| 210 | Em Andamento                   | #0b5394   | Trabalho ativo em execução                      |
| 211 | Aguardando Colaboração Interna | #f1c232   | Depende de outro setor interno                  |
| 212 | Solucionar                     | #fff2cc   | Prioridade para resolução                       |
| 217 | Em planejamento                | #a64d79   | Fase de planejamento/projeto                    |
| 218 | SCI                            | #274e13   | Sistema de Controle Interno                     |
| 219 | Solucionado                    | —         | Resolução técnica implementada                  |
| 222 | Backlog                        | #2986cc   | Item de backlog/fila                            |
| 223 | Erro de Cadastro Simphony      | #f44336   | Problema específico de cadastro Simphony        |
| 229 | Cadastro FNRH                  | #fff2cc   | Problema específico de cadastro FNRH            |
| 233 | Problema                       | #f44336   | Classificação genérica de problema              |

### Etiquetas para Inventário (Computer)

| ID  | Nome                | Cor       | Comentário                                      |
|-----|---------------------|-----------|-------------------------------------------------|
| 214 | Alerta de Manutenção| #f1c232   | Computador precisa de manutenção preventiva     |
| 215 | Não localizado      | #8e7cc3   | Computador não encontrado no local registrado   |
| 216 | Máquina de Chaves   | #16537e   | Computador usado como máquina de chaves         |
| 220 | Translator          | #b4a7d6   | Computador com software de tradução             |
| 228 | PDV                 | #cc0000   | Ponto de Venda (PDV)                            |

### Etiquetas de Prioridade/Classificação

| ID  | Nome        | Cor  | Comentário                                      |
|-----|-------------|------|-------------------------------------------------|
| 230 | P: Baixa    | —    | Prioridade baixa                                |
| 231 | Problema    | —    | Classificação genérica                          |

---

## Uso Estratégico para Filtragem no GLPI

### Vantagens das Etiquetas sobre Status Padrão

1. **Múltiplas etiquetas simultâneas**: Um ticket pode ter status "Em Andamento" + etiquetas "Aguardando Fornecedor" + "Em Homologação"
2. **Categorização temática**: Agrupe tickets por tipo de demanda (ex: "Erro de Cadastro Simphony", "Cadastro FNRH")
3. **Visibilidade visual**: Cores facilitam identificação rápida na lista de tickets
4. **Filtros avançados**: GLPI permite filtrar por etiqueta na interface web

### Diretrizes de Atribuição

**Ao analisar ticket novo (Passo 2 da skill):**
- Leia a análise e identifique o estado atual
- Atribua etiqueta de fluxo correspondente (Em Análise, Aguardando Fornecedor, etc.)
- Se for tema recorrente, adicione etiqueta temática (Erro de Cadastro Simphony, etc.)

**Ao criar Problema derivado:**
- Atribua etiquetas temáticas aos Problemas (ex: #219 "CMFlex-BI" + etiqueta "Problema")
- Isso permite filtrar todos os Problemas de um cluster específico

**Durante revisão de backlog:**
- Use `py scripts/tag-manager.py list` para auditar etiquetas de tickets críticos
- Remova etiquetas desatualizadas (ex: "Aguardando Fornecedor" quando fornecedor já respondeu)

### Exemplo de Filtragem no GLPI

Na interface web do GLPI:
1. Acesse **Chamados > Chamados**
2. Clique em **Filtros** (ícone de funil)
3. Em **Etiquetas**, selecione uma ou mais etiquetas
4. GLPI mostra apenas tickets com todas as etiquetas selecionadas

**Caso de uso:**
- Filtro: "Aguardando Fornecedor" + "Em Análise"
- Resultado: Todos os tickets que estão sendo investigados mas dependem de fornecedor externo

---

## Limitações e Notas

1. **Sem suporte MCP**: O plugin Tag não expõe ferramentas via MCP. Toda operação é via REST direto.
2. **Sessão expira**: O `Session-Token` expira após inatividade. O script `tag-manager.py` reinicializa automaticamente.
3. **Permissões**: Usuário deve ter permissão de escrita nos itens para atribuir etiquetas.
4. **Entidade**: Etiquetas são globais (entities_id=0, is_recursive=1), aplicáveis a todas as entidades.
5. **ID da associação vs ID da etiqueta**: Sempre use o `id` retornado por `PluginTagTagItem` para operações de remoção.

---

## Integração Futura com RAG

O RAG pode ser expandido para incluir `tags` como metadado de chunk, permitindo:

```bash
# Busca semântica filtrada por etiqueta
wsl python3 scripts/rag-query.py "integração CMFlex" --tag "Aguardando Fornecedor" --top 10

# Análise de cluster por etiqueta
wsl python3 scripts/rag-query.py "" --mode gravity --tag "Em Análise" --top 20
```

**Implementação necessária:**
1. Modificar `rag_lib/parser.py` para extrair etiquetas do ticket MD (se presentes nos metadados)
2. Adicionar campo `tags` aos metadados do chunk em `rag_lib/chunker.py`
3. Atualizar `rag_lib/store.py` para suportar filtro por lista de tags

---

## Referências

- Documentação oficial do plugin: https://github.com/pluginsGLPI/tag
- API REST GLPI: https://github.com/glpi-project/glpi/blob/master/apirest.md
- Script utilitário: `scripts/tag-manager.py`
