import os
import subprocess
from pathlib import Path
from typing import List, Union, Optional

class TgrepOrchestrator:
    """
    Orchestrates a linguistic analysis pipeline:
    Raw Text -> .mrg (Penn Treebank format) -> .t2c (Tgrep2 Index) -> Search Results
    
    Uses spaCy & benepar for constituency parsing, and wraps the compiled
    tgrep2 binary for indexing and pattern searching.
    """

    def __init__(self, tgrep2_binary_path: Union[str, Path] = None):
        """
        Initializes the TgrepOrchestrator with the path to the tgrep2 binary.
        If no path is specified, it attempts to resolve the binary from common locations.
        
        Args:
            tgrep2_binary_path: Path to the tgrep2 executable.
        """
        if tgrep2_binary_path is None:
            # Common relative locations in this repository
            base_dir = Path(__file__).parent.resolve()
            local_bin = Path.home() / ".local" / "bin" / "tgrep2"
            
            # Fail-safe: if local bin doesn't exist, try to copy it from bundled package data
            bundled_bin = base_dir / "bin" / "tgrep2-andreasvc"
            if bundled_bin.exists():
                local_bin.parent.mkdir(parents=True, exist_ok=True)
                import shutil
                
                if not local_bin.exists():
                    try:
                        shutil.copy2(bundled_bin, local_bin)
                        local_bin.chmod(0o755)
                    except Exception:
                        pass

            possible_paths = [
                local_bin,
                base_dir / "bin" / "tgrep2-andreasvc",
                base_dir / "bin" / "tgrep2-bwaldon",
                Path.cwd() / "bin" / "tgrep2-andreasvc",
                Path.cwd() / "bin" / "tgrep2-bwaldon",
            ]
            for p in possible_paths:
                if p.exists() and os.access(p, os.X_OK):
                    tgrep2_binary_path = p
                    break
            else:
                # Fallback to system-wide executable
                tgrep2_binary_path = Path("tgrep2")
        else:
            tgrep2_binary_path = Path(tgrep2_binary_path)

        # Resolve path and validate executable status
        if tgrep2_binary_path.parent != Path("."):
            resolved_bin = tgrep2_binary_path.resolve()
            if not resolved_bin.exists():
                raise FileNotFoundError(f"tgrep2 binary not found at: {resolved_bin}")
            if not os.access(resolved_bin, os.X_OK):
                raise PermissionError(f"tgrep2 binary at {resolved_bin} is not executable.")
            self.tgrep2_binary_path = resolved_bin
        else:
            self.tgrep2_binary_path = tgrep2_binary_path

        self._nlp = None  # Lazy loaded spaCy pipeline

    def _init_nlp(self):
        """
        Helper method to perform lazy initialization of spaCy and benepar.
        This avoids heavy loading overhead during object initialization.
        """
        if self._nlp is not None:
            return

        try:
            import spacy
            import benepar
            import nltk
        except ImportError as e:
            raise ImportError(
                "Parsing requires 'spacy', 'benepar', and 'nltk' to be installed. "
                "Please run: pip install spacy benepar nltk"
            ) from e

        # Load spaCy model
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            raise OSError(
                "spaCy model 'en_core_web_sm' is missing. "
                "Please run: python -m spacy download en_core_web_sm"
            )

        # Check if benepar_en3 model is downloaded, otherwise download it
        try:
            nltk.data.find("models/benepar_en3")
        except LookupError:
            print("benepar_en3 model not found. Attempting to download...")
            try:
                benepar.download("benepar_en3")
            except Exception as e:
                raise RuntimeError(
                    f"Failed to download 'benepar_en3' model automatically: {e}. "
                    "Please verify your internet connection or manually run: "
                    "python -c \"import benepar; benepar.download('benepar_en3')\""
                ) from e

        # Add benepar pipe depending on spaCy version
        try:
            if spacy.__version__.startswith("2."):
                from benepar.spacy_interface import BeneparComponent
                nlp.add_pipe(BeneparComponent("benepar_en3"))
            else:
                nlp.add_pipe("benepar", config={"model": "benepar_en3"})
        except Exception as e:
            raise RuntimeError(
                f"Failed to add benepar component to spaCy pipeline: {e}."
            ) from e

        self._nlp = nlp

    def parse_to_mrg(
        self, 
        texts: List[str], 
        mrg_path: Union[str, Path], 
        batch_size: int = 64
    ) -> List[object]:
        """
        Uses spaCy and benepar to parse raw text strings into constituency trees,
        exports them in Penn Treebank (.mrg) format (one tree per line), and returns
        a list of NLTK Tree objects.

        Args:
            texts: A list of raw text strings to parse.
            mrg_path: Destination path for the .mrg file.
            batch_size: Batch size for spaCy nlp.pipe to optimize performance.

        Returns:
            A list of nltk.tree.Tree objects representing the parsed sentences.
        """
        self._init_nlp()
        mrg_path = Path(mrg_path).resolve()
        mrg_path.parent.mkdir(parents=True, exist_ok=True)

        # Attempt to import nltk Tree for return object conversion
        try:
            from nltk.tree import Tree as NltkTree
        except ImportError:
            NltkTree = None

        tree_objects = []
        with mrg_path.open("w", encoding="utf-8") as f:
            # nlp.pipe optimizes tokenization and parsing performance for large corpora
            for doc in self._nlp.pipe(texts, batch_size=batch_size):
                for sent in doc.sents:
                    parse_str = sent._.parse_string
                    if not parse_str:
                        continue
                    
                    # Clean and write tree to .mrg (one tree per line)
                    clean_parse = parse_str.strip()
                    f.write(clean_parse + "\n")

                    if NltkTree is not None:
                        try:
                            tree_objects.append(NltkTree.fromstring(clean_parse))
                        except Exception:
                            # If tree formatting fails to load in NLTK, skip object creation
                            pass
                    else:
                        # If NLTK is not available, append the string representation
                        tree_objects.append(clean_parse)

        return tree_objects

    def index_corpus(
        self, 
        mrg_path: Union[str, Path], 
        t2c_path: Union[str, Path] = None
    ) -> Path:
        """
        Invokes the tgrep2 tool via a secure subprocess call to compile a .mrg file
        into a binary .t2c corpus index.

        Args:
            mrg_path: Path to the Penn Treebank (.mrg) file.
            t2c_path: Path to write the .t2c index. Defaults to same name as mrg_path.

        Returns:
            The Path to the compiled .t2c file.
        """
        mrg_path = Path(mrg_path).resolve()
        if not mrg_path.exists():
            raise FileNotFoundError(f"Penn Treebank source file not found: {mrg_path}")

        if t2c_path is None:
            t2c_path = mrg_path.with_suffix(".t2c")
        else:
            t2c_path = Path(t2c_path).resolve()

        t2c_path.parent.mkdir(parents=True, exist_ok=True)

        # Build execution list securely (no shell=True) to avoid shell-injection risks.
        cmd = [str(self.tgrep2_binary_path), "-C", "-K", "-p", str(mrg_path), str(t2c_path)]

        try:
            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                stdin=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"tgrep2 indexing failed with exit code {e.returncode}.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Stderr: {e.stderr.strip()}"
            ) from e

        return t2c_path

    def search_index(
        self, 
        pattern: str, 
        t2c_path: Union[str, Path],
        additional_args: Optional[List[str]] = None
    ) -> List[str]:
        """
        Runs a tgrep2 pattern search against the .t2c index file and returns
        the matching subtrees as a list of Python-accessible tree strings.

        Args:
            pattern: The Tgrep pattern query (e.g. 'NP < VP').
            t2c_path: Path to the .t2c binary index file.
            additional_args: List of optional command-line flags to pass to tgrep2.

        Returns:
            A list of matched tree strings in Penn Treebank format.
        """
        t2c_path = Path(t2c_path).resolve()
        if not t2c_path.exists():
            raise FileNotFoundError(f"tgrep2 index file not found: {t2c_path}")

        # Secure arguments list. No shell parsing is executed.
        cmd = [str(self.tgrep2_binary_path), "-c", str(t2c_path)]
        
        if additional_args:
            # Ensure type safety of additional arguments
            for arg in additional_args:
                if not isinstance(arg, str):
                    raise ValueError(f"Additional argument must be a string: {arg}")
            cmd.extend(additional_args)

        cmd.append(pattern)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                stdin=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"tgrep2 search failed with exit code {e.returncode}.\n"
                f"Command: {' '.join(cmd)}\n"
                f"Stderr: {e.stderr.strip()}"
            ) from e

        # Extract and clean match outputs
        matches = []
        for line in result.stdout.splitlines():
            line_stripped = line.strip()
            if line_stripped:
                matches.append(line_stripped)

        return matches

    def _escape_word_or_regex(self, word: str) -> str:
        """
        Safely formats a word query. If the word starts and ends with '/',
        it is assumed to be a regular expression. Otherwise, if it contains
        tgrep2 syntax characters, it is escaped as a strict regex.
        """
        if word.startswith('/') and word.endswith('/'):
            return word
        
        special_chars = set(" <>.$,&|!()=[]/:~@*\"'")
        if any(c in special_chars for c in word):
            import re
            escaped = re.escape(word)
            return f"/^{escaped}$/"
        return word

    def _build_word_pattern(self, word: str, pos: Optional[str] = None) -> str:
        """Helper to build a pattern for matching a single word with optional POS tag."""
        word_term = self._escape_word_or_regex(word)
        leaf_term = f"({word_term} !< __)"
        if pos:
            pos_term = pos if (pos.startswith('/') and pos.endswith('/')) else pos
            return f"({pos_term} < {leaf_term})"
        else:
            return f"(__ < {leaf_term})"

    def search_word(
        self,
        word: str,
        t2c_path: Union[str, Path],
        pos: Optional[str] = None,
        case_insensitive: bool = True,
        return_type: Optional[str] = None,
        additional_args: Optional[List[str]] = None
    ) -> Union[List[dict], List[str]]:
        """
        Search the index for occurrences of a single word, optionally filtered by part-of-speech (POS).

        Args:
            word: The word to search for (e.g. 'loves' or regex pattern '/^[Jj]ohn$/').
            t2c_path: Path to the .t2c index file.
            pos: Optional POS tag to filter by (e.g. 'VBZ', 'NNP').
            case_insensitive: If True, performs case-insensitive search (default is True).
            return_type: If None (default), returns a list of dictionaries with 'subtree', 'tree',
                         and 'sentence'. Otherwise choose from 'subtree', 'tree', 'sentence'
                         to return a list of formatted strings.
            additional_args: Any additional arguments to pass to tgrep2.

        Returns:
            List of matching results (dictionaries or formatted strings).
        """
        pattern = self._build_word_pattern(word, pos)
        
        args = list(additional_args) if additional_args else []
        if case_insensitive and "-i" not in args:
            args.append("-i")
        if "-a" not in args:
            args.append("-a")
            
        if return_type is None:
            if "-m" not in args:
                args.extend(["-m", "%s ||| %h ||| %w ||| %tw\n"])
        elif return_type == "tree":
            if "-w" not in args:
                args.append("-w")
        elif return_type == "sentence":
            if "-w" not in args:
                args.append("-w")
            if "-t" not in args:
                args.append("-t")
        elif return_type == "subtree":
            pass
        else:
            raise ValueError(f"Invalid return_type: {return_type}. Choose from None, 'subtree', 'tree', 'sentence'.")

        matches = self.search_index(pattern, t2c_path, additional_args=args)
        
        if return_type is None:
            parsed_matches = []
            for m in matches:
                parts = m.split(" ||| ", 3)
                if len(parts) == 4:
                    parsed_matches.append({
                        "sentence_index": int(parts[0]) - 1,
                        "subtree": parts[1],
                        "tree": parts[2],
                        "sentence": parts[3]
                    })
            return parsed_matches
            
        return matches

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
    ) -> Union[List[dict], List[str]]:
        """
        Search for collocations of two words with specific syntactic/structural relations.

        Args:
            word1: The first word.
            word2: The second word.
            t2c_path: Path to the .t2c index file.
            relation: Relation type:
                      'immediate' (word1 immediately precedes word2),
                      'precedes' (word1 precedes word2 at any distance/limited distance),
                      'sister' (word1 is a sister of and precedes word2),
                      'sister_immediate' (word1 is a sister of and immediately precedes word2).
            distance: If relation is 'precedes', limits the maximum number of words
                      between word1 and word2.
            pos1: Optional POS tag for word1.
            pos2: Optional POS tag for word2.
            case_insensitive: If True, performs case-insensitive search (default is True).
            return_type: If None (default), returns a list of dictionaries with 'subtree', 'tree',
                         and 'sentence'. Otherwise choose from 'subtree', 'tree', 'sentence'.
            additional_args: Any additional arguments.
        """
        w1_pat = self._build_word_pattern(word1, pos1)
        w2_pat = self._build_word_pattern(word2, pos2)

        args = list(additional_args) if additional_args else []
        if case_insensitive and "-i" not in args:
            args.append("-i")
        if "-a" not in args:
            args.append("-a")
            
        if return_type is None:
            if "-m" not in args:
                args.extend(["-m", "%s ||| %h ||| %w ||| %tw\n"])
        elif return_type == "tree":
            if "-w" not in args:
                args.append("-w")
        elif return_type == "sentence":
            if "-w" not in args:
                args.append("-w")
            if "-t" not in args:
                args.append("-t")
        elif return_type == "subtree":
            pass
        else:
            raise ValueError(f"Invalid return_type: {return_type}. Choose from None, 'subtree', 'tree', 'sentence'.")

        if relation == "immediate":
            pattern = f"({w1_pat} . {w2_pat})"
        elif relation == "sister_immediate":
            pattern = f"({w1_pat} $. {w2_pat})"
        elif relation == "sister":
            pattern = f"({w1_pat} $.. {w2_pat})"
        elif relation == "precedes":
            if distance is not None:
                if distance < 1:
                    raise ValueError("distance must be at least 1")
                all_matches = []
                for d in range(1, distance + 1):
                    inner = w2_pat
                    for _ in range(d - 1):
                        inner = f"(__ . {inner})"
                    pattern = f"({w1_pat} . {inner})"
                    matches = self.search_index(pattern, t2c_path, additional_args=args)
                    all_matches.extend(matches)
                
                # Deduplicate while preserving order
                seen = set()
                unique_matches = []
                for m in all_matches:
                    if m not in seen:
                        seen.add(m)
                        unique_matches.append(m)
            else:
                pattern = f"({w1_pat} .. {w2_pat})"
        else:
            raise ValueError(f"Unknown relation: {relation}")

        if relation != "precedes" or distance is None:
            unique_matches = self.search_index(pattern, t2c_path, additional_args=args)

        if return_type is None:
            parsed_matches = []
            for m in unique_matches:
                parts = m.split(" ||| ", 3)
                if len(parts) == 4:
                    parsed_matches.append({
                        "sentence_index": int(parts[0]) - 1,
                        "subtree": parts[1],
                        "tree": parts[2],
                        "sentence": parts[3]
                    })
            return parsed_matches

        return unique_matches

    def search_pos(
        self,
        pos_tag: str,
        t2c_path: Union[str, Path],
        word: Optional[str] = None,
        case_insensitive: bool = True,
        return_type: Optional[str] = None,
        additional_args: Optional[List[str]] = None
    ) -> Union[List[dict], List[str]]:
        """
        Search for words matching a part-of-speech (POS) tag.
        Supports common aliases: NOUN, VERB, ADJ, ADV, PRON, DET.
        """
        pos_map = {
            "NOUN": "/^NN/",     # NN, NNS, NNP, NNPS
            "VERB": "/^VB/",     # VB, VBD, VBG, VBN, VBP, VBZ
            "ADJ": "/^JJ/",      # JJ, JJR, JJS
            "ADV": "/^RB/",      # RB, RBR, RBS, WRB
            "PRON": "/^PRP/",    # PRP, PRP$
            "DET": "/^DT/",      # DT
        }
        
        normalized_pos = pos_map.get(pos_tag.upper(), pos_tag)
        
        if word:
            pattern = self._build_word_pattern(word, normalized_pos)
        else:
            pattern = normalized_pos

        args = list(additional_args) if additional_args else []
        if case_insensitive and "-i" not in args:
            args.append("-i")
        if "-a" not in args:
            args.append("-a")
            
        if return_type is None:
            if "-m" not in args:
                args.extend(["-m", "%s ||| %h ||| %w ||| %tw\n"])
        elif return_type == "tree":
            if "-w" not in args:
                args.append("-w")
        elif return_type == "sentence":
            if "-w" not in args:
                args.append("-w")
            if "-t" not in args:
                args.append("-t")
        elif return_type == "subtree":
            pass
        else:
            raise ValueError(f"Invalid return_type: {return_type}. Choose from None, 'subtree', 'tree', 'sentence'.")

        matches = self.search_index(pattern, t2c_path, additional_args=args)
        
        if return_type is None:
            parsed_matches = []
            for m in matches:
                parts = m.split(" ||| ", 3)
                if len(parts) == 4:
                    parsed_matches.append({
                        "sentence_index": int(parts[0]) - 1,
                        "subtree": parts[1],
                        "tree": parts[2],
                        "sentence": parts[3]
                    })
            return parsed_matches
            
        return matches

    def search_phrase(
        self,
        phrase_tag: str,
        t2c_path: Union[str, Path],
        contains: Optional[List[str]] = None,
        immediate: bool = True,
        case_insensitive: bool = True,
        return_type: Optional[str] = None,
        additional_args: Optional[List[str]] = None
    ) -> Union[List[dict], List[str]]:
        """
        Search for syntactic phrases (e.g. NP, VP, PP) containing specified children/descendants.

        Args:
            phrase_tag: The phrase type (e.g. 'NP', 'VP', 'PP', 'S').
            t2c_path: Path to the .t2c index file.
            contains: List of child/descendant node labels or words that the phrase must contain.
            immediate: If True, the children in 'contains' must be immediately dominated
                       by the phrase (operator '<').
                       If False, they can be descendants at any depth (operator '<<').
            case_insensitive: If True, performs case-insensitive search (default is True).
            return_type: If None (default), returns a list of dictionaries with 'subtree', 'tree',
                         and 'sentence'. Otherwise choose from 'subtree', 'tree', 'sentence'.
            additional_args: Any additional arguments.
        """
        op = "<" if immediate else "<<"
        
        if not contains:
            pattern = phrase_tag
        else:
            formatted_children = []
            for child in contains:
                if child.isupper() and len(child) <= 4:
                    formatted_children.append(child)
                else:
                    formatted_children.append(self._escape_word_or_regex(child))
            
            child_clauses = [f"{op} {c}" for c in formatted_children]
            pattern = f"{phrase_tag} {' & '.join(child_clauses)}"

        args = list(additional_args) if additional_args else []
        if case_insensitive and "-i" not in args:
            args.append("-i")
        if "-a" not in args:
            args.append("-a")
            
        if return_type is None:
            if "-m" not in args:
                args.extend(["-m", "%s ||| %h ||| %w ||| %tw\n"])
        elif return_type == "tree":
            if "-w" not in args:
                args.append("-w")
        elif return_type == "sentence":
            if "-w" not in args:
                args.append("-w")
            if "-t" not in args:
                args.append("-t")
        elif return_type == "subtree":
            pass
        else:
            raise ValueError(f"Invalid return_type: {return_type}. Choose from None, 'subtree', 'tree', 'sentence'.")

        matches = self.search_index(pattern, t2c_path, additional_args=args)
        
        if return_type is None:
            parsed_matches = []
            for m in matches:
                parts = m.split(" ||| ", 3)
                if len(parts) == 4:
                    parsed_matches.append({
                        "sentence_index": int(parts[0]) - 1,
                        "subtree": parts[1],
                        "tree": parts[2],
                        "sentence": parts[3]
                    })
            return parsed_matches
            
        return matches
