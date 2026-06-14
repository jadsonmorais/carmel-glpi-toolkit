# Notas de Migração Entre Máquinas — VerdanaDesk Chamados

> Aprendizados da migração 2026-05-21: sync do repo jadsonmorais/hermes para nova máquina Windows.

---

## Erros encontrados e correções

### 1. `_env.py` com path fixo de outra máquina

**Problema:** O `_env.py` usava hardcoded UNC path da máquina anterior:
```python
BASE_DIR = r"\\wsl.localhost\Debian\home\jadson\.hermes\skills\..."
```
Isso quebra completamente em qualquer outra máquina (Windows não encontra o path).

**Fix:** Path relativo via `__file__`:
```python
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", "data"))
```

---

### 2. `analyze-backlog.py` — `NameError: name 'defaultdict' is not defined`

**Problema:** O script importava `Counter` mas não `defaultdict`:
```python
from collections import Counter   # faltava defaultdict
```

**Fix:** Adicionar import:
```python
from collections import Counter, defaultdict
```

---

### 3. MCP GLPI — `npx` quebra no Node.js 24+

**Problema:** Node 24+ vem com `npm` ausente na instalação default. O `npx` não encontra `npx-cli.js`:
```
Error: Cannot find module '...\npm\bin\npx-cli.js'
```

**Fix:**
1. Restaurar npm: `corepack enable`
2. Instalar o pacote globalmente (não via npx): `npm install -g mcp-glpi`
3. No `config.yaml`, usar path absoluto do binário em vez do `npx`:
```yaml
mcp_servers:
  glpi:
    command: "/c/Users/jadson.morais/AppData/Roaming/npm/mcp-glpi"
    args: []
```

**Padrão geral:** `npx -y <pacote>` funciona na maioria dos setups, mas em Node frescos/configurações customizadas o path absoluto do binário é mais robusto.

---

### 4. WSL — `pip` não instalado

**Problema:** Instalação WSL minimal sem `python3-pip`. RAG scripts não funcionam:
```
/bin/bash: line 1: pip: command not found
```

**Fix:** `wsl sudo apt install -y python3-pip`
Depois: `wsl pip3 install chromadb sentence-transformers --break-system-packages`

---

## Checklist de migração para nova máquina

- [ ] Clonar repo `jadsonmorais/hermes`
- [ ] Sync `memories/MEMORY.md` e `memories/USER.md`
- [ ] Sync `skills/` (incluindo `verdanadesk-chamados/`)
- [ ] Sync `SOUL.md` (se customizado)
- [ ] **Verificar `_env.py`:** `BASE_DIR` deve ser path relativo, não UNC fixo
- [ ] Verificar `_env.py` tokens GLPI se ainda válidos
- [ ] Testar `py scripts/analyze-backlog.py`
- [ ] Testar `py scripts/incremental-update.py --help`
- [ ] Instalar `mcp-glpi` globalmente e configurar `config.yaml` com path absoluto
- [ ] Configurar `.env` (TELEGRAM_BOT_TOKEN, TERMINAL_ENV, etc.)
- [ ] Verificar WSL pip: `wsl python3 -m pip --version`
- [ ] Instalar deps RAG no WSL: `chromadb sentence-transformers`
- [ ] Testar RAG: `wsl python3 scripts/rag-build.py --stats`

---

## Estrutura que deve migrar vs. o que é local

**Migrar (repo/sync):**
- `memories/MEMORY.md`, `memories/USER.md`
- `skills/` completo (incluindo dados em `skills/*/data/`)
- `SOUL.md`

**NÃO migrar (máquina-local):**
- `config.yaml` — contém credenciais, provider, MCP servers
- `auth.json` / `.env`
- `state.db`
- `.anthropic_oauth.json`
- `.hermes_history`
