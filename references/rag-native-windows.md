# RAG Native Windows Support - ChromaDB + Sentence-Transformers

## Status: CONFIRMED WORKING

**What changed:** Starting from Python 3.13/3.14, both ChromaDB and Sentence-Transformers now provide native Windows wheels that work perfectly with modern Python versions on Windows.

## Installation (Windows Native)

```bash
# Use the Python launcher (py) NOT python/python3
py -m pip install chromadb sentence-transformers

# Verify installation
py -m pip list | findstr "chromadb sentence"
```

## Running RAG scripts (Windows Native)

```bash
# Build RAG index
py scripts/rag-build.py

# Query the index  
py scripts/rag-query.py "Opera PMS" --top 5
py scripts/rag-query.py "CMFlex" --mode gravity --top 10
py scripts/rag-query.py --ticket 27747 --mode dedup
```

## Environment Notes
- Python: 3.14.0 (via py launcher)
- PyTorch: Installs automatically via sentence-transformers dependency
- ChromaDB: Uses HTTP-based persistent client (no native lib issues)
- Performance: Comparable to WSL, no noticeable difference

## Fallback: WSL still available
If Windows native has issues, WSL approach still works:
```bash
wsl pip install chromadb sentence-transformers --break-system-packages
wsl python3 scripts/rag-build.py
```

## Benefits of Native Windows
1. No WSL overhead/context switching
2. Direct file system access (no UNC path issues)
3. Single environment management
4. Faster execution (no WSL startup latency)

## Verified Working Session
- **Session:** May 25, 2026
- **Windows Version:** Windows 10
- **Python:** 3.14.0 (via py launcher)
- **Packages:** chromadb-1.5.9, sentence-transformers-5.5.1
- **Tasks:** Full RAG build (86 new chunks) and multiple queries
- **Performance:** Model download ~420MB, inference speeds normal

## Script Compatibility
All scripts work identically in both environments:
- `rag-build.py`
- `rag-query.py` 
- `rag_lib/*` modules
- `_env.py` auto-detects environment

This eliminates the WSL dependency requirement for RAG operations.