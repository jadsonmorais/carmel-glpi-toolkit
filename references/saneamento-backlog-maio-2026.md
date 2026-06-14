# Saneamento de Backlog Órfão e Clusterização ITIL

## Contexto
Durante a auditoria de maio de 2026, identificamos 122 tickets órfãos (não solucionados e sem vínculo com Problems/Changes). A estratégia de saneamento baseou-se na identificação de "Clusters Horizontais" para agrupar demandas recorrentes.

## Novos Clusters (Problems) Criados

| ID | Nome do Problema | Escopo / Palavras-chave |
|---|---|---|
| #245 | Infraestrutura de Rede e Conectividade | Access Points, Switches, VPN, Cabeamento, Internet |
| #246 | Sistemas de Telefonia e Ramais | Falha de Ramal, Configuração de Central |
| #247 | Módulo de Compras CMFlex | Compras, Orçamentos, Alçadas de aprovação |
| #248 | Integração Integra Front (IFO) | Falhas no robô de sincronização PMS <> ERP |
| #249 | Suporte a Produtividade (Google/Appsheet) | Workspace, Permissões Drive, Apps No-code |
| #250 | Governança de Shadow IT | Soluções setoriais sem apoio da TI (ex: Google AI Studio) |
| #251 | Suporte e Configuração Oracle Simphony POS | PDV, Botões de Venda, Tablets, Micros |

## Lições Aprendidas no Saneamento
1. **Divergência de Contagem:** A API `search/Ticket` pode omitir itens se houver restrição de entidade ou se o status for `Solved`. Use `range=0-500` e verifique a entidade ativa.
2. **Shadow IT como Problem:** Demandas como o ticket #27071 (Google AI Studio) não são apenas "tickets de sistema", mas sinais de falta de governança estrutural.
3. **Clusterização por Palavra-chave:** 86% do backlog órfão foi resolvido mapeando termos nos nomes dos tickets para IDs de problemas específicos.
