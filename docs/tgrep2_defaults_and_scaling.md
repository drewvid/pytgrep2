# TGrep2: Default Constants & Scaling Guide

This document describes the global constants and default behaviors in the `tgrep2` codebase and explains how the system processes large corpora (up to millions of sentences) with low memory overhead.

---

## 1. Global Defines and Constants

These constants are defined at compile time and govern the initial allocation and sizing limits:

| Define / Constant | Default Value | Purpose | Analysis / Sensibility |
| :--- | :--- | :--- | :--- |
| `MAX_FILENAME` | `512` bytes | Buffer size for forming and checking relative file paths with compressors (e.g. `.gz`). | **Low/restrictive for modern systems.** Full absolute paths with deep nesting can exceed 512 bytes. Safe for relative paths. |
| `INIT_HASH` | `500,000` | Size of the hash table used for word deduplication when compiling corpora. | **Sensible.** Keeps bucket collision rates extremely low for typical vocabularies, enabling $O(1)$ lookups. |
| `INIT_BUFFER` | `32,768` bytes | Buffer size for parsing query patterns or input lines during corpus building. | **Sensible.** Easily handles exceptionally long tree-expression strings on a single line. |
| `INIT_TREES` | `20,000` | Initial array size for the tree recycling pool. | **Sensible.** Nodes are reused from this pool dynamically rather than being allocated/freed constantly. Grows dynamically if needed. |
| `INIT_STREES` | `16,000` | Initial pre-allocated array size for sentence node lists. | **Excessive but harmless.** Most sentences have < 200 nodes. However, because only a small window of sentences is kept in memory concurrently, memory waste is negligible. |
| `INIT_KIDS` | `64` | Initial array size for child pointers on *every* tree node. | **Inefficient but bounded.** Allocates 64 child pointers even for terminals (0 children) or standard binary nodes. Harmless in practice due to node recycling. |
| **Max Children** | `255` | Default ceiling for a node's children count to optimize binary corpus storage. | **Sensible Optimization.** Stores counts in 1 byte. Can be extended to `65,535` (stored in 2 bytes) using the `-K` command-line flag. |

---

## 2. Operational Defaults

| Option/Variable | Default Value | Action |
| :--- | :--- | :--- |
| `TMatchMode` | `M_FIRST` | Only reports the first matching subtree found per sentence. Can be changed to all matches via the `-a` option. |
| `PMatchMode` | `M_ALL` | Evaluates matches across all provided patterns. Can be restricted to the first matching pattern via `-f`. |
| `DefFormat` | `F_SHORT` | Outputs trees in single-line, compact parenthesis format (e.g. `(NP (NN cat))`). |
| `ReorderLinks` | `TRUE` | Automatically optimizes queries by executing low-cost/restrictive operations before high-cost ones (e.g. parent-child checks before dominance/precedence). |
| `TotalStored` | `1` | Stores only the current sentence in memory, saving RAM. Automatically increases when printing context sentences (e.g. `%2b` or `%2a`). |

---

## 3. How Scaling and Large Corpora Processing Works

`tgrep2` is designed to scale to millions of trees (sentences) without exhausting system memory. It achieves this through the following engineering choices:

### Streaming Architecture
The matching engine and the compiler read and write files **sequentially, sentence by sentence**. At any point in time, only the current sentence (plus any requested context buffer sentences) is kept in active memory. As a result, memory consumption is flat ($O(1)$) with respect to the number of sentences in the corpus.

### In-Memory Lexicon Footprint
`tgrep2` loads all unique word types and tags into a flat global array (`Words`) upon opening the compiled corpus:
- A large corpus of 1 million sentences typically has between 200,000 and 500,000 unique word types.
- The `Word` structure is extremely lightweight (24 bytes on 64-bit systems).
- Loading a lexicon of 300,000 unique words requires less than **10–20 MB of RAM**, making it extremely light on resources.

### 64-Bit System Compatibility
All sentence indices, word indices, and pattern match counters use 32-bit signed integers (`int`). This allows the code to easily scale up to **2.14 billion** unique words or sentences. 

### Sequential I/O Scanning
Because the program scans the binary corpus file linearly without random seeking:
- It works out of the box with huge file sizes (exceeding 2 GB) on modern operating systems.
- Running search queries on a compiled 200 MB corpus (1 million sentences) only takes seconds on standard SSDs due to high sequential read throughput.

---

## 4. Practical Guidelines for Large Corpora

1. **Use the `-r` option for progress reports**: When searching large corpora, run with `-r <seconds>` (e.g., `-r 5`) to output completion percentage progress updates to `stderr`.
2. **Compile with `-K` for wide trees**: If any node in your trees exceeds 255 children (e.g., flat structures, or long lists parsed as children of one node), always use the `-K` flag when preparing the corpus to avoid a parsing abort:
   ```bash
   tgrep2 -K -p input_corpus.mrg output_corpus.t2c
   ```
