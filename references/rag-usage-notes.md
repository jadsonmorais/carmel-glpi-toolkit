# RAG Usage Notes — Workarounds & Environment

## Workaround: `--mode gravity` requires non-empty query

`rag-query.py` validates that `query` is non-empty even when `--mode gravity` (which ignores the query text and sorts by `gravity_score`).

**Fix:** pass a dummy query:
```bash
python3 scripts/rag-query.py "." --mode gravity --top 15
```

## Environment: WSL vs native venv

**Original assumption:** RAG requires WSL because PyTorch lacks wheels for Python 3.14 on Windows.

**Validated reality:** In this session, `chromadb` + `sentence-transformers` installed cleanly via `pip install chromadb sentence-transformers` inside the project's venv (Python 3.13, Debian/WSL). No `wsl` command prefix needed — the venv's `python3` worked directly.

**Recommendation:**
- If running inside a Linux/WSL shell with venv activated: use `python3` directly.  
- If running from Windows `cmd`/`pwsh` outside WSL: use `wsl python3`.
- The `_env.py` auto-detects the environment; scripts work in both.

## Output format: gravity score top-N

Example columns returned:
```
Rank  Ticket   Score_Final  Gravity  Sim   Idle   Flags
1     #16651   0.478        34.5     0.611 171
```

- `Score_Final` = weighted blend (default 50% similarity + 50% gravity)
- `Gravity` = raw gravity_score 0-100
- `Sim` = cosine similarity to query
- `Idle` = days since last interaction
- `Flags` = `[PROJETO]`, `[SEM TECNICO]`

## Common pitfall: first run downloads model

`paraphrase-multilingual-mpnet-base-v2` is downloaded on first `rag-build.py` or `rag-query.py` execution (~1.1 GB). This is automatic but slow. Subsequent runs use cache.
