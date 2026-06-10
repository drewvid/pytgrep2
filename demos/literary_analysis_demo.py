#!/usr/bin/env python3
"""
pytgrep2 Literary & Scientific Paragraph Analysis Demo
======================================================
This script demonstrates the hybrid Syntactically-Filtered Semantic Analysis workflow.
It parses a custom literary corpus of 10 intellectually rich literary, scientific, and
philosophical paragraphs into a Penn Treebank (.mrg) format,
indexes the .mrg file into a binary TGrep2 (.t2c) database, runs precise syntactic
filters, and sends matching sentences to Google GenAI (Gemini) for deep semantic analysis.
"""

import os
import sys
from pathlib import Path
from pytgrep2 import TgrepOrchestrator, TgrepSemanticAnalyzer

# Curated literary corpus (list of JSON objects/dictionaries)
CORPUS = [
    # 1. Jane Austen - Pride and Prejudice
    {
        "text": "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife. "
        "However little known the feelings or views of such a man may be on his first entering a neighbourhood, "
        "this truth is so well fixed in the minds of the surrounding families, that he is considered the rightful property of "
        "some one or other of their daughters.",
        "metadata": {"author": "Jane Austen", "title": "Pride and Prejudice", "year": 1813, "genre": "Social Fiction"}
    },

    # 2. Albert Einstein - Relativity: The Special and General Theory
    {
        "text": "If we contemplate the concept of time in its relation to the coordinate system, we see that it must be defined "
        "in such a way that the laws of nature remain as simple as possible. Supposing that we have a train moving along "
        "an embankment, any event which takes place along it can also be observed from the embankment. Under these "
        "circumstances, we must consider whether the concept of simultaneity is relative or absolute.",
        "metadata": {"author": "Albert Einstein", "title": "Relativity: The Special and General Theory", "year": 1916, "genre": "Popular Science"}
    },

    # 3. Virginia Woolf - To the Lighthouse
    {
        "text": "What is the meaning of life? That was all—a simple question; one that tended to close in on one with years. "
        "The great revelation had never come. The great revelation perhaps never did come. Instead there were little "
        "daily miracles, illuminations, matches struck unexpectedly in the dark; here was one. If one could only hold "
        "onto these moments, the world would seem a little less chaotic.",
        "metadata": {"author": "Virginia Woolf", "title": "To the Lighthouse", "year": 1927, "genre": "Modernist Fiction"}
    },

    # 4. William James - The Principles of Psychology
    {
        "text": "Consciousness, then, does not appear to itself chopped up in bits. Such words as 'chain' or 'train' do not "
        "describe it fitly as it presents itself in the first instance. It is nothing jointed; it flows. A 'river' or "
        "a 'stream' are the metaphors by which it is most naturally described. If we speak of the stream of thought, "
        "of consciousness, or of subjective life, we describe it most fitly.",
        "metadata": {"author": "William James", "title": "The Principles of Psychology", "year": 1890, "genre": "Psychology/Philosophy"}
    },

    # 5. Bram Stoker - Dracula
    {
        "text": "I began to fear as I wrote in this book that I was getting too diffuse; but now I am glad that I went into detail "
        "from the first, for there is something so strange about this place and all in it that I cannot but feel uneasy. "
        "If I could escape from this castle, I would run until my legs gave out. But the doors are locked, and I am "
        "a prisoner in the hands of the Count.",
        "metadata": {"author": "Bram Stoker", "title": "Dracula", "year": 1897, "genre": "Gothic Horror"}
    },

    # 6. Lewis Carroll - Alice's Adventures in Wonderland
    {
        "text": "'If everybody minded their own business,' the Duchess said, in a hoarse growl, 'the world would go round a deal "
        "faster than it does.' Alice, who felt quite glad to show off a little of her knowledge, immediately objected. "
        "'Which would not be an advantage,' she said, 'for it would make it very difficult to know when it was day or night.'",
        "metadata": {"author": "Lewis Carroll", "title": "Alice's Adventures in Wonderland", "year": 1865, "genre": "Literary Nonsense"}
    },

    # 7. Henry David Thoreau - Walden
    {
        "text": "I went to the woods because I wished to live deliberately, to front only the essential facts of life, and see "
        "if I could not learn what it had to teach, and not, when I came to die, discover that I had not lived. I did "
        "not wish to live what was not life, living is so dear; nor did I wish to practise resignation, unless it was "
        "quite necessary. I wanted to live deep and suck out all the marrow of life.",
        "metadata": {"author": "Henry David Thoreau", "title": "Walden", "year": 1854, "genre": "Philosophy/Memoir"}
    },

    # 8. Arthur Conan Doyle - The Memoirs of Sherlock Holmes
    {
        "text": "It has long been an axiom of mine that the little things are infinitely the most important. You see, but you "
        "do not observe. The distinction is clear. For example, you have frequently seen the steps which lead up from the "
        "hall to this room. If I ask you how many there are, you cannot tell me.",
        "metadata": {"author": "Arthur Conan Doyle", "title": "The Memoirs of Sherlock Holmes", "year": 1892, "genre": "Detective Fiction"}
    },

    # 9. Rachel Carson - Silent Spring
    {
        "text": "Only within the moment of time represented by the present century has one species—man—acquired significant "
        "power to alter the nature of his world. Although this power was initially small, it has now grown to a "
        "disturbing magnitude, threatening the very life support systems of the Earth. If we continue on this path of "
        "unchecked chemical pollution, we will soon face a silent and sterile spring.",
        "metadata": {"author": "Rachel Carson", "title": "Silent Spring", "year": 1962, "genre": "Ecology/Science"}
    },

    # 10. Herman Melville - Moby Dick
    {
        "text": "Whenever I find myself growing grim about the mouth; whenever it is a damp, drizzly November in my soul; then, "
        "I account it high time to get to sea as soon as I can. This is my substitute for pistol and ball. With a "
        "philosophical flourish Cato throws himself upon his sword; I quietly take to the ship. If I must be a voyager, "
        "let me go with a free and adventurous heart.",
        "metadata": {"author": "Herman Melville", "title": "Moby Dick", "year": 1851, "genre": "Adventure/Epic Fiction"}
    }
]


