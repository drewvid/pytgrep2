import os
from pathlib import Path
from typing import Union, Optional, Dict
from google import genai
from google.genai import types
import compress_pickle
from .tgrep_orchestrator import TgrepOrchestrator

class TgrepQueryGenerator:
    """
    Translates natural language descriptions into valid TGrep2 query patterns.
    Uses Google GenAI Gemini and caches successful queries locally in a
    compressed pickle file.
    """

    def __init__(
        self,
        cache_path: Union[str, Path] = "tgrep_query_cache.pkl.gz",
        api_key: Optional[str] = None,
        model: str = "gemini-3.1-flash-lite",
        orchestrator: Optional[TgrepOrchestrator] = None
    ):
        self.cache_path = Path(cache_path)
        self.model = model
        self.orchestrator = orchestrator or TgrepOrchestrator()
        
        # Initialize GenAI Client
        self.client = genai.Client(api_key=api_key)
        
        self.cache: Dict[str, str] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Loads cached queries if the compressed cache file exists."""
        if self.cache_path.exists():
            try:
                loaded = compress_pickle.load(self.cache_path)
                if isinstance(loaded, dict):
                    self.cache = loaded
            except Exception:
                self.cache = {}
        else:
            self.cache = {}

    def _save_cache(self) -> None:
        """Saves current cache to the compressed cache file."""
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            compress_pickle.dump(self.cache, self.cache_path, compression="gzip")
        except Exception as e:
            raise RuntimeError(f"Failed to write cache to {self.cache_path}: {e}") from e

    def validate_pattern(self, pattern: str) -> bool:
        """
        Validates TGrep2 query pattern syntax.
        Returns True if the pattern syntax is valid, False otherwise.
        """
        temp_dir = Path("temp_validation")
        temp_dir.mkdir(exist_ok=True)
        mrg_file = temp_dir / "val.mrg"
        t2c_file = temp_dir / "val.t2c"
        try:
            with mrg_file.open("w", encoding="utf-8") as f:
                f.write("(S (NP (NNP John)) (VP (VBD saw) (NP (NNP Mary))))\n")
            
            self.orchestrator.index_corpus(mrg_file, t2c_file)
            self.orchestrator.search_index(pattern, t2c_file)
            return True
        except Exception:
            return False
        finally:
            if mrg_file.exists():
                mrg_file.unlink()
            if t2c_file.exists():
                t2c_file.unlink()
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()

    def _get_pattern_error(self, pattern: str) -> str:
        """Helper to capture the exact error message from tgrep2 binary execution."""
        temp_dir = Path("temp_validation")
        temp_dir.mkdir(exist_ok=True)
        mrg_file = temp_dir / "val.mrg"
        t2c_file = temp_dir / "val.t2c"
        try:
            with mrg_file.open("w", encoding="utf-8") as f:
                f.write("(S (NP (NNP John)) (VP (VBD saw) (NP (NNP Mary))))\n")
            self.orchestrator.index_corpus(mrg_file, t2c_file)
            self.orchestrator.search_index(pattern, t2c_file)
            return "No error detected"
        except Exception as e:
            return str(e)
        finally:
            if mrg_file.exists():
                mrg_file.unlink()
            if t2c_file.exists():
                t2c_file.unlink()
            if temp_dir.exists() and not any(temp_dir.iterdir()):
                temp_dir.rmdir()

    def generate_pattern(self, description: str, max_retries: int = 3) -> str:
        """
        Translates a natural language description into a valid TGrep2 query pattern.
        Checks cache first, generates with Gemini if not cached, and retries with feedback
        if pattern validation fails.
        """
        cleaned_desc = description.strip()
        if not cleaned_desc:
            raise ValueError("Description cannot be empty.")

        if cleaned_desc in self.cache:
            return self.cache[cleaned_desc]

        system_prompt = (
            "You are an expert linguistic analysis assistant. Your task is to translate a description "
            "of a grammatical/syntactic pattern into a valid TGrep2 query pattern.\n\n"
            "TGrep2 Operators Cheat Sheet:\n"
            "  Vertical Relations:\n"
            "  - A < B   : A immediately dominates B (A is parent of B)\n"
            "  - A > B   : A is child of B\n"
            "  - A << B  : A dominates B at any depth (A is ancestor of B)\n"
            "  - A >> B  : A is descendant of B\n"
            "  - A <: B  : B is the only child of A\n"
            "  - A <, B  : B is the first child of A\n"
            "  - A <- B  : B is the last child of A (also written as A <` B)\n"
            "  - A <<, B : B is the left-most descendant of A\n"
            "  Horizontal Relations:\n"
            "  - A . B   : A immediately precedes B\n"
            "  - A , B   : A immediately follows B\n"
            "  - A .. B  : A precedes B at any distance\n"
            "  - A ,, B  : A follows B at any distance\n"
            "  Sister Relations:\n"
            "  - A $ B   : A and B are sisters (share same parent, A != B)\n"
            "  - A $. B  : A is a sister of B and immediately precedes B\n"
            "  - A $.. B : A is a sister of B and precedes B\n"
            "  Boolean and Labeling:\n"
            "  - A !< B  : A does not dominate B\n"
            "  - A | B   : A or B\n"
            "  - A & B   : A and B (can also use space: A B)\n"
            "  - [ ... ] : Grouping relations (e.g., A < (B . C) or A < [B | C])\n"
            "  - /regex/ : Matches node label with regex (e.g., /^VB/ matches VB, VBD, VBG)\n"
            "  - Labeling: A=lbl ... =lbl refers back to the same node\n\n"
            "Examples:\n"
            "1. English: \"A noun phrase dominating an adjective\"\n"
            "   Pattern: NP < JJ\n"
            "2. English: \"A verb phrase containing a past-tense verb followed immediately by a direct object\"\n"
            "   Pattern: VP < (VBD . NP)\n"
            "3. English: \"Passive voice constructions\"\n"
            "   Pattern: VP < (AUX . (VP < VBN))\n\n"
            "Translate the description to a TGrep2 query pattern. Return ONLY the pattern string, with no markdown formatting or extra explanatory text."
        )

        user_prompt = f"English description: \"{cleaned_desc}\"\nPattern:"
        
        current_prompt = user_prompt
        for attempt in range(max_retries):
            response = self.client.models.generate_content(
                model=self.model,
                contents=current_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.0
                )
            )
            pattern = response.text.strip()
            
            if pattern.startswith("`") and pattern.endswith("`"):
                pattern = pattern.strip("`").strip()
            
            if self.validate_pattern(pattern):
                self.cache[cleaned_desc] = pattern
                self._save_cache()
                return pattern
            else:
                error_msg = self._get_pattern_error(pattern)
                current_prompt = (
                    f"{user_prompt}\n\n"
                    f"On a previous attempt, you generated the pattern: '{pattern}'.\n"
                    f"This pattern is invalid and caused the following error:\n{error_msg}\n\n"
                    f"Please correct the error and output a valid TGrep2 pattern."
                )

        raise RuntimeError(f"Failed to generate a valid TGrep2 pattern for description: '{cleaned_desc}' after {max_retries} attempts.")
