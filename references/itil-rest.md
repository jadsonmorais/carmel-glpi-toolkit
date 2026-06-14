# ITIL via REST — Endpoints e Campos

## Problem

### Criar
```python
req('POST', 'Problem', body={"input": {
    "name": "...",
    "itilcategories_id": 145,
    "status": 2,               # 1=Novo 2=Em andamento 3=Resolvido 4=Fechado
    "urgency": 3, "impact": 3, "priority": 3,
    "content": "...",
    "symptomcontent": "<p>...</p>",
    "causecontent":   "<p>...</p>",
    "impactcontent":  "<p>...</p>",
}}, st=st)
```

### Atualizar campos de análise (PUT)
```python
req('PUT', 'Problem/{id}', body={"input": {
    "id": pid,
    "symptomcontent": "<p>...</p>",
    "causecontent":   "<p>...</p>",
    "impactcontent":  "<p>...</p>",
    "itilcategories_id": 145,
}}, st=st)
```

### Atribuir técnico
```python
req('POST', 'Problem_User', body={"input": {
    "problems_id": pid,
    "users_id": uid,
    "type": 2,   # 1=Solicitante 2=Atribuído 3=Observador
}}, st=st)
```

### Vincular ticket
```python
req('POST', 'Problem_Ticket', body={"input": {
    "problems_id": pid, "tickets_id": tid,
}}, st=st)
```

---

## Change (Mudança)

```python
# Criar
c = req('POST', 'Change', body={"input": {"name": "...", "itilcategories_id": X, "status": 2, ...}}, st=st)
cid = c['id']

# Vincular ticket / problem / técnico
req('POST', 'Change_Ticket',  body={"input": {"changes_id": cid, "tickets_id": tid}}, st=st)
req('POST', 'Change_Problem', body={"input": {"changes_id": cid, "problems_id": pid}}, st=st)
req('POST', 'Change_User',    body={"input": {"changes_id": cid, "users_id": uid, "type": 2}}, st=st)
```

---

## Categorias ITIL (itilcategories_id) — principais

| ID  | Categoria |
|-----|-----------|
| 120 | Gestão de Acessos |
| 144 | Serviços de Sistemas |
| 145 | Serviços de Sistemas > CMFlex |
| 146 | CMFlex > Almoxarifado |
| 147 | CMFlex > Ativo Fixo (CAF) |
| 148 | CMFlex > BI |
| 149 | CMFlex > BPM |
| 150 | CMFlex > Compras |
| 151 | CMFlex > Contabilidade |
| 152 | CMFlex > Contas a Pagar |
| 153 | CMFlex > Contas a Receber |
| 156 | CMFlex > Fiscal |
| 157 | CMFlex > Global |
| 159 | CMFlex > Orçamento |
| 166 | Serviços de Sistemas > Opera |
| 167 | Opera > Opera Cloud PMS |
| 168 | Opera > R&A (Relatórios) |
| 170 | Serviços de Sistemas > RHID |
| 171 | Serviços de Sistemas > Simphony |
| 172 | Simphony > EMC |
| 173 | Simphony > Micros (Caixas e Tablets) |
| 371 | Simphony > KDS |
| 192 | Microsoft Power BI |
| 208 | Infraestrutura |
| 210 | Infraestrutura > Servidor |
| 209 | Infraestrutura > Switchs |
| 211 | Infraestrutura > Access Points |

Lista completa via: `req('GET', 'ITILCategory?range=0-200', st=st)`

---

## Busca de órfãos (tickets sem Problem)

A API não suporta `lessthan` confiável no campo 12. Consultar cada status separadamente:

```python
for s in [1, 2, 3, 4]:  # Novo, Atribuído, Planejado, Pendente
    r = req('GET',
        f"search/Ticket"
        f"?criteria[0][field]=200&criteria[0][searchtype]=equals&criteria[0][value]=0"
        f"&criteria[1][link]=AND&criteria[1][field]=12&criteria[1][searchtype]=equals&criteria[1][value]={s}"
        f"&forcedisplay[0]=1&forcedisplay[1]=3&forcedisplay[2]=12&forcedisplay[3]=80"
        f"&range=0-200", st=st)
```

Campo 200 = `problems_id`, valor 0 = sem Problem vinculado.

---

## Base de Conhecimento KCS

### Categorias (knowbaseitemcategories_id)
| ID | Prefixo | Tipo |
|----|---------|------|
| 50 | BEC | Bug/Erro Conhecido |
| 51 | IDT | Instrução de Trabalho |
| 52 | SDC | Solução de Contorno |
| 53 | SDV | Solução Definitiva |
| 54 | MAN | Manual / Documentação |
| 55 | DTS | Documentação Técnica de Sistema |

### Nomenclatura
- Formato: `PREFIX-XXXX - Título` (4 dígitos, zero-padded)
- `PREFIX-0000` reservado para template modelo
- Próximos disponíveis (jun/2026): BEC-0018, DTS-0020, IDT-0073, MAN-0117, SDC-0004, SDV-0005

### Criar e categorizar
```python
r = req('POST', 'KnowbaseItem', body={"input": {"name": name, "answer": html_content, "is_faq": 0}}, st=st)
req('POST', 'KnowbaseItem_KnowbaseItemCategory',
    body={"input": {"knowbaseitems_id": r['id'], "knowbaseitemcategories_id": CAT_ID}}, st=st)
```
