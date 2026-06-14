# Receita de Processamento Incremental

## Script canônico

O processamento incremental está implementado em:

```
scripts/incremental-update.py
```

Executar com:
```
py scripts/incremental-update.py
```

O script **não precisa de argumentos** — os endpoints e paths estão hardcoded nele.

## O que ele faz

1. Busca endpoint de lista → metadados de todos os 164 tickets abertos
2. Busca endpoint bulk → todas as 458+ interações
3. Lê `data/index.md` e compara `Data da Ultima Atualizacao` do GLPI com a coluna `Última atualização GLPI` do index
4. Reprocessa apenas tickets onde `glpi_upd > glpi_ts_index` (ou tickets novos/legados sem glpi_ts)
5. Gera/sobrescreve o `.md` individual em `data/`
6. Atualiza `index.md` com novos timestamps

## Por que comparar `glpi_ts` e não `proc_ts`

Comparar com o timestamp de processamento (`proc_ts`) é impreciso: se o processamento ocorreu depois da última atualização do GLPI, o ticket aparece como "desatualizado" mesmo sem mudança real. Usar `glpi_ts` (salvo no momento do processamento) garante que só tickets com interações **novas** são reprocessados.

## Caso de entradas legadas

O index antigo tinha apenas `| ticket | proc_ts | status |` (sem `glpi_ts`). O script detecta essas entradas pela ausência do campo e as marca como `legado`, reprocessando-as para preencher o `glpi_ts` corretamente.

## Formato do index.md (v2)

```
| Ticket | Data de processamento | Última atualização GLPI | Status |
|--------|----------------------|------------------------|--------|
| 15099  | 2026-05-17 20:00     | 2026-05-15 00:12:52    | Processado |
```
