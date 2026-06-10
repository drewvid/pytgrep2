import json
import sys
from pathlib import Path

# Add repository root to path to enable local import of pytgrep2
base_dir = Path(__file__).parent.parent.resolve()
sys.path.append(str(base_dir))

from pytgrep2 import TgrepOrchestrator

def main():
    print("=== TGREP2 Metadata Mapping Example (Scale-Friendly Approach) ===")
    
    # 1. Define sentences/trees from 3 different sources
    corpus_data = [
        {
            "tree": "(ROOT (S (NP (NNS Astronomers)) (VP (VBD discovered) (NP (DT a) (JJ new) (NN planet))) (. .)))",
            "metadata": {
                "article_id": "art_001",
                "title": "Astronomers discover a new planet",
                "source": "Space News Daily",
                "date": "2026-06-01"
            }
        },
        {
            "tree": "(ROOT (S (NP (DT The) (JJ local) (NN team)) (VP (VBD won) (NP (DT the) (NN championship))) (. .)))",
            "metadata": {
                "article_id": "art_002",
                "title": "Local team wins the championship",
                "source": "Daily Sports",
                "date": "2026-06-03"
            }
        },
        {
            "tree": "(ROOT (S (NP (DT The) (NN tech) (NN company)) (VP (VBD announced) (NP (DT a) (JJ new) (NN model))) (. .)))",
            "metadata": {
                "article_id": "art_003",
                "title": "Tech giant announces new AI model",
                "source": "Tech Weekly",
                "date": "2026-06-07"
            }
        }
    ]
    
    # Define file paths
    mrg_path = Path("mrg-t2c/metadata_demo.mrg")
    t2c_path = Path("mrg-t2c/metadata_demo.t2c")
    metadata_path = Path("mrg-t2c/metadata_demo.json")
    
    # Ensure directory exists
    mrg_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 2. Create the .mrg file (one tree per line)
        print("\nStep 1: Writing Penn Treebank trees to .mrg file...")
        with mrg_path.open("w", encoding="utf-8") as f:
            for item in corpus_data:
                f.write(item["tree"] + "\n")
        print(f"-> Saved: {mrg_path}")
        
        # 3. Create the external metadata file mapping 0-based sentence indices to source articles
        print("\nStep 2: Writing sentence-index to metadata mapping file...")
        metadata_map = {}
        for idx, item in enumerate(corpus_data):
            metadata_map[idx] = item["metadata"]
            
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(metadata_map, f, indent=4)
        print(f"-> Saved: {metadata_path}")
        
        # 4. Compile the corpus
        print("\nStep 3: Compiling .mrg file to binary .t2c index...")
        orchestrator = TgrepOrchestrator()
        orchestrator.index_corpus(mrg_path, t2c_path)
        print(f"-> Saved index: {t2c_path}")
        
        # 5. Perform a search query
        # Let's search for any noun phrase (NP) immediately dominating a new adjective (JJ)
        # Pattern: NP < JJ
        pattern = "NP < JJ"
        print(f"\nStep 4: Performing pattern search for '{pattern}'...")
        results = orchestrator.search_phrase("NP", t2c_path, contains=["JJ"], immediate=True)
        print(f"-> Found {len(results)} matches.")
        
        # 6. Load metadata and map the matches back to their original source articles
        print("\nStep 5: Loading metadata mapping and reporting search results...")
        with metadata_path.open("r", encoding="utf-8") as f:
            # json keys are always parsed as strings, so we convert them to int
            loaded_metadata = {int(k): v for k, v in json.load(f).items()}
            
        for i, match in enumerate(results):
            sent_idx = match["sentence_index"]
            source_meta = loaded_metadata.get(sent_idx, {})
            
            print(f"\nMatch #{i+1}:")
            print(f"  Sentence Index: {sent_idx}")
            print(f"  Subtree:        {match['subtree']}")
            print(f"  Sentence Text:  {match['sentence']}")
            print(f"  Source Article: {source_meta.get('title')} (Article ID: {source_meta.get('article_id')})")
            print(f"  Publisher:      {source_meta.get('source')} (Date: {source_meta.get('date')})")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
