import os
import tempfile
from pathlib import Path
from typing import List, Union, Optional, Dict, Any, Callable
from google import genai
from google.genai import types

from .tgrep_orchestrator import TgrepOrchestrator
from .query_generator import TgrepQueryGenerator

class TgrepSemanticAnalyzer:
    """
    Coordinates Syntactically-Filtered Semantic Analysis.
    Prunes/filters a text corpus or index using pytgrep2, then runs semantic analysis
    on the matched sentences using Google GenAI (Gemini).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3.1-flash-lite",
        orchestrator: Optional[TgrepOrchestrator] = None,
        query_generator: Optional[TgrepQueryGenerator] = None,
    ):
        """
        Initializes the TgrepSemanticAnalyzer.

        Args:
            api_key: Google GenAI API key. If None, resolves from standard environment variables.
            model: Gemini model name (defaults to 'gemini-3.1-flash-lite').
            orchestrator: Optional custom TgrepOrchestrator instance.
            query_generator: Optional custom TgrepQueryGenerator instance.
        """
        # Resolve API Key
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model = model
        
        # Initialize Google GenAI client
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = genai.Client()
        
        self.orchestrator = orchestrator or TgrepOrchestrator()
        self.query_generator = query_generator or TgrepQueryGenerator(
            api_key=self.api_key,
            model=model,
            orchestrator=self.orchestrator
        )

    def _construct_prompt(
        self,
        sentence: str,
        subtrees: List[str],
        task: str,
        metadata: Optional[Any] = None,
        custom_prompt_formatter: Optional[Callable[[str, List[str], Any, str], str]] = None
    ) -> str:
        """Helper to construct the prompt sent to Gemini."""
        if custom_prompt_formatter:
            return custom_prompt_formatter(sentence, subtrees, metadata, task)
            
        prompt_parts = [
            "You are an expert natural language processing and linguistic analysis assistant.",
            f"Your task is to analyze the following sentence:\n\"{sentence}\""
        ]
        
        if len(subtrees) == 1:
            prompt_parts.append(
                f"The sentence was selected because it matches a syntactic pattern. "
                f"The matching subtree is:\n{subtrees[0]}"
            )
        else:
            prompt_parts.append(
                "The sentence was selected because it matches a syntactic pattern. "
                "The matching subtrees are:"
            )
            for s in subtrees:
                prompt_parts.append(f"- {s}")
                
        if metadata is not None:
            prompt_parts.append(f"Here is additional metadata associated with this sentence:\n{metadata}")
            
        prompt_parts.append(f"\nTask Instruction: {task}")
        prompt_parts.append("\nAnalysis:")
        
        return "\n".join(prompt_parts)

    def _call_gemini(
        self,
        prompt: str,
        response_schema: Optional[Any] = None,
        response_mime_type: Optional[str] = None
    ) -> str:
        """Helper to call Gemini API."""
        config_args = {}
        if response_mime_type:
            config_args["response_mime_type"] = response_mime_type
        if response_schema:
            config_args["response_schema"] = response_schema
            
        config = types.GenerateContentConfig(**config_args) if config_args else None
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config
        )
        return response.text.strip() if response.text else ""

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
    ) -> List[Dict[str, Any]]:
        """
        Executes the Syntactically-Filtered Semantic Analysis workflow.

        Args:
            corpus: List of raw strings, or path to a Penn Treebank (.mrg) file, or path to a 
                    TGrep2 index (.t2c / .t2c.gz) file.
            pattern_or_desc: A direct TGrep2 pattern string or a natural language description.
            semantic_task: The natural language task prompt for Gemini.
            metadata: Optional metadata aligned with corpus by 0-based sentence index.
            is_pattern: If True, treats pattern_or_desc as a direct TGrep2 pattern. 
                        If False, translates pattern_or_desc to a pattern using query generator.
            max_results: Maximum number of matching sentences to analyze with Gemini.
            case_insensitive: Perform case-insensitive structural matching (adds -i flag).
            response_schema: Optional response schema for structured Gemini output.
            response_mime_type: Optional response mime type (e.g. 'application/json').
            custom_prompt_formatter: Optional custom prompt builder callback function.

        Returns:
            List of dictionaries, each containing:
              - 'sentence_index': 0-based index of the matched sentence
              - 'sentence': The raw sentence string
              - 'subtrees': List of matched Penn Treebank subtrees
              - 'tree': The full parse tree
              - 'metadata': Corresponding metadata (if provided)
              - 'analysis': The text or structured JSON output from Gemini
              - 'pattern': The final TGrep2 pattern used
        """
        # 1. Resolve/generate TGrep2 pattern
        if is_pattern:
            pattern = pattern_or_desc.strip()
        else:
            pattern = self.query_generator.generate_pattern(pattern_or_desc)

        # 2. Determine corpus handling
        temp_dir = None
        t2c_path = None
        
        try:
            if isinstance(corpus, (list, tuple)):
                # Parse and compile list of texts
                temp_dir = tempfile.TemporaryDirectory(prefix="pytgrep2_analysis_")
                temp_path = Path(temp_dir.name)
                mrg_file = temp_path / "corpus.mrg"
                t2c_path = temp_path / "corpus.t2c"
                
                self.orchestrator.parse_to_mrg(corpus, mrg_file)
                self.orchestrator.index_corpus(mrg_file, t2c_path)
            else:
                corpus_path = Path(corpus).resolve()
                if not corpus_path.exists():
                    raise FileNotFoundError(f"Corpus file not found: {corpus_path}")
                
                if corpus_path.name.endswith(".t2c") or corpus_path.name.endswith(".t2c.gz"):
                    t2c_path = corpus_path
                else:
                    # Treat as .mrg or other file: compile to .t2c
                    temp_dir = tempfile.TemporaryDirectory(prefix="pytgrep2_analysis_")
                    temp_path = Path(temp_dir.name)
                    t2c_path = temp_path / corpus_path.with_suffix(".t2c").name
                    self.orchestrator.index_corpus(corpus_path, t2c_path)

            # 3. Search index with custom format to retrieve indexes and subtrees
            args = ["-a", "-m", "%s ||| %h ||| %w ||| %tw\n"]
            if case_insensitive:
                args.append("-i")
                
            matches = self.orchestrator.search_index(pattern, t2c_path, additional_args=args)

            # 4. Group matches by sentence index
            grouped_matches = {}
            for m in matches:
                parts = m.split(" ||| ", 3)
                if len(parts) == 4:
                    try:
                        sent_idx = int(parts[0]) - 1
                        if sent_idx not in grouped_matches:
                            grouped_matches[sent_idx] = {
                                "sentence_index": sent_idx,
                                "subtree": parts[1],
                                "tree": parts[2],
                                "sentence": parts[3],
                                "subtrees": []
                            }
                        grouped_matches[sent_idx]["subtrees"].append(parts[1])
                    except ValueError:
                        pass

            # 5. Perform semantic analysis on the matches (up to max_results)
            sorted_indices = sorted(grouped_matches.keys())
            if max_results is not None:
                sorted_indices = sorted_indices[:max_results]

            results = []
            for sent_idx in sorted_indices:
                item = grouped_matches[sent_idx]
                sentence = item["sentence"]
                subtrees = item["subtrees"]
                tree = item["tree"]
                
                # Align metadata
                meta = None
                if metadata is not None:
                    if isinstance(metadata, list):
                        if 0 <= sent_idx < len(metadata):
                            meta = metadata[sent_idx]
                    elif isinstance(metadata, dict):
                        meta = metadata.get(sent_idx) or metadata.get(str(sent_idx))

                # Build prompt and query Gemini
                prompt = self._construct_prompt(
                    sentence=sentence,
                    subtrees=subtrees,
                    task=semantic_task,
                    metadata=meta,
                    custom_prompt_formatter=custom_prompt_formatter
                )
                
                analysis = self._call_gemini(prompt, response_schema, response_mime_type)
                
                results.append({
                    "sentence_index": sent_idx,
                    "sentence": sentence,
                    "subtrees": subtrees,
                    "tree": tree,
                    "metadata": meta,
                    "analysis": analysis,
                    "pattern": pattern
                })
                
            return results
            
        finally:
            # Clean up temp files
            if temp_dir is not None:
                try:
                    temp_dir.cleanup()
                except Exception:
                    pass
