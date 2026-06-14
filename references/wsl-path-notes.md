# WSL Path Translation Notes for Windows Git-Bash

## Problem
When running RAG scripts via `wsl python3` from the Windows git-bash terminal, the path to scripts may get mangled with extra prefixes (e.g., `/mnt/c/Users/...` gets prepended with Git install paths).

## Reproduction
```bash
# Fails with "No such file or directory"
wsl python3 "/mnt/c/Users/jadson.morais/AppData/Local/hermes/skills/productivity/verdanadesk-chamados/scripts/rag-query.py"
```

## Workaround
1. First verify the path exists in WSL:
   ```bash
   wsl ls -la "/mnt/c/Users/jadson.morais/AppData/Local/hermes/skills/productivity/verdanadesk-chamados/scripts/rag-query.py"
   ```
2. If valid, run using the WSL path directly without extra quoting/escaping:
   ```bash
   wsl python3 /mnt/c/Users/jadson.morais/AppData/Local/hermes/skills/productivity/verdanadesk-chamados/scripts/rag-query.py "query" --mode gravity
   ```
3. Alternatively, use `execute_code` with Python's `subprocess` to call WSL, which avoids git-bash path interpolation.

## Related Files
- `scripts/rag-query.py`
- `scripts/rag-build.py`
- `_env.py` (path detection logic)
