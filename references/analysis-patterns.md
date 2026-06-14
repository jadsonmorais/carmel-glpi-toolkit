## Padrões de Clusterização e Governança

### Identificação de Shadow IT
Ao analisar tickets sobre ferramentas no-code (Google AI Studio, Appsheet, Sheets complexos), agrupar sob o conceito de **Shadow IT**.
- **Causa Raiz:** Falta de braço técnico da TI em períodos anteriores.
- **Ação:** Criar Problem dedicado para mapeamento e migração assistida para custódia oficial da TI.

### Clusterização de Backlog Órfão
Ao encontrar massa de tickets (>100) sem vínculo:
1. **Infraestrutura/Rede:** Access Points, Switches, VPN, Internet.
2. **Telefonia:** Ramais e centrais fixas.
3. **Suprimentos:** Compras e Orçamentos (separar de Almoxarifado para manter o foco em fluxos de aprovação).
4. **Dados/BI:** Sustentação de DW Postgres e pipelines ETL (costumam ser o maior cluster por volume de retrabalho).
5. **Integração Front (IFO):** Falhas de sincronização PMS <> CMFlex.

### Fluxo ITIL Avançado
- **Ticket -> Problem -> Change:** Sempre que um ticket revelar uma falha sistêmica configurável (ex: paramentrização de campos obrigatórios no Opera), criar a tríade completa.
- **Status 'Testando':** Use status `6 (Test)` na Change para indicar validação técnica em ambiente TST (ex: Kevin testando bloqueio de FNRH).
- **Video-Trilhas:** Para Problems de suporte recorrente (Simphony, Opera), propor Changes de criação de conteúdo em vídeo para a plataforma **Humand**.
> Extraído de sessão real com 164 chamados abertos. Use como receita para auditorias periódicas.

## Métricas-chave a calcular

| Métrica | Definição | Trigger de ação |
|---------|-----------|-----------------|
| **Parados** | >30 dias sem interação (`tipo` followup/task/abertura) | Revisão semanal com técnico |
| **Antigos** | >90 dias desde primeira interação | Auditoria de validade |
| **Projetos travados** | Texto contém "tornou-se um projeto" ou "projeto" | Mapear dependências e priorizar |
| **Fantasmas** | Apenas 1 interação (só abertura) | Mensagem 48h + fechar se não responder |
| **Desbalanceamento** | Técnico com >30% dos chamados atribuídos | Redistribuição |

## Agrupamentos que revelam padrões

1. **Por localização + categoria** — ex: "Magna Praia > Opera Relatórios" apareceu 8x, indicando demanda agrupável em 1 reunião.
2. **Por requerente (users_id)** — ex: user 55 abriu 8 chamados de relatório. Resolver em bloco.
3. **Por técnico + idle** — técnico com muitos chamados parados = gargalo.

## Scripts de apoio

- `scripts/analyze-backlog.py` — varre todos os `.md` processados, cruza com metadados do endpoint de lista, gera `plano-de-acao.md` e os dois detalhamentos (`parados`, `antigos`).
