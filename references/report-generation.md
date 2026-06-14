# Geração de Relatórios Executivos

> Sessão: 2026-05-17 | Usuário corrigiu relatório gravity com 15/15 tickets hardcoded errados.

## Regra absoluta

**NUNCA hardcodar metadados de ticket em relatórios gerados.**
Sempre ler dos arquivos `.md` reais via parser ou regex antes de gerar qualquer tabela, ranking ou ficha comparativa.

## Erro real ocorrido

Relatório `relatorio-gravity-executivo.md` foi gerado com dicionário Python hardcoded para os top 15 tickets. Resultado:
- #27620 aparecia como "Opera R&A Magna Praia" quando na verdade é "Impressora > Falha, Carmel Taiba"
- 15 discrepâncias totais: status, local, técnico e categoria todos errados
- Usuário rejeitou o relatório e exigiu regeneração com dados reais

## Formato aprovado pelo usuário

O usuário aprovou e prefere relatórios estruturados neste formato:

```
## 1. Sumário Executivo
- Principais achados em bullets

## 2. Top N por <critério>
- Tabela com: Rank, Ticket, Score, Idle, Status, Local, Técnico, Categoria, Flags

## 3. Ficha Individual dos Top N
### #XXXX — Título real
**Rank:** X | **Score:** Y | **Idle:** Zd | **Status:** S
**Local:** L | **Técnico:** T | **Categoria:** C

#### Resumo Executivo
<conteúdo real do .md>

#### Contexto do Negócio
<conteúdo real do .md>

#### Decisões Técnicas
<conteúdo real do .md>

#### Bloqueios & Dependências
<conteúdo real do .md>

#### Próximos Passos
<conteúdo real do .md>

---

## 4. Clusters Identificados
- Tabela com tickets similares
- Diagnóstico do cluster

## 5. Recomendações Imediatas
- Ações concretas com responsáveis e prazos
```

## Parser de metadados (Python)

Use este padrão para extrair metadados reais de qualquer `TICKET_ID.md`:

```python
import re

def parse_ticket_md(path):
    content = open(path, encoding="utf-8").read()
    data = {"titulo": "", "status": "", "localizacao": "",
            "tecnico": "Não atribuído", "categoria": ""}
    m = re.search(r'^# Chamado #(\d+)\s*—\s*(.+)$', content, re.MULTILINE)
    if m:
        data["titulo"] = m.group(2).strip()
    for line in content.splitlines():
        if line.startswith("- **Status:**"):
            data["status"] = line.split(":**")[-1].strip()
        elif line.startswith("- **Localização:**"):
            data["localizacao"] = line.split(":**")[-1].strip()
        elif line.startswith("- **Técnico Responsável:**"):
            data["tecnico"] = line.split(":**")[-1].strip()
        elif line.startswith("- **Técnico Atribuído:**"):
            data["tecnico"] = line.split(":**")[-1].strip()
        elif line.startswith("- **Categoria:**"):
            data["categoria"] = line.split(":**")[-1].strip()
    return data
```

## Verificação obrigatória

Antes de entregar qualquer relatório comparativo:
1. Confirmar que os metadados vieram dos `.md` reais, não de memória ou hardcode
2. Verificar se pelo menos 1 ticket tem categoria/local inesperado (sanity check)
3. Se o usuário questionar factualidade, regenerar inteiramente a partir dos fontes
