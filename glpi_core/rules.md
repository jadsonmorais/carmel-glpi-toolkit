# Regras de Governança — glpi_core

## Nomenclatura de tarefas (ProjectTask)

- Tarefas de fase de projeto (containers): `F<n> - <descrição curta>`, onde `<n>` é o número da fase (1-5).
- Tarefas de execução/leaf (incidente ou item de projeto): `[Sistema/Área] - Ação Principal - Contexto/Local`.
  Use `governance.build_task_name(sistema_area, acao_principal, contexto_local)` para montar o título.
  Ex: `[POS/Simphony] - Instalar Workstation - Restaurante`. Evitar títulos genéricos como "Atualizar sistema".
- O nome não pode iniciar com caractere especial (validado em `TaskCreateSchema`).

## Separação Incidente vs. Projeto (tags)

- Toda tarefa/chamado deve ter uma `GovernanceTag` (ver `schemas/governance.py`):
  - `BREAK_FIX`: suporte reativo, concorre na fila/SLA de incidente crítico.
  - `PLANEJADO` / `PROJETO`: entrega de engenharia/evolução — não deve concorrer na mesma fila/SLA de incidente.
  - `BLOCKED`: impedimento por dependência externa (fornecedor, acesso não liberado) — permite ao gestor filtrar e atuar cirurgicamente.
- Nunca misturar o fluxo de um incidente crítico com o de uma tarefa de projeto só porque estão na mesma ferramenta.

## Marcos de aprovação (Milestones)

- Não assumir que uma tarefa-pai está pronta só porque as tarefas-filhas foram fechadas.
- Usar `ApprovalMilestone` (ver `schemas/governance.py`) como portões explícitos de governança:
  `Homologação Concluída` → `Rollout Realizado` → `Operação Assistida`.
- Isso dá visibilidade executiva sem precisar investigar detalhes técnicos de cada tarefa.

## Definition of Done (DoD)

- Tarefas filhas só podem ser fechadas se os critérios objetivos da fase estiverem cumpridos
  (ver `DOD_BY_PHASE` em `schemas/task.py`) — ex: evidência anexada, IP/MAC registrado, log de teste anexado.
- Velocidade do dia a dia nunca deve abrir mão da qualidade dos dados de governança.

## Templates

