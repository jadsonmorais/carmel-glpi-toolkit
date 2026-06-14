# ITIL no GLPI — Mudanças e Problemas (Carmel Hoteis)

## Objetivo
Usar o GLPI de forma madura conectando o fluxo: Incidente → Problema → Mudança.

## Template de Mudança (RFC) — campos-chave

### 1. Cabeçalho / Identificação
- Título da Mudança (RFC-YYYY-NNN)
- Tipo: Normal / Padrão / Emergencial
- Categoria: Infraestrutura > Rede | Cloud > AWS/Azure | Aplicacao > Opera PMS | BI > ETL | Seguranca | Integracao > APIs
- Solicitante + Responsável Técnico
- Datas: Solicitação / Aprovação CAB / Execução Planejada / Encerramento

### 2. Contexto e Justificativa
- Descrição do problema/necessidade que gerou a mudança
- Sistemas impactados
- Incidentes ou Problemas relacionados (IDs)
- Benefício esperado

### 3. Análise de Risco
- Impacto (1-5) / Urgência (1-5) / Prioridade calculada
- Risco se NÃO implementar
- Janela de manutenção: dia/horário de menor impacto operacional
- Sistemas dependentes que podem ser afetados

### 4. Plano de Execução
- Pré-requisitos / comunicação prévia necessária
- Passos detalhados (numerados, com responsável e tempo estimado)
- Critério de sucesso (o que valida que deu certo)
- Duração estimada + tempo máximo antes de acionar rollback

### 5. Plano de Rollback
- Condição de acionamento (quando reverter)
- Passos de reversão
- Responsável pelo rollback
- Tempo estimado para reverter

### 6. Validação e Encerramento
- Testes pós-implementação
- Aprovação do solicitante
- Documentação atualizada (base de conhecimento)
- Status final: Implementada / Revertida / Parcial

---

## Quando abrir Mudança vs Problema vs Incidente

| Situação | Tipo GLPI |
|----------|-----------|
| Algo parou — impacto imediato | Incidente |
| Padrão recorrente identificado (N incidentes do mesmo tipo) | Problema |
| Ajuste técnico planejado, parametrização, upgrade | Mudança |
| Incidente que exige reconfiguração para não voltar | Incidente + Mudança vinculada |

## Fluxo de triagem ITIL

```
Chamado aberto (Incidente)
    ↓
Resolução imediata (workaround ou solução)
    ↓
Análise de causa raiz → recorrente? → Abrir Problema
    ↓
Causa raiz identificada → exige mudança de configuração/sistema? → Abrir Mudança
    ↓
Mudança aprovada no CAB → Executar → Encerrar Problema + Incidentes vinculados
```

## CAB (Change Advisory Board) adaptado para hotelaria

Dado o contexto dos Carmel Hoteis, sugere-se:

- **CAB Semanal leve:** 30min, quarta-feira, alinha mudanças da semana
- **Participantes fixos:** TI Coord (Jadson) + Gerência de cada unidade afetada
- **Mudanças Padrão:** pré-aprovadas (sem precisar de CAB) — lista a definir
- **Mudanças Emergenciais:** aprovação simplificada, registro obrigatório pós-execução
- **Janela de manutenção padrão:** madrugada (01h-05h) ou segunda-feira manhã (antes de 10h)

## Categorias de mudança sugeridas para Carmel

- Infraestrutura > Rede
- Cloud > AWS
- Cloud > Azure
- Aplicacao > Opera PMS
- Aplicacao > Simphony
- Aplicacao > CMFlex
- Aplicacao > Infraspeak
- BI > ETL
- BI > Indicadores
- Seguranca
- Integracao > APIs
- Integracao > IFC8
