# MCP GLPI — Integração com a Skill VerdanaDesk

## Configuração (já feita em `~/.hermes/config.yaml`)

```yaml
mcp_servers:
  glpi:
    command: "npx"
    args: ["-y", "mcp-glpi"]
    env:
      GLPI_URL: "https://carmelhoteis.verdanadesk.com"   # SEM /apirest.php — o cliente concatena internamente
      GLPI_APP_TOKEN: "..."
      GLPI_USER_TOKEN: "..."
    tools:
      exclude: [delete_ticket, delete_computer, delete_software, delete_problem, delete_change]
      prompts: false
      resources: false
```

Após qualquer mudança no config: `/reload-mcp`

---

## Ferramentas disponíveis — 69 tools (prefixo `mcp_glpi_` no Hermes)

### Tickets (uso mais frequente)

| Ferramenta | Parâmetros principais | Quando usar |
|------------|-----------------------|-------------|
| `glpi_list_tickets` | `limit`, `status` (1-6), `order` | Listar chamados com filtros |
| `glpi_get_ticket` | `id` | Ver chamado completo (followups + tasks) |
| `glpi_create_ticket` | `name`, `content`, `urgency`, `type`, `category_id`, `user_id_assign` | Abrir novo chamado |
| `glpi_update_ticket` | `id`, `name`, `content`, `status`, `urgency` | Atualizar chamado |
| `glpi_add_followup` | `ticket_id`, `content`, `is_private` | Registrar comentário/decisão |
| `glpi_add_task` | `ticket_id`, `content`, `state`, `users_id_tech`, `actiontime` | Adicionar tarefa |
| `glpi_add_solution` | `ticket_id`, `content`, `solutiontypes_id` | Fechar com solução |
| `glpi_assign_ticket` | `ticket_id`, `user_id`, `type` (1=req, 2=assigned, 3=obs) | Atribuir técnico/grupo |
| `glpi_get_ticket_followups` | `ticket_id` | Buscar só followups |
| `glpi_get_ticket_tasks` | `ticket_id` | Buscar só tasks |
| `glpi_get_ticket_stats` | — | Estatísticas de chamados |

**Status codes:** 1=Novo, 2=Em processamento (atribuído), 3=Em processamento (planejado), 4=Pendente, 5=Resolvido, 6=Fechado

### ITIL — Problemas e Mudanças

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_problems` | Listar problemas abertos |
| `glpi_get_problem` | Detalhe de um problema |
| `glpi_create_problem` | Criar problema ITIL |
| `glpi_update_problem` | Atualizar problema |
| `glpi_list_changes` | Listar mudanças |
| `glpi_get_change` | Detalhe de uma mudança |
| `glpi_create_change` | Criar requisição de mudança |
| `glpi_update_change` | Atualizar mudança |

### Ativos (Inventário)

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_computers` | Listar computadores |
| `glpi_get_computer` | Detalhe de um computador |
| `glpi_create_computer` | Cadastrar computador |
| `glpi_update_computer` | Atualizar computador |
| `glpi_list_softwares` | Listar softwares |
| `glpi_get_software` | Detalhe de software |
| `glpi_create_software` | Cadastrar software |
| `glpi_list_network_equipments` | Listar equipamentos de rede |
| `glpi_get_network_equipment` | Detalhe de equipamento de rede |
| `glpi_list_printers` | Listar impressoras |
| `glpi_get_printer` | Detalhe de impressora |
| `glpi_list_monitors` | Listar monitores |
| `glpi_get_monitor` | Detalhe de monitor |
| `glpi_list_phones` | Listar telefones |
| `glpi_get_phone` | Detalhe de telefone |
| `glpi_get_asset_stats` | Estatísticas de ativos |

### Base de Conhecimento

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_knowbase` | Listar artigos |
| `glpi_get_knowbase_item` | Ler artigo |
| `glpi_search_knowbase` | Buscar por texto |
| `glpi_create_knowbase_item` | Criar artigo |

### Usuários e Grupos

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_users` | Listar usuários |
| `glpi_get_user` | Detalhe de usuário |
| `glpi_search_user` | Buscar usuário por nome/email |
| `glpi_create_user` | Criar usuário |
| `glpi_list_groups` | Listar grupos |
| `glpi_get_group` | Detalhe de grupo |
| `glpi_create_group` | Criar grupo |
| `glpi_add_user_to_group` | Adicionar usuário a grupo |

### Entidades, Localizações, Categorias

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_entities` | Listar entidades (unidades) |
| `glpi_get_entity` | Detalhe de entidade |
| `glpi_list_locations` | Listar localizações |
| `glpi_get_location` | Detalhe de localização |
| `glpi_create_location` | Criar localização |
| `glpi_list_categories` | Listar categorias de chamado |

### Contratos e Fornecedores

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_contracts` | Listar contratos |
| `glpi_get_contract` | Detalhe de contrato |
| `glpi_create_contract` | Criar contrato |
| `glpi_list_suppliers` | Listar fornecedores |
| `glpi_get_supplier` | Detalhe de fornecedor |
| `glpi_create_supplier` | Criar fornecedor |

### Projetos

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_projects` | Listar projetos |
| `glpi_get_project` | Detalhe de projeto |
| `glpi_create_project` | Criar projeto |
| `glpi_update_project` | Atualizar projeto |

### Documentos e Utilitários

| Ferramenta | Uso |
|------------|-----|
| `glpi_list_documents` | Listar documentos |
| `glpi_get_document` | Baixar/ver documento |
| `glpi_search` | Busca genérica em qualquer itemtype |
| `glpi_get_session_info` | Info da sessão API ativa |

---

## Divisão de responsabilidades

| Operação | Usar |
|----------|------|
| Processar/atualizar todos os chamados em batch | `py scripts/incremental-update.py` |
| Busca semântica / gravidade / duplicatas | `wsl python3 scripts/rag-query.py` |
| Ver status de um chamado específico | `glpi_get_ticket` |
| Agir sobre um chamado (comentar, atribuir, fechar) | ferramentas `glpi_*` via MCP |
| Queries ad-hoc (sem técnico, por categoria, etc.) | `glpi_list_tickets` + `glpi_search` |
| Inventário de ativos | `glpi_list_computers`, `glpi_list_network_equipments`, etc. |

---

## Credenciais

- `GLPI_APP_TOKEN` — token de aplicação (Setup > General > API no VerdanaDesk)
- `GLPI_USER_TOKEN` — token do usuário (Preferências > Remote access keys)
- **Diferente** dos tokens de plugin (`graphic.json.php`) usados no `_env.py`

Se o MCP retornar 401/403: renovar `GLPI_USER_TOKEN` nas preferências do GLPI.

## Pitfall importante — URL sem /apirest.php

O cliente `mcp-glpi` concatena `/apirest.php` internamente em todas as chamadas.
O `GLPI_URL` deve apontar para a raiz do servidor, **sem** o sufixo:

```
CORRETO:   https://carmelhoteis.verdanadesk.com
ERRADO:    https://carmelhoteis.verdanadesk.com/apirest.php   ← duplica o path → 400
```
