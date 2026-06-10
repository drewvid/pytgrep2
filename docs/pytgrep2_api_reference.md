# `TgrepOrchestrator` Developer API Reference

This document provides a detailed API reference for the `TgrepOrchestrator` class inside [tgrep_orchestrator.py](../pytgrep2/tgrep_orchestrator.py).

The `TgrepOrchestrator` class manages the lifecycle of parsed corpora (from raw text lists to Penn Treebank files, compiled binary index files, and structural query execution) by wrapping constituency parsers and compiled `tgrep2` binaries.

---

## Class Signature

```python
class TgrepOrchestrator:
    """
    Orchestrates a linguistic analysis pipeline:
    Raw Text -> .mrg (Penn Treebank format) -> .t2c (Tgrep2 Index) -> Search Results
    """
```

---

## 1. Constructor: `__init__`

Initializes the orchestrator and resolves the path to the executable `tgrep2` binary.

```python
def __init__(self, tgrep2_binary_path: Union[str, Path, None] = None)
```

### Parameters:
* **`tgrep2_binary_path`** *(str | Path | None, optional)*:
  Explicit path to the `tgrep2` binary executable. If `None`, it resolves the binary using the following search order:
  1. `bin/tgrep2-andreasvc` (in script's directory)
  2. `bin/tgrep2-bwaldon` (in script's directory)
  3. `bin/tgrep2-andreasvc` (in current working directory)
  4. `bin/tgrep2-bwaldon` (in current working directory)
  5. System PATH fallback looking for command `tgrep2`.

### Exceptions Raised:
* **`FileNotFoundError`**: If the specified binary path does not exist on disk.
* **`PermissionError`**: If the resolved binary path exists but is not marked as executable (`chmod +x`).

---

## 2. Methods

### `parse_to_mrg`
Segment and parse raw text strings into constituency trees, formatted in Penn Treebank (`.mrg`) syntax.

```python
def parse_to_mrg(
    self, 
    texts: List[str], 
    mrg_path: Union[str, Path], 
    batch_size: int = 64
) -> List[Union[nltk.tree.Tree, str]]
```
* **Parameters**:
  * `texts` *(List[str])*: A list of raw sentence strings to parse.
  * `mrg_path` *(str | Path)*: Destination path for writing the `.mrg` file.
  * `batch_size` *(int, default=64)*: Batch size for `spaCy`'s `nlp.pipe` model parallelism.
* **Returns**:
  * List of `nltk.tree.Tree` objects if `nltk` is installed in the python environment.
  * List of string-based PTB tree representations if `nltk` is not installed.
* **Exceptions Raised**:
  * `ImportError`: If `spacy` or `benepar` is missing from the environment.
  * `OSError`: If the `en_core_web_sm` model is missing in spaCy.
  * `RuntimeError`: If benepar component loading or model download fails.

---

### `index_corpus`
Compile a Penn Treebank (`.mrg`) text file into a binary search index (`.t2c`).

```python
def index_corpus(
    self, 
    mrg_path: Union[str, Path], 
    t2c_path: Union[str, Path, None] = None
) -> Path
```
* **Parameters**:
  * `mrg_path` *(str | Path)*: Path to the source PTB `.mrg` file.
  * `t2c_path` *(str | Path | None, optional)*: Destination path for the `.t2c` binary file. If `None`, it defaults to replacing the `.mrg` extension of the source file with `.t2c`.
* **Returns**:
  * `Path` object representing the compiled `.t2c` file.
* **Exceptions Raised**:
  * `FileNotFoundError`: If the source `.mrg` file does not exist.
  * `RuntimeError`: If compilation command exits with a non-zero exit status.

---

### `search_index`
Query a compiled `.t2c` index with a TGrep2 query pattern and return matching subtrees.

```python
def search_index(
    self, 
    pattern: str, 
    t2c_path: Union[str, Path],
    additional_args: Optional[List[str]] = None
) -> List[str]
```
* **Parameters**:
  * `pattern` *(str)*: The TGrep2 search query string (e.g. `NP < NNP`).
  * `t2c_path` *(str | Path)*: Path to the target `.t2c` index file.
  * `additional_args` *(List[str] | None, optional)*: List of command-line arguments passed to the query command (e.g., `["-a"]` for all matches, or `["-m", "%xh\t%th"]` for formatting).
* **Returns**:
  * List of string search result lines.
* **Exceptions Raised**:
  * `FileNotFoundError`: If the `.t2c` index file is not found.
  * `ValueError`: If any argument in `additional_args` is not a string type.
  * `RuntimeError`: If the query command exits with a non-zero exit status.

---

## 3. Internal Design Features

### Lazy Initialization (`_init_nlp`)
Constituency parsers are loaded dynamically upon the first invocation of `parse_to_mrg()`, caching the spaCy pipeline at `self._nlp`. This minimizes script initialization overhead for commands that only perform search queries.

### Secure Subprocess Execution
To prevent shell injection vulnerabilities, all shell calls (`subprocess.run`) are executed with `shell=False`. Command-line strings are constructed as strict argument arrays, preventing arbitrary shell expansion or command concatenation:

```python
# SECURE (internal implementation):
cmd = [str(self.tgrep2_binary_path), "-c", str(t2c_path)]
if additional_args:
    cmd.extend(additional_args)
cmd.append(pattern)
subprocess.run(cmd, capture_output=True, text=True, check=True)
```
