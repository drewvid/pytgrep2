# TGrep2 Output Formatting & Subtree Extraction Tutorial

This tutorial describes how to control the formatting of search results and extract subtrees using TGrep2, and how to utilize these features within the Python wrapper (`TgrepOrchestrator`).

By default, when a pattern matches, TGrep2 prints the matching subtree on a single line in short parenthesized format. However, TGrep2 offers a rich string-formatting language to output specific node labels, sentence positions, metadata, or formatted subtree text.

---

## 1. Quick Formatting Flags (No `-m` specified)

If you do not specify a custom `-m` format, you can use these flags to quickly change the tree printing style:

| Flag | Description | Output Example |
| :--- | :--- | :--- |
| *(None)* | **Short Form**: Compact single-line parenthesized tree. | `(NP (NNP John))` |
| `-l` | **Long Form**: Multi-line, indented tree with one node per line. | *(Indented PTB Tree)* |
| `-t` | **Terminals Only**: Prints only the words (leaves), stripping syntax. | `John` |
| `-u` | **Top Node Name**: Prints only the label of the matched subtree root. | `NP` |
| `-x` | **Subtree Code**: Prints the location of the node as `s:n` (sentence:node). | `1:2` |
| `-w` | **Whole Tree**: Prints the entire sentence tree, rather than the matching subtree. | `(S (NP (NNP John)) ...)` |

### Python Example:
```python
# Print only the leaf words (terminals) for the matching subtrees
matches = orchestrator.search_index("NP < NNP", t2c_path, additional_args=["-t"])
for word in matches:
    print(word)  # Output: "John", "Mary"
```

---

## 2. Advanced Formatted Output (`-m <format>`)

The `-m` option allows you to define a custom format string, similar to Python's format strings or C's `printf`. 

A formatting string can contain regular text, escape sequences (like `\n` or `\t`), and placeholders starting with `%`.

### Non-Tree Placeholders
* `%f`: The filename of the `.t2c` corpus.
* `%s`: The sentence number (starting from 1).
* `%p`: The index number of the matching pattern (starting from 1).
* `%i`: The match index on the current sentence (starts at 1).
* `%j`: The match index on the current sentence for *this* pattern (resets per pattern).
* `%c`: The sentence comment (if comments were loaded via the `-C` flag when indexing).

### Tree Placeholders
* `%h`: The head node (first node) of the matched pattern.
* `%m`: The nodes marked for printing (using the single back-quote `` ` `` prefix in the pattern). If no nodes are marked, it defaults to the head node `%h`.
* `%w`: The top root node of the entire sentence tree.
* `%=label=`: The subtree matched by the node labeled `label` inside the pattern.
* `%Nb`: The sentence tree that is `N` sentences *before* the current match (e.g., `%1b` for the previous sentence).
* `%Na`: The sentence tree that is `N` sentences *after* the current match.

---

## 3. Tree Formatting Modifiers

You can add a style modifier immediately after the `%` of any tree placeholder to customize how that subtree is printed:

| Modifier | Style | Example | Output |
| :--- | :--- | :--- | :--- |
| `l` | Long format | `%lh` | Multi-line indented tree |
| `t` | Terminals only | `%th` | Leaves (words) of head node |
| `u` | Top node name | `%uh` | Label of the head node |
| `n` | Node number | `%nh` | Depth-first pre-order node ID |
| `x` | Subtree code | `%xh` | Location code `s:n` |
| `k` | Word count | `%kh` | Count of terminal words under node |
| `d` | Depth of tree | `%dh` | Max tree depth (leaves have depth 1) |
| `y` | First terminal index | `%yh` | Index of first leaf word (1-indexed) |
| `z` | Last terminal index | `%zh` | Index of last leaf word (1-indexed) |

### Format Padding:
Just like `printf`, you can specify width and alignment. E.g., `%-5s` left-justifies the sentence number in a 5-character column.

---

## 4. Node Markers for Printing

By default, TGrep2 prints the subtree matched by the **head node** (the first node in the pattern). You can mark specific nodes for printing by prefixing them with a single back-quote `` ` ``:

* *Pattern*: `` NP << `JJ << `NN ``
* *Meaning*: Match an `NP` that dominates both a `JJ` and an `NN`, but print **only** the matching `JJ` and `NN` subtrees (separated by a newline in the output), rather than the parent `NP`.

In Python, these marked nodes are accessed together via the `%m` placeholder.

---

## 5. Python Parsing Recipes

Since `search_index` returns a list of strings representing the output lines, you can use tab-delimited formats to easily unpack structured records directly into Python objects.

### Recipe 1: Extracting Tab-Separated Data
```python
# Query: find NP dominating NNP, and output: sentence_number \t head_word \t tag_name
pattern = "NP < NNP"
fmt = "%s\\t%th\\t%uh\\n" # Note double backslash to escape tab in python string

matches = orchestrator.search_index(
    pattern, 
    t2c_path, 
    additional_args=["-m", fmt]
)

for line in matches:
    parts = line.split("\t")
    if len(parts) == 3:
        sent_num = int(parts[0])
        word = parts[1]
        tag = parts[2]
        print(f"Sentence #{sent_num}: Word '{word}' is under tag '{tag}'")
```

### Recipe 2: Extracting Labeled Subtrees
You can extract multiple subtrees of interest in a single query by using node labels and referencing them in the output format.

```python
# Query: Find NP dominating an NNP (labeled proper) and a VP sister
pattern = "S=sent << (NP=proper < NNP) $. VP=verb"
# Print: sentence_number | proper_phrase | verb_phrase
fmt = "%s|%=proper=t|%=verb=t\\n"

matches = orchestrator.search_index(
    pattern, 
    t2c_path, 
    additional_args=["-m", fmt]
)

for line in matches:
    sent_id, proper_txt, verb_txt = line.split("|")
    print(f"S#{sent_id}: '{proper_txt}' is sister to verb phrase '{verb_txt}'")
```
