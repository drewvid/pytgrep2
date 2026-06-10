import sys
from pathlib import Path
from pytgrep2 import TgrepOrchestrator

def main():
    print("=== TGREP2 NLP Pipeline Example ===")
    
    # 1. Initialize the orchestrator
    # It automatically resolves and uses the compiled tgrep2-andreasvc binary
    orchestrator = TgrepOrchestrator()
    print(f"Using binary: {orchestrator.tgrep2_binary_path}\n")
    
    # 2. Define 20 sentences for parsing
    sentences = [
        "The quick brown fox jumps over the lazy dog.",
        "John loves Mary, but Mary loves Bill.",
        "A smart dog barked at the moon all night.",
        "The linguist analyzed the parsed tree structures.",
        "Computers can process natural language sentences easily.",
        "We are operating in a research environment.",
        "Constituency parsing generates hierarchical syntactic trees.",
        "TGrep2 is a command-line tool for corpus searching.",
        "Python wrappers simplify legacy tool integration.",
        "A robust pipeline manages the lifecycle of files.",
        "Sentence parsing requires a parser like benepar.",
        "The parser uses a self-attentive network architecture.",
        "Subprocess calls run binaries safely without shells.",
        "Penn Treebank format uses nested parentheses.",
        "Linguistic research often requires querying parsed corpora.",
        "Syntactic queries can find specific grammar patterns.",
        "The developer wrote an integration interface.",
        "Caching indices improves search performance significantly.",
        "The pipeline converts raw text into structural trees.",
        "This example script demonstrates the entire NLP workflow."
    ]
    
    # Define file paths
    mrg_path = Path("mrg-t2c/example_corpus.mrg")
    t2c_path = Path("mrg-t2c/example_corpus.t2c")
    
    try:
        # 3. Parse texts to .mrg file (Penn Treebank format)
        print("Step 1: Parsing 20 sentences using spaCy + benepar...")
        trees = orchestrator.parse_to_mrg(sentences, mrg_path)
        print(f"-> Successfully parsed sentences and saved to {mrg_path}")
        print(f"-> Sample parse: {trees[0]}\n")
        
        # 4. Compile .mrg file to .t2c index file
        print("Step 2: Compiling .mrg file to binary .t2c index...")
        orchestrator.index_corpus(mrg_path, t2c_path)
        print(f"-> Successfully compiled index file: {t2c_path}\n")
        
        # 5. Search the index for noun phrases
        # Let's search for noun phrases (NP) dominating a proper noun (NNP) or pronoun (PRP)
        pattern = "NP < NNP | < PRP"
        print(f"Step 3: Searching index for noun phrases dominating proper nouns/pronouns: '{pattern}'")
        matches = orchestrator.search_index(pattern, t2c_path, additional_args=["-a"])
        
        print(f"\nFound {len(matches)} matching noun phrase subtrees:")
        for idx, match in enumerate(matches):
            print(f"  [{idx + 1}] {match}")
            
    except Exception as e:
        print(f"\nAn error occurred during pipeline execution: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
