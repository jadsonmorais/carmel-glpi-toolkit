# Regras de Atribuição de Entidade GLPI via MCP

## Contexto
Itens criados via ferramentas MCP do GLPI (`glpi_create_ticket`, `glpi_create_problem`, `glpi_create_change`, etc.) são atribuídos à **entidade ativa no GLPI web UI** no momento em que o `GLPI_USER_TOKEN` foi gerado.

## Procedimento para criar itens na Entidade 1 (TI/Carmel)
1. Acesse o GLPI: https://carmelhoteis.verdanadesk.com
2. No canto superior direito, altere para a **Entidade 1 (TI/Carmel)** via perfil > Mudar de entidade
3. Gere um novo `GLPI_USER_TOKEN` em Perfil > Preferências > API
4. Copie o novo token
5. Atualize o arquivo de configuração do Hermes:
   - Windows: `C:/Users/jadson.morais/AppData/Local/hermes/config.yaml`
   - Localize a seção `mcp_servers.glpi.env.GLPI_USER_TOKEN`
   - Substitua pelo novo token
6. Recarregue o MCP no chat: envie `/reload-mcp`

## Validação
Após o procedimento, crie um item de teste e verifique o campo `entities_id` na resposta da API:
- `entities_id: 1` → correto (Entidade TI)
- `entities_id: 0` → incorreto (Entidade raiz, repetir procedimento)

## Nota
Tokens já emitidos permanecem vinculados à entidade original. Sempre gere um novo token após mudar a entidade padrão no GLPI.