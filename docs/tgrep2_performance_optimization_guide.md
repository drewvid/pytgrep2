# TGrep2 Performance & Pipeline Optimization Guide

When building large-scale linguistic pipelines, NLP parsing and query execution can become bottlenecked by memory overhead and disk I/O. This guide provides optimization strategies for utilizing `TgrepOrchestrator` and the `tgrep2` binaries efficiently on large corpora.

---

## 1. Lazy Loading & Resource Management

Constituency parsing models (like `spaCy`'s pipeline and `benepar`) are heavy and slow to import, often requiring 1.5GB+ of RAM and taking several seconds to load into memory.

### Optimization Strategy:
The `TgrepOrchestrator` implements **lazy loading**. Instantiating `orchestrator = TgrepOrchestrator()` is practically instantaneous and does not load spaCy or benepar. 

If your program only performs searches on an existing `.t2c` index, the parsing models are never loaded, avoiding the performance and memory overhead entirely:

```python
from tgrep_orchestrator import TgrepOrchestrator

# Instantaneous initialization (no NLP model loading)
orchestrator = TgrepOrchestrator()

# Search is extremely fast and has minimal memory footprint
matches = orchestrator.search_index("NP < NNP", "precompiled_corpus.t2c")
```

---

## 2. Batched NLP Parsing

When parsing raw sentences into Penn Treebank formats, parsing sentence-by-sentence in a loop is highly inefficient because it prevents the deep learning libraries from leveraging GPU/CPU batch parallelism.

### Anti-Pattern:
```python
# SLOW: Iterative parsing
for sentence in list_of_sentences:
    orchestrator.parse_to_mrg([sentence], mrg_path) # Invokes pipeline repeatedly
```

### Best Practice:
Pass the entire list of sentences directly to `parse_to_mrg()`. This internally leverages `spaCy`'s optimized `nlp.pipe` streaming pipeline:

```python
# FAST: Batched parsing (leverages CPU/GPU parallelism)
sentences = [...] # List of 100,000 sentences
orchestrator.parse_to_mrg(sentences, mrg_path, batch_size=128)
```
*Note: Adjust `batch_size` based on system memory. `64` or `128` are typically optimal for benepar.*

---

## 3. Caching and Index Reuse

Compiling a `.mrg` file into a binary `.t2c` search index is relatively fast, but still incurs process spawning overhead and disk I/O. In large projects, you should avoid recompiling the index if the source treebank has not changed.

### Best Practice:
Implement an index compilation cache check:

```python
from pathlib import Path

def get_or_create_index(orchestrator, mrg_file: Path, t2c_file: Path) -> Path:
    # Check if index exists and is newer than the source mrg file
    if t2c_file.exists() and t2c_file.stat().st_mtime > mrg_file.stat().st_mtime:
        return t2c_file # Return cached index
    
    # Otherwise compile/recompile
    print(f"Index stale or missing. Compiling {t2c_file}...")
    return orchestrator.index_corpus(mrg_file, t2c_file)
```

---

## 4. Native Disk Compression (`.gz`, `.bz2`)

Large Penn Treebank files (`.mrg`) and binary indices (`.t2c`) can grow to gigabytes for large corpora.

### Optimization Strategy:
TGrep2 has native compression support. If you pass an input or output path with `.gz`, `.bz`, `.bz2`, or `.Z` extensions, the binary automatically compresses/decompresses the data on the fly. 

This significantly reduces disk space without requiring separate extraction steps:

```python
mrg_path = Path("large_corpus.mrg.gz")
t2c_path = Path("large_corpus.t2c.gz")

# 1. Parse and save compressed (.mrg.gz is automatically parsed by gzip if supported,
# or write to uncompressed and compress programmatically)
# 2. Compile index with native compression:
orchestrator.index_corpus(mrg_path, t2c_path) # tgrep2 compiles directly to a gzipped binary!
```
*Note: Decompressing gzip streams is extremely fast on modern CPUs and often improves search speeds on mechanical drives by reducing disk I/O.*

---

## 5. Query Optimization Flags

TGrep2 compiles and optimizes search queries internally (e.g. by reordering links so that rarer node checks are evaluated first).

* **Disabling Link Reordering (`-d` flag)**:
  By default, TGrep2 reorders query links to optimize search throughput. However, if you are running highly structured segmented patterns or disjunctions where you have carefully placed the most likely branches first, you can suppress link reordering with `-d`:
  ```python
  # Suppress link reordering for specific queries
  matches = orchestrator.search_index(
      "NP < NNP", 
      t2c_path, 
      additional_args=["-d"]
  )
  ```
* **Limiting Search Results**:
  If you only need to check for the presence of a structure rather than collecting all matching subtrees, avoid passing `-a` (which returns all matches). Leaving `-a` out allows TGrep2 to stop searching a sentence as soon as the first match is found, improving performance.
