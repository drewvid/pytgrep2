# `pytgrep2` Developer API Reference

This document provides a detailed API reference for all classes and methods in the `pytgrep2` library.

The `pytgrep2` library exposes three main classes:
1. **[`TgrepOrchestrator`](#1-tgreporchestrator)** (defined in [tgrep_orchestrator.py](../pytgrep2/tgrep_orchestrator.py)): Manages the parser and compiler pipeline.
2. **[`TgrepQueryGenerator`](#2-tgrepquerygenerator)** (defined in [query_generator.py](../pytgrep2/query_generator.py)): Translates natural language into structural TGrep2 patterns using Google GenAI (Gemini) and handles local caching.
3. **[`TgrepSemanticAnalyzer`](#3-tgrepsemanticanalyzer)** (defined in [semantic_analyzer.py](../pytgrep2/semantic_analyzer.py)): Coordinates Syntactically-Filtered Semantic Analysis by integrating grammatical filtering and semantic analysis using Google GenAI (Gemini).

---

## 1. `TgrepOrchestrator`

Manages the lifecycle of constituency parsing (using `spaCy` + `benepar`) and structural query execution by wrapping the compiled `tgrep2` executable.

```python
class TgrepOrchestrator:
    """
    Orchestrates a linguistic analysis pipeline:
    Raw Text -> .mrg (Penn Treebank format) -> .t2c (Tgrep2 Index) -> Search Results
    """
```

### Constructor

```python
def __init__(self, tgrep2_binary_path: Union[str, Path] = None)
```

* **Parameters**:
  * `tgrep2_binary_path` *(str | Path, optional)*: Explicit path to the `tgrep2` executable binary. If `None` (default), resolves the binary automatically by checking:
    1. A local binary path at `~/.local/bin/tgrep2`
    2. A bundled binary at `pytgrep2/bin/tgrep2-andreasvc` or `pytgrep2/bin/tgrep2-bwaldon`
    3. Paths relative to the current working directory (`bin/tgrep2-andreasvc` or `bin/tgrep2-bwaldon`)
    4. The system `PATH` as a fallback command `tgrep2`.
* **Exceptions Raised**:
  * `FileNotFoundError`: If the specified binary path does not exist on disk.
  * `PermissionError`: If the resolved binary path exists but is not marked as executable (`chmod +x`).

---

### Public Methods

#### `parse_to_mrg`
Segment and parse raw text strings into constituency trees, formatted in Penn Treebank (`.mrg`) syntax.

```python
def parse_to_mrg(
    self, 
    texts: List[str], 
    mrg_path: Union[str, Path], 
    batch_size: int = 64
) -> List[object]
```
* **Parameters**:
  * `texts` *(List[str])*: A list of raw sentence/paragraph strings to parse.
  * `mrg_path` *(str | Path)*: Destination path for writing the `.mrg` file.
  * `batch_size` *(int, default=64)*: Batch size for `spaCy`'s `nlp.pipe` processing to optimize pipeline throughput.
* **Returns**:
  * `List[nltk.tree.Tree]` if `nltk` is installed in the python environment.
  * `List[str]` containing string PTB tree representations if `nltk` is not installed.
* **Exceptions Raised**:
  * `ImportError`: If `spacy` or `benepar` is missing from the environment.
  * `OSError`: If the `en_core_web_sm` model is missing in spaCy.
  * `RuntimeError`: If benepar component loading or model download fails.

> [!TIP]
> The `spaCy` model loading and `benepar` pipe initialization are deferred (lazy loaded) until the first time `parse_to_mrg` is executed, keeping the import/load footprint minimal for searching existing indices.

---

#### `index_corpus`
Compile a Penn Treebank (`.mrg`) text file into a binary search index (`.t2c`).

```python
def index_corpus(
    self, 
    mrg_path: Union[str, Path], 
    t2c_path: Union[str, Path] = None
) -> Path
```
* **Parameters**:
  * `mrg_path` *(str | Path)*: Path to the source PTB `.mrg` file.
  * `t2c_path` *(str | Path | None, optional)*: Destination path for the `.t2c` binary file. If `None`, defaults to changing the `.mrg` suffix to `.t2c`.
* **Returns**:
  * `Path` object representing the compiled `.t2c` file.
* **Exceptions Raised**:
  * `FileNotFoundError`: If the source `.mrg` file does not exist.
  * `RuntimeError`: If compilation command exits with a non-zero status.

---

#### `search_index`
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

#### `search_word`
Search the index for occurrences of a single word, optionally filtered by part-of-speech (POS).

```python
def search_word(
    self,
    word: str,
    t2c_path: Union[str, Path],
    pos: Optional[str] = None,
    case_insensitive: bool = True,
    return_type: Optional[str] = None,
    additional_args: Optional[List[str]] = None
) -> Union[List[dict], List[str]]
```
* **Parameters**:
  * `word` *(str)*: The word or regular expression pattern (e.g., `'/^[Jj]ohn$/'`) to search for.
  * `t2c_path` *(str | Path)*: Path to the target `.t2c` index file.
  * `pos` *(str | None, optional)*: POS tag to filter results by (e.g., `'VBZ'`, `'NNP'`).
  * `case_insensitive` *(bool, default=True)*: Performs case-insensitive matching.
  * `return_type` *(str | None, optional)*: If `None` (default), returns a list of dictionaries with structural matches. Choose from `'subtree'`, `'tree'`, or `'sentence'` to retrieve pre-formatted string lines directly.
  * `additional_args` *(List[str] | None, optional)*: Additional arguments passed directly to `tgrep2`.
* **Returns**:
  * List of matching results (dictionaries or formatted strings). If `return_type` is `None`, each dictionary has keys:
    * `sentence_index`: 0-based sentence index.
    * `subtree`: The matching subtree string.
    * `tree`: The full parse tree.
    * `sentence`: The raw sentence text.
* **Exceptions Raised**:
  * `ValueError`: If an invalid `return_type` is provided.

---

#### `search_collocation`
Search for syntactic collocations of two words with specific structural relations.

```python
def search_collocation(
    self,
    word1: str,
    word2: str,
    t2c_path: Union[str, Path],
    relation: str = "immediate",
    distance: Optional[int] = None,
    pos1: Optional[str] = None,
    pos2: Optional[str] = None,
    case_insensitive: bool = True,
    return_type: Optional[str] = None,
    additional_args: Optional[List[str]] = None
) -> Union[List[dict], List[str]]
```
* **Parameters**:
  * `word1` *(str)*: The first target word.
  * `word2` *(str)*: The second target word.
  * `t2c_path` *(str | Path)*: Path to the `.t2c` index.
  * `relation` *(str, default="immediate")*: The relation type. Choose from:
    * `"immediate"`: `word1` immediately precedes `word2` (`.`).
    * `"precedes"`: `word1` precedes `word2` at any distance (or limited distance if `distance` is specified).
    * `"sister"`: `word1` is a sister of and precedes `word2` (`$..`).
    * `"sister_immediate"`: `word1` is a sister of and immediately precedes `word2` (`$.`).
  * `distance` *(int | None, optional)*: Limits the maximum words between `word1` and `word2` when `relation` is `"precedes"`. Must be $\ge 1$.
  * `pos1`, `pos2` *(str | None, optional)*: Optional POS tag filters for the respective words.
  * `case_insensitive` *(bool, default=True)*: Performs case-insensitive matching.
  * `return_type` *(str | None, optional)*: Same behavior as in `search_word`.
  * `additional_args` *(List[str] | None, optional)*: Extra arguments for `tgrep2`.
* **Returns**:
  * List of matching results (dictionaries or formatted strings).
* **Exceptions Raised**:
  * `ValueError`: If an invalid `return_type` or `relation` is specified, or if `distance` is less than 1.

---

#### `search_pos`
Search for words matching a specific part-of-speech (POS) tag.

```python
def search_pos(
    self,
    pos_tag: str,
    t2c_path: Union[str, Path],
    word: Optional[str] = None,
    case_insensitive: bool = True,
    return_type: Optional[str] = None,
    additional_args: Optional[List[str]] = None
) -> Union[List[dict], List[str]]
```
* **Parameters**:
  * `pos_tag` *(str)*: POS tag or shorthand alias. The standard aliases supported are:
    * `NOUN` $\rightarrow$ `/^NN/`
    * `VERB` $\rightarrow$ `/^VB/`
    * `ADJ` $\rightarrow$ `/^JJ/`
    * `ADV` $\rightarrow$ `/^RB/`
    * `PRON` $\rightarrow$ `/^PRP/`
    * `DET` $\rightarrow$ `/^DT/`
  * `t2c_path` *(str | Path)*: Path to the target `.t2c` index file.
  * `word` *(str | None, optional)*: Specific word to constrain the POS search.
  * `case_insensitive` *(bool, default=True)*: Performs case-insensitive matching.
  * `return_type` *(str | None, optional)*: Same behavior as in `search_word`.
  * `additional_args` *(List[str] | None, optional)*: Extra arguments for `tgrep2`.
* **Returns**:
  * List of matching results (dictionaries or formatted strings).

---

#### `search_phrase`
Search for syntactic phrases containing specified child elements.

```python
def search_phrase(
    self,
    phrase_tag: str,
    t2c_path: Union[str, Path],
    contains: Optional[List[str]] = None,
    immediate: bool = True,
    case_insensitive: bool = True,
    return_type: Optional[str] = None,
    additional_args: Optional[List[str]] = None
) -> Union[List[dict], List[str]]
```
* **Parameters**:
  * `phrase_tag` *(str)*: Phrase category to query (e.g. `'NP'`, `'VP'`, `'PP'`, `'S'`).
  * `t2c_path` *(str | Path)*: Path to the target `.t2c` index file.
  * `contains` *(List[str] | None, optional)*: List of node labels or words that the phrase must contain.
  * `immediate` *(bool, default=True)*: If `True`, target elements must be immediate children (`<`). If `False`, they can be descendants at any depth (`<<`).
  * `case_insensitive` *(bool, default=True)*: Performs case-insensitive matching.
  * `return_type` *(str | None, optional)*: Same behavior as in `search_word`.
  * `additional_args` *(List[str] | None, optional)*: Extra arguments for `tgrep2`.
* **Returns**:
  * List of matching results (dictionaries or formatted strings).

---

### Internal Helper Methods

* `_init_nlp(self) -> None`: Performs lazy loading of `spacy` and `benepar` libraries and setups the pipeline.
* `_escape_word_or_regex(self, word: str) -> str`: Formats a word query by escaping special characters unless the word is already formatted as a standard regex (e.g., starting/ending with `/`).
* `_build_word_pattern(self, word: str, pos: Optional[str] = None) -> str`: Helper method to generate the appropriate TGrep2 query pattern for a single word and POS tag constraint.

---

## 2. `TgrepQueryGenerator`

Translates natural language descriptions into valid structural TGrep2 patterns using Google GenAI (Gemini) and caches successful queries locally in a compressed pickle file.

```python
class TgrepQueryGenerator:
    """
    Translates natural language descriptions into valid TGrep2 query patterns.
    Uses Google GenAI Gemini and caches successful queries locally in a
    compressed pickle file.
    """
```

### Constructor

```python
def __init__(
    self,
    cache_path: Union[str, Path] = "tgrep_query_cache.pkl.gz",
    api_key: Optional[str] = None,
    model: str = "gemini-3.1-flash-lite",
    orchestrator: Optional[TgrepOrchestrator] = None
)
```

* **Parameters**:
  * `cache_path` *(str | Path, default="tgrep_query_cache.pkl.gz")*: File path to load and save compressed query caches.
  * `api_key` *(str | None, optional)*: Google GenAI API key. If `None`, resolved by the Google GenAI SDK.
  * `model` *(str, default="gemini-3.1-flash-lite")*: Google GenAI Gemini model name to query.
  * `orchestrator` *(TgrepOrchestrator | None, optional)*: Custom orchestrator used to validate syntax correctness of generated patterns. If `None`, a new instance is created.

---

### Public Methods

#### `validate_pattern`
Validates TGrep2 query pattern syntax.

```python
def validate_pattern(self, pattern: str) -> bool
```
* **Parameters**:
  * `pattern` *(str)*: The pattern string to validate.
* **Returns**:
  * `True` if the pattern syntax is valid, `False` otherwise.
* **Implementation Note**: Validates the pattern by parsing a simple mock sentence into a temporary directory index and querying it. Temporary files are guaranteed to be cleaned up afterward.

---

#### `generate_pattern`
Translates a natural language description into a valid TGrep2 query pattern.

```python
def generate_pattern(self, description: str, max_retries: int = 3) -> str
```
* **Parameters**:
  * `description` *(str)*: Natural language explanation of the desired syntactic structure.
  * `max_retries` *(int, default=3)*: Maximum number of retry attempts using self-correction feedback if LLM-generated patterns fail syntactical validation.
* **Returns**:
  * Valid TGrep2 pattern string.
* **Exceptions Raised**:
  * `ValueError`: If the input description is empty.
  * `RuntimeError`: If a valid pattern could not be generated within the maximum retry limit.

---

### Internal Helper Methods

* `_load_cache(self) -> None`: Loads cached query mappings from `cache_path` if the file exists.
* `_save_cache(self) -> None`: Saves current query mappings dictionary as a compressed gzip pickle to `cache_path`.
* `_get_pattern_error(self, pattern: str) -> str`: Captures and returns the exact error string raised by the `tgrep2` executable on execution of the given pattern.

---

## 3. `TgrepSemanticAnalyzer`

Coordinates Syntactically-Filtered Semantic Analysis. Prunes/filters a text corpus using structural TGrep2 matching, then executes targeted semantic analyses on those matches using Google GenAI (Gemini).

```python
class TgrepSemanticAnalyzer:
    """
    Coordinates Syntactically-Filtered Semantic Analysis.
    Prunes/filters a text corpus or index using pytgrep2, then runs semantic analysis
    on the matched sentences using Google GenAI (Gemini).
    """
```

### Constructor

```python
def __init__(
    self,
    api_key: Optional[str] = None,
    model: str = "gemini-3.1-flash-lite",
    orchestrator: Optional[TgrepOrchestrator] = None,
    query_generator: Optional[TgrepQueryGenerator] = None,
)
```

* **Parameters**:
  * `api_key` *(str | None, optional)*: Google GenAI API key. If `None`, falls back to environment variables `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
  * `model` *(str, default="gemini-3.1-flash-lite")*: Google GenAI Gemini model name to query.
  * `orchestrator` *(TgrepOrchestrator | None, optional)*: Custom orchestrator instance.
  * `query_generator` *(TgrepQueryGenerator | None, optional)*: Custom query generator instance.

---

### Public Methods

#### `analyze_corpus`
Runs the Syntactically-Filtered Semantic Analysis workflow.

```python
def analyze_corpus(
    self,
    corpus: Union[List[str], Path, str],
    pattern_or_desc: str,
    semantic_task: str,
    metadata: Optional[Union[List[Any], Dict[Any, Any]]] = None,
    is_pattern: bool = True,
    max_results: Optional[int] = None,
    case_insensitive: bool = True,
    response_schema: Optional[Any] = None,
    response_mime_type: Optional[str] = None,
    custom_prompt_formatter: Optional[Callable[[str, List[str], Any, str], str]] = None,
) -> List[Dict[str, Any]]
```
* **Parameters**:
  * `corpus` *(List[str] | Path | str)*: A list of raw texts, a path to a Penn Treebank `.mrg` file, or a path to a compiled `.t2c` / `.t2c.gz` index.
  * `pattern_or_desc` *(str)*: A direct TGrep2 pattern string or a natural language description (translated via `TgrepQueryGenerator`).
  * `semantic_task` *(str)*: The instruction prompt sent to Gemini (e.g. *"Analyze the tone..."*).
  * `metadata` *(List[Any] | Dict[Any, Any] | None, optional)*: Optional metadata aligned with the corpus by 0-based sentence index.
  * `is_pattern` *(bool, default=True)*: If `True`, treats `pattern_or_desc` as a direct TGrep2 pattern. If `False`, translates it using `TgrepQueryGenerator` first.
  * `max_results` *(int | None, optional)*: Maximum number of matched sentences to process with Gemini.
  * `case_insensitive` *(bool, default=True)*: Performs case-insensitive matching.
  * `response_schema` *(Any | None, optional)*: Optional schema structure for structured Gemini outputs.
  * `response_mime_type` *(str | None, optional)*: Optional mime type (e.g. `'application/json'`) for structured outputs.
  * `custom_prompt_formatter` *(Callable | None, optional)*: Custom prompt formatting function. Signature should match `(sentence: str, subtrees: List[str], metadata: Any, task: str) -> str`.
* **Returns**:
  * A list of dictionaries representing the analysis results. Each dictionary contains:
    * `sentence_index`: 0-based sentence index.
    * `sentence`: The raw sentence text.
    * `subtrees`: List of matched PTB subtrees.
    * `tree`: The full parse tree.
    * `metadata`: Corresponding metadata (if provided).
    * `analysis`: Text or structured JSON response from Gemini.
    * `pattern`: The final TGrep2 pattern used.
* **Exceptions Raised**:
  * `FileNotFoundError`: If the corpus path is provided but does not exist.

---

### Internal Helper Methods

* `_construct_prompt(self, sentence: str, subtrees: List[str], task: str, metadata: Optional[Any] = None, custom_prompt_formatter: Optional[Callable[[str, List[str], Any, str], str]] = None) -> str`: Builds the prompt sent to Gemini.
* `_call_gemini(self, prompt: str, response_schema: Optional[Any] = None, response_mime_type: Optional[str] = None) -> str`: Calls the Google GenAI SDK to generate content under `self.model` using the provided prompt and configurations.

---

## 4. Secure Subprocess Execution

To prevent command injection vulnerabilities, all subprocess invocations in `pytgrep2` execute with `shell=False`. Arguments are strictly array-serialized before invoking the underlying `tgrep2` executable.

```python
# Secure Internal Pattern Example
cmd = [str(self.tgrep2_binary_path), "-c", str(t2c_path)]
if additional_args:
    cmd.extend(additional_args)
cmd.append(pattern)
subprocess.run(cmd, capture_output=True, text=True, check=True)
```
