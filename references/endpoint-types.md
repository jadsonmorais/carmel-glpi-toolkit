# Tipos de Endpoint GLPI/VerdanaDesk

## Endpoint de Detalhamento Individual

**URL pattern:** `https://carmelhoteis.verdanadesk.com/plugins/utilsdashboards/front/ajax/graphic.json.php?token={token-unico-por-ticket}`

**Estrutura JSON:**
```json
{
  "name": "(TST) - X",
  "comment": "",
  "data": [
    {
      "id": 18552,
      "Ticket": 15099,
      "date": "2025-06-10 15:35:38",
      "users_id": 188,
      "content": "&#60;p&#62;Boa tarde!&#60;\/p&#62;",
      "tipo": "followup"
    }
  ]
}
```

**Campos-chave que identificam:** `Ticket`, `tipo` (valores: "followup" ou "task"), `users_id`, `content` (HTML-encoded)

**Proposito:** Processar UM chamado completo, gerar arquivo individual com timeline e acompanhamentos.

---

## Endpoint de Listagem/Dashboard

**URL pattern:** `https://carmelhoteis.verdanadesk.com/plugins/utilsdashboards/front/ajax/graphic.json.php?token={token-de-dashboard}`

**Estrutura JSON:**
```json
{
  "name": "(TST) - List Tickets",
  "comment": "",
  "data": [
    {
      "id": 27629,
      "Tipo": "Requisi\u00e7\u00e3o",
      "Entidade": "TI",
      "Localizacao": "Carmel Cumbuco",
      "Data da Ultima Atualizacao": "2026-05-17 10:50:33",
      "Data da Abertura": "2026-05-17 10:50:33",
      "Data do Fechamento": null,
      "Status": "2 - Atribuido",
      "Requerente": "Chrecepcao Carmel Cumbuco",
      "Grupo Requerente": "Recepcao",
      "Tecnico Atribuido": "Eliel Hilquias",
      "Urgencia": 3,
      "Impacto": 3,
      "Prioridade": 1,
      "Categoria": "Solicita\u00e7\u00e3o de Equipamentos de TI > Perif\u00e9ricos > Acess\u00f3rios",
      "Tempo para resolver": "2026-05-21 08:00:00",
      "Tempo para atribuir": "2026-05-18 08:30:00"
    }
  ]
}
```

**Campos-chave que identificam:** `id` (ticket ID), `Status`, `Categoria`, `Localizacao`, `Data da Abertura`, `Urgencia`, `Impacto`, `Prioridade`, `Tecnico Atribuido`

**NÃO contém:** campo `Ticket` (usa `id` no lugar), campo `tipo`, campo `users_id`, campo `content`

**Proposito:** Obter lista de tickets abertos para triagem e priorização. NÃO contém acompanhamentos.

---

## Como detectar programaticamente

```python
import json

def detect_endpoint_type(data):
    if not data.get('data') or len(data['data']) == 0:
        return "empty"
    first = data['data'][0]
    if 'Ticket' in first and 'tipo' in first and 'content' in first:
        return "individual"
    if 'id' in first and 'Status' in first and 'Categoria' in first:
        return "list"
    return "unknown"
```

## Lição aprendida
O mesmo path `graphic.json.php` retorna formatos COMPLETAMENTE diferentes dependendo do token.
NUNCA assumir o formato baseado apenas no path. Sempre inspecionar as chaves do primeiro item de `data[]`.