- Templates descrevem uma árvore de `ProjectTask` (e, opcionalmente, o `Project` raiz) em JSON, em `glpi_core/templates/*.json`, validados por `ProjectTemplateSchema`/`TaskTemplateNode` (`schemas/template.py`).
- `TaskTemplateNode` espelha 1:1 todos os campos graváveis de `TaskCreateSchema` (ver seção "Campos suportados") — qualquer campo do GLPI pode ser fixado direto no JSON, não só nome/conteúdo.
- Carregar com `TemplateRepository.load("<nome sem .json>")` (`glpi_core/templates/__init__.py`); listar com `TemplateRepository.list_available()`.
- A macro genérica `apply_template_to_project` (`macros/apply_template.py`) aplica qualquer template:
  - Com `project_id`: usa um `Project` já existente no GLPI e só cria a árvore de tarefas dentro dele (ex.: padronizar/expandir um projeto que já existe, como o Projeto #256 real).
  - Sem `project_id` (com `project_overrides`): cria um `Project` novo a partir de `template.project_defaults` + overrides, e then a árvore.
- Para adicionar um template novo: copiar um `.json` existente como base, ajustar `nodes` (cada nó pode ter `children` recursivos, `phase` para herdar o DoD da fase, e `tag` para a tag de governança a aplicar), validar com `TemplateRepository.load(...)` e testar com `--dry-run` antes de rodar contra o GLPI real.
- Exemplos: `fases_padrao.json` (5 fases simples, sem subtarefas) e `simphony_pos_rollout.json` (árvore completa com sub-fases, replicando a estrutura real aplicada no Projeto #256).

## Operações em massa

Para tarefas que já existem no GLPI (criadas por este pacote ou não), use os métodos de `TaskService`/`TagService` — ou as macros finas equivalentes:

- `bulk_rename_tasks` (payload `{task_ids, prefix}`) → `TaskService.bulk_rename`: aplica um prefixo de nomenclatura em massa, idempotente.
- `bulk_apply_dod` (payload `{task_ids, phase}` ou `{project_id, id_range, phase}`) → `TaskService.bulk_apply_dod` / `discover_project_tasks`: injeta o checklist de DoD em tarefas que ainda não têm, idempotente.
- `bulk_tag_tasks` (payload `{items_ids, tag, itemtype}`) → `TagService.bulk_assign_governance_tag`: atribui uma `GovernanceTag` a vários itens de uma vez, resolvendo o id da tag uma única vez.
- **`TaskService.discover_project_tasks(project_id, id_range)`**: quando o projeto não foi criado por este pacote (ex.: Projeto #256 real, montado originalmente via scripts soltos), o sub-recurso `GET Project/{id}/ProjectTask` é não confiável nesta instância GLPI (devolve um subconjunto incompleto sem erro). Esse método varre um range de IDs com `GET ProjectTask/{id}` e filtra por `projects_id` — única forma confiável de descobrir a lista real de tarefas hoje.

## Campos suportados (Create/Template)

Levantados a partir da API real (`GET ProjectTask/{id}`, `GET Project/{id}`):

- **ProjectTask**: `name`, `content`, `comment`, `is_milestone`, `percent_done`, `auto_percent_done`, `plan_start_date`, `plan_end_date`, `real_start_date`, `real_end_date`, `planned_duration`, `projectstates_id`, `projecttasktypes_id`, `projecttasktemplates_id`, `users_id`, `entities_id`, `is_recursive`, `is_template`, `template_name`, além de `projects_id`/`projecttasks_id` (relação pai/projeto).
- **Project**: `name`, `content`, `comment`, `code`, `priority`, `percent_done`, `auto_percent_done`, `plan_start_date`, `plan_end_date`, `real_start_date`, `real_end_date`, `projectstates_id`, `projecttypes_id`, `projecttemplates_id`, `users_id`, `groups_id`, `entities_id`, `is_recursive`, `is_template`, `show_on_global_gantt`, `template_name`.
- Campos somente-leitura (`id`, `date_creation`, `date_mod`, `uuid`, `links`, `date`, `is_deleted`) ficam fora de `*CreateSchema`/`TaskTemplateNode` e só aparecem em `*ReadSchema`.

## Nomenclatura de comandos/macros

- Padrão: `<verbo>_<entidade>_<contexto>`, em snake_case.
- Exemplos: `apply_macro_projeto_256_fases_1_a_5`, `assign_tag_ticket_zabbix`.

## Fluxo para adicionar uma nova macro

1. Definir o schema de entrada em `schemas/` (Pydantic), nunca aceitar dict bruto na camada de macro.
2. Implementar a lógica de negócio em `services/`, não dentro da macro.
3. Criar a macro em `macros/<contexto>.py`, decorada com `@register_macro("<nome>")`.
4. A macro deve apenas orquestrar chamadas a `services/` — sem chamadas HTTP diretas.
5. Importar o novo módulo de macro em `cli.py` para que o `@register_macro` seja executado.
6. Adicionar teste em `tests/test_macros.py` cobrindo o caminho feliz e ao menos uma falha de validação.

## Camadas e responsabilidades

- `connection/client.py`: autenticação e transporte HTTP. Não conhece regras de negócio.
- `services/`: CRUD e regras de negócio (Controllers/Use Cases).
- `schemas/`: contratos de entrada/saída, validados com Pydantic antes de qualquer chamada à API.
- `macros/`: orquestração determinística de comandos compostos.
- `command_handler.py`: dispatcher único — todo comando externo entra por aqui.

## Determinismo

- Nenhuma macro deve depender de IA/LLM para decidir o que fazer — toda decisão é código explícito.
- Mesma entrada (payload) deve sempre produzir a mesma sequência de chamadas à API.