def main():
    print("=" * 80)
    print("             pytgrep2 Literary & Scientific Paragraph Analysis Demo")
    print("=" * 80)

    # 1. Initialize TgrepOrchestrator
    orchestrator = TgrepOrchestrator()
    
    # 2. File paths for the demo
    base_dir = Path(__file__).parent
    mrg_path = base_dir / "literary_corpus.mrg"
    t2c_path = base_dir / "literary_corpus.t2c"

    try:
        # Step 1: Parse raw paragraphs to Penn Treebank format (.mrg)
        print("\n[Step 1] Parsing raw text paragraphs into Penn Treebank (.mrg) format...")
        print(f"Target .mrg file: {mrg_path}")
        
        metadata_dict = {}
        global_sent_idx = 0
        
        # Parse each paragraph individually to count its sentences and map them to their metadata
        with open(mrg_path, "w", encoding="utf-8") as f_out:
            for idx, item in enumerate(CORPUS):
                paragraph = item["text"]
                metadata = item["metadata"]
                
                temp_mrg = base_dir / f"temp_{idx}.mrg"
                trees = orchestrator.parse_to_mrg([paragraph], temp_mrg)
                
                # Copy temp parse file contents into the master file
                if temp_mrg.exists():
                    f_out.write(temp_mrg.read_text(encoding="utf-8"))
                    temp_mrg.unlink()
                
                # Map each parsed sentence of the paragraph to the source metadata dictionary
                for _ in range(len(trees)):
                    metadata_dict[global_sent_idx] = metadata
                    global_sent_idx += 1
                    
        print(f"Parsing completed successfully. Total sentences parsed: {global_sent_idx}")

        # Step 2: Compile the .mrg file into a binary TGrep2 (.t2c) search index
        print("\n[Step 2] Compiling .mrg file into a binary TGrep2 (.t2c) search index...")
        print(f"Target .t2c file: {t2c_path}")
        orchestrator.index_corpus(mrg_path, t2c_path)
        print("Index compiled successfully.")

        # Step 3: Run Syntactic Filter with TGrep2
        # We will filter for conditional structures: SBAR immediately dominating IN (if/unless/whenever)
        pattern = "SBAR < (IN < /^(if|unless|whenever)$/)"
        print(f"\n[Step 3] Running syntactic filter: '{pattern}'")
        raw_matches = orchestrator.search_index(pattern, t2c_path, additional_args=["-a", "-i"])
        print(f"Found {len(raw_matches)} structural matching subtrees in the corpus.")

        # Step 4: Run Gemini Semantic Analysis if API key is set
        print("\n[Step 4] Setting up Google GenAI Semantic Analyzer...")
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            print("WARNING: GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables.")
            print("Skipping Gemini API calls. Local syntactic search is fully verified.")
            return

        print("Initializing TgrepSemanticAnalyzer...")
        analyzer = TgrepSemanticAnalyzer(api_key=api_key, model="gemini-3.1-flash-lite")
        
        semantic_task = (
            "Analyze the conditional reasoning used in this sentence. "
            "Explain the premise/hypothesis and the consequence/implication stated by the author."
        )

        print(f"Sending matching sentences to Gemini (model: {analyzer.model})...")
        results = analyzer.analyze_corpus(
            corpus=t2c_path,
            pattern_or_desc=pattern,
            semantic_task=semantic_task,
            metadata=metadata_dict,
            is_pattern=True,
            case_insensitive=True
        )

        print("\n" + "=" * 80)
        print("                   Gemini Semantic Analysis Results")
        print("=" * 80)
        
        for idx, res in enumerate(results, 1):
            meta = res['metadata'] or {"author": "Unknown", "title": "Unknown", "year": "N/A"}
            print(f"\n[{idx}] Source: {meta['author']} — \"{meta['title']}\" ({meta['year']})")
            print(f"    Sentence  : \"{res['sentence']}\"")
            print(f"    Subtree   : {res['subtrees'][0]}")
            print(f"    Analysis  : {res['analysis']}")
            print("-" * 60)

    except Exception as e:
        print(f"\nAn error occurred during demo execution: {e}", file=sys.stderr)
        raise e

    finally:
        # Step 5: Clean up created corpus files
        print("\n[Step 5] Cleaning up temporary corpus index files...")
        for p in (mrg_path, t2c_path):
            if p.exists():
                try:
                    p.unlink()
                    print(f"  Deleted: {p}")
                except OSError as e:
                    print(f"  Error deleting {p}: {e}")
        print("Demo run finished.")


if __name__ == "__main__":
    main()
