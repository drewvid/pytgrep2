import sys
from pathlib import Path
from pytgrep2 import TgrepOrchestrator

def main():
    print("=== TGREP2 Manual Patterns Verification ===")
    
    # 1. Curated sentences designed to trigger specific syntax relationships
    sentences = [
        "John loves Mary.",                           # NNP, VBZ
        "The smart dog barked at the big yellow cat.", # DT, JJ, NN, PP
        "He runs fast.",                              # PRP, VBZ, RB
        "She reads books quietly.",                   # PRP, VBZ, NNS, RB
        "The children laughed.",                      # DT, NNS, VBD
        "The dog saw the dog.",                       # Duplicate words for name matching back links
        "John loves Mary in the garden."              # Deep trees, PP, S dominating VP dominating PP
    ]
    
    # 2. Comprehensive pattern test suite based on the TGrep2 manual
    patterns_to_test = [
        # --- 1. Basic Operators (Dominance & Precedence) ---
        {
            "pattern": "NP < NNP",
            "desc": "Noun Phrase (NP) immediately dominating a Proper Noun (NNP)",
            "expected_min": 4
        },
        {
            "pattern": "NNP > NP",
            "desc": "Proper Noun (NNP) that is a child of a Noun Phrase (NP)",
            "expected_min": 4
        },
        {
            "pattern": "NP << PRP",
            "desc": "Noun Phrase (NP) dominating a Pronoun (PRP) at any depth",
            "expected_min": 2
        },
        {
            "pattern": "PRP >> NP",
            "desc": "Pronoun (PRP) dominated by a Noun Phrase (NP) at any depth",
            "expected_min": 2
        },
        {
            "pattern": "DT . JJ",
            "desc": "Determiner (DT) immediately preceding an Adjective (JJ)",
            "expected_min": 2
        },
        {
            "pattern": "JJ , DT",
            "desc": "Adjective (JJ) immediately following a Determiner (DT)",
            "expected_min": 2
        },
        {
            "pattern": "NP .. VP",
            "desc": "Noun Phrase (NP) preceding a Verb Phrase (VP) at any distance",
            "expected_min": 7
        },
        {
            "pattern": "VP ,, NP",
            "desc": "Verb Phrase (VP) following a Noun Phrase (NP) at any distance",
            "expected_min": 7
        },
        
        # --- 2. Sister Operators ---
        {
            "pattern": "NP $ VP",
            "desc": "Noun Phrase (NP) that is a sister of a Verb Phrase (VP)",
            "expected_min": 7
        },
        {
            "pattern": "NP $. VP",
            "desc": "Noun Phrase (NP) sister of and immediately preceding a Verb Phrase (VP)",
            "expected_min": 7
        },
        {
            "pattern": "VP $, NP",
            "desc": "Verb Phrase (VP) sister of and immediately following a Noun Phrase (NP)",
            "expected_min": 7
        },
        {
            "pattern": "NP $.. VP",
            "desc": "Noun Phrase (NP) sister of and preceding a Verb Phrase (VP) at any distance",
            "expected_min": 7
        },
        {
            "pattern": "VP $,, NP",
            "desc": "Verb Phrase (VP) sister of and following a Noun Phrase (NP) at any distance",
            "expected_min": 7
        },

        # --- 3. Positional Child/Descendant Operators ---
        {
            "pattern": "NP <, DT",
            "desc": "Noun Phrase (NP) whose first child is a Determiner (DT)",
            "expected_min": 6
        },
        {
            "pattern": "DT >, NP",
            "desc": "Determiner (DT) which is the first child of Noun Phrase (NP)",
            "expected_min": 6
        },
        {
            "pattern": "NP <- NN",
            "desc": "Noun Phrase (NP) whose last child is a Noun (NN)",
            "expected_min": 5
        },
        {
            "pattern": "NP <` NN",
            "desc": "Noun Phrase (NP) whose last child is a Noun (NN) (synonymous operator)",
            "expected_min": 5
        },
        {
            "pattern": "NN >- NP",
            "desc": "Noun (NN) which is the last child of Noun Phrase (NP)",
            "expected_min": 5
        },
        {
            "pattern": "NN >` NP",
            "desc": "Noun (NN) which is the last child of Noun Phrase (NP) (synonymous operator)",
            "expected_min": 5
        },
        {
            "pattern": "NP <: NNP",
            "desc": "Noun Phrase (NP) containing exactly one child, which is a Proper Noun (NNP)",
            "expected_min": 4
        },
        {
            "pattern": "NNP >: NP",
            "desc": "Proper Noun (NNP) that is the only child of Noun Phrase (NP)",
            "expected_min": 4
        },
        {
            "pattern": "NP <<, DT",
            "desc": "Noun Phrase (NP) whose left-most descendant is a Determiner (DT)",
            "expected_min": 6
        },
        {
            "pattern": "NP <<` NN",
            "desc": "Noun Phrase (NP) whose right-most descendant is a Noun (NN)",
            "expected_min": 5
        },
        {
            "pattern": "NP <<: NNP",
            "desc": "Noun Phrase (NP) where there is a single path of descent to a Proper Noun (NNP)",
            "expected_min": 4
        },
        {
            "pattern": "NP <3 JJ",
            "desc": "Noun Phrase (NP) whose third child is an Adjective (JJ)",
            "expected_min": 1
        },
        {
            "pattern": "NP <-2 JJ",
            "desc": "Noun Phrase (NP) whose second-to-last child is an Adjective (JJ)",
            "expected_min": 1
        },

        # --- 4. Boolean Logic & Modifiers ---
        {
            "pattern": "NP !< VP",
            "desc": "Noun Phrase (NP) that does NOT immediately dominate a Verb Phrase (VP)",
            "expected_min": 10
        },
        {
            "pattern": "NP <<= PRP",
            "desc": "Noun Phrase (NP) that dominates a Pronoun (PRP) or is equal to it",
            "expected_min": 2
        },
        {
            "pattern": "VP < VBZ | < VBD",
            "desc": "Verb Phrase (VP) dominating a VBZ OR VBD",
            "expected_min": 7
        },
        {
            "pattern": "NP < DT < NN",
            "desc": "Noun Phrase (NP) immediately dominating both a Determiner (DT) AND a Noun (NN)",
            "expected_min": 4
        },
        {
            "pattern": "VP < VBZ & < NP",
            "desc": "Verb Phrase (VP) immediately dominating both a VBZ AND a Noun Phrase (NP)",
            "expected_min": 3
        },
        {
            "pattern": "NP [< JJ | . JJ] [< NN | . NN]",
            "desc": "Noun Phrase (NP) grouping with square brackets: (dominates or precedes JJ) AND (dominates or precedes NN)",
            "expected_min": 2
        },

        # --- 5. Node Name Matching ---
        {
            "pattern": "*",
            "desc": "Wildcard pattern matching any node in the corpus",
            "expected_min": 50
        },
        {
            "pattern": "/^NN/",
            "desc": "Regular expression matching node names starting with NN (NN, NNS, NNP)",
            "expected_min": 10
        },
        {
            "pattern": "!DT",
            "desc": "Negated node name matching any node that is not a Determiner (DT)",
            "expected_min": 50
        },
        {
            "pattern": "Mary|/^[Jj]ohn/",
            "desc": "OR'd node name matching constant 'Mary' or regex '/^[Jj]ohn/'",
            "expected_min": 4
        },

        # --- 6. Labeled Nodes & Back Links ---
        {
            "pattern": "S=foo << (NP .. (VP >> =foo))",
            "desc": "Labeled node back-link: S dominates an NP and a VP, and VP is dominated by the same S",
            "expected_min": 5
        },
        {
            "pattern": "*=a >> /^NN/ .. (*=b >> /^NN/ ~ =a)",
            "desc": "Similarity back-link (~): Find a noun that shares the same name with a subsequent noun",
            "expected_min": 1
        },

        # --- 7. Segmented Patterns ---
        {
            "pattern": "S << (VP=v < NP) : =v < PP",
            "desc": "Segmented pattern using colons (:): S dominates VP=v which dominates NP, and v also dominates PP",
            "expected_min": 1
        },

        # --- 8. Multiple Patterns & Macros ---
        {
            "pattern": "NP < JJ; NP < DT",
            "desc": "Multiple patterns separated by semicolon (;)",
            "expected_min": 6
        },
        {
            "pattern": "@ NP /^NP/; @ NN /^NN/; @NP < @NN",
            "desc": "Pattern macro definition and reference using @",
            "expected_min": 4
        }
    ]
    
    mrg_path = Path("manual_test_corpus.mrg")
    t2c_path = Path("manual_test_corpus.t2c")
    base_dir = Path(__file__).parent.parent.resolve()
    
    binaries = {
        "andreasvc": base_dir / "bin" / "tgrep2-andreasvc",
        "bwaldon": base_dir / "bin" / "tgrep2-bwaldon"
    }
    
    try:
        # Step 1: Parse the sentences into PTB (.mrg) format
        print("Step 1: Parsing sentences to Penn Treebank format...")
        temp_orchestrator = TgrepOrchestrator()
        temp_orchestrator.parse_to_mrg(sentences, mrg_path)
        print(f"-> Created {mrg_path}\n")
        
        # Step 2: Compile the index using the robust andreasvc binary (works for both search engines)
        print("Step 2: Indexing corpus using andreasvc binary...")
        indexer = TgrepOrchestrator(tgrep2_binary_path=binaries["andreasvc"])
        indexer.index_corpus(mrg_path, t2c_path)
        print(f"-> Created {t2c_path}\n")
        
        # Test each binary for searching
        for bin_name, bin_path in binaries.items():
            print(f"=========================================")
            print(f"Testing search binary: {bin_name}")
            print(f"Path: {bin_path}")
            print(f"=========================================")
            
            orchestrator = TgrepOrchestrator(tgrep2_binary_path=bin_path)
            
            # Step 3: Run the patterns
            print(f"Step 3: Querying the corpus using patterns from the manual...")
            for entry in patterns_to_test:
                pattern = entry["pattern"]
                desc = entry["desc"]
                expected_min = entry["expected_min"]
                print(f"\nPattern: '{pattern}'\nDescription: {desc}")
                
                # Search using the -a option to find all matching subtrees
                matches = orchestrator.search_index(pattern, t2c_path, additional_args=["-a"])
                print(f"-> Found {len(matches)} match(es) (Expected >= {expected_min})")
                for idx, match in enumerate(matches[:5]): # Show up to first 5 matches to keep output clean
                    print(f"   [{idx + 1}] {match}")
                if len(matches) > 5:
                    print(f"   ... and {len(matches) - 5} more matches.")
                
                # Validation check
                if len(matches) < expected_min:
                    raise ValueError(
                        f"Validation failed for pattern '{pattern}' on binary '{bin_name}': "
                        f"found {len(matches)} matches, but expected at least {expected_min}."
                    )
            
            print(f"\nBinary {bin_name} verified successfully!\n")
            
        print("=== All TGREP2 binaries and patterns verified successfully! ===")
        
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Cleanup
        print("\nCleaning up temporary corpus files...")
        for p in [mrg_path, t2c_path]:
            if p.exists():
                p.unlink()
        print("Cleanup complete.")

if __name__ == "__main__":
    main()
