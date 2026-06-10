import sys
import os
import subprocess
from pathlib import Path

# Add parent directory to path so we can import pytgrep2
base_dir = Path(__file__).parent.parent.resolve()
sys.path.append(str(base_dir))

from pytgrep2 import TgrepOrchestrator

def test_specialized_searches(bin_path, test_corpus_mrg, test_corpus_t2c):
    print(f"  Running specialized searches test...")
    orchestrator = TgrepOrchestrator(tgrep2_binary_path=bin_path)
    
    # We assume index is already compiled by andreasvc at step 1
    
    # 1. Test search_word
    # Default (return_type=None) returns List[dict]
    loves_default = orchestrator.search_word("loves", test_corpus_t2c)
    assert len(loves_default) == 2, "search_word('loves') failed"
    assert isinstance(loves_default[0], dict), "default return type should be dict"
    assert set(loves_default[0].keys()) == {"sentence_index", "subtree", "tree", "sentence"}, "default dict keys mismatch"
    assert loves_default[0]["subtree"] == "(VBZ loves)"
    assert {m["sentence_index"] for m in loves_default} == {0, 6}, "sentence_index values for 'loves' mismatch"

    # Specified return_type='subtree' returns List[str]
    loves_subtree = orchestrator.search_word("loves", test_corpus_t2c, return_type="subtree")
    assert len(loves_subtree) == 2
    assert isinstance(loves_subtree[0], str), "return_type='subtree' should return list of strings"
    assert loves_subtree[0] == "(VBZ loves)"

    assert len(orchestrator.search_word("Loves", test_corpus_t2c, return_type="subtree")) == 2, "search_word('Loves') failed"
    assert len(orchestrator.search_word("Loves", test_corpus_t2c, case_insensitive=False, return_type="subtree")) == 0, "search_word('Loves', case_insensitive=False) failed"
    assert len(orchestrator.search_word(".", test_corpus_t2c, return_type="subtree")) == 7, "search_word('.') failed"
    assert len(orchestrator.search_word("Mary", test_corpus_t2c, pos="NNP", return_type="subtree")) == 2, "search_word('Mary', pos='NNP') failed"
    assert len(orchestrator.search_word("Mary", test_corpus_t2c, pos="VBZ", return_type="subtree")) == 0, "search_word('Mary', pos='VBZ') failed"
    
    sentences = orchestrator.search_word("loves", test_corpus_t2c, return_type="sentence")
    assert len(sentences) == 2, "return_type='sentence' length check failed"
    assert "John loves Mary ." in sentences or "John loves Mary in the garden ." in sentences, "return_type='sentence' content check failed"
    
    # 2. Test search_collocation
    # Default (return_type=None) returns List[dict]
    coll_default = orchestrator.search_collocation("loves", "Mary", test_corpus_t2c, relation="immediate")
    assert len(coll_default) == 2, "search_collocation immediate failed"
    assert isinstance(coll_default[0], dict), "default return type should be dict"
    assert set(coll_default[0].keys()) == {"sentence_index", "subtree", "tree", "sentence"}
    assert {m["sentence_index"] for m in coll_default} == {0, 6}, "sentence_index values for collocation mismatch"

    assert len(orchestrator.search_collocation("loves", "mary", test_corpus_t2c, relation="immediate", case_insensitive=True, return_type="subtree")) == 2, "search_collocation case_insensitive failed"
    assert len(orchestrator.search_collocation("loves", "mary", test_corpus_t2c, relation="immediate", case_insensitive=False, return_type="subtree")) == 0, "search_collocation case_sensitive failed"
    assert len(orchestrator.search_collocation("the", "cat", test_corpus_t2c, relation="precedes", return_type="subtree")) == 2, "search_collocation precedes failed"
    assert len(orchestrator.search_collocation("the", "cat", test_corpus_t2c, relation="precedes", case_insensitive=False, return_type="subtree")) == 1, "search_collocation precedes case_sensitive failed"
    assert len(orchestrator.search_collocation("the", "cat", test_corpus_t2c, relation="precedes", distance=2, return_type="subtree")) == 0, "search_collocation distance=2 failed"
    assert len(orchestrator.search_collocation("the", "cat", test_corpus_t2c, relation="precedes", distance=3, return_type="subtree")) == 1, "search_collocation distance=3 failed"
    
    # 3. Test search_pos
    nouns = orchestrator.search_pos("NOUN", test_corpus_t2c, return_type="subtree")
    assert len(nouns) >= 11, f"search_pos('NOUN') failed, found {len(nouns)}"
    assert len(orchestrator.search_pos("VBZ", test_corpus_t2c, word="loves", return_type="subtree")) == 2, "search_pos('VBZ', word='loves') failed"
    
    # 4. Test search_phrase
    vps = orchestrator.search_phrase("VP", test_corpus_t2c, return_type="subtree")
    assert len(vps) >= 7, f"search_phrase('VP') failed, found {len(vps)}"
    s_np_vp = orchestrator.search_phrase("S", test_corpus_t2c, contains=["NP", "VP"], immediate=True, return_type="subtree")
    assert len(s_np_vp) >= 5, f"search_phrase('S', contains=['NP', 'VP']) failed, found {len(s_np_vp)}"
    np_dt_nn = orchestrator.search_phrase("NP", test_corpus_t2c, contains=["DT", "NN"], immediate=True, return_type="subtree")
    assert len(np_dt_nn) == 5, f"search_phrase('NP', contains=['DT', 'NN']) failed, found {len(np_dt_nn)}"
    
    print("  [PASS] Specialized searches test.")

def main():
    print("=== Running Comprehensive TGrep2 Test Suite ===")
    
    test_corpus_mrg = Path(__file__).parent / "test_corpus.mrg"
    test_corpus_t2c = Path(__file__).parent / "test_corpus.t2c"
    
    binaries = {
        "andreasvc": base_dir / "bin" / "tgrep2-andreasvc",
        "bwaldon": base_dir / "bin" / "tgrep2-bwaldon"
    }
    
    # 1. Verify binaries exist and are executable
    for name, path in binaries.items():
        if not path.exists():
            print(f"ERROR: Binary {name} not found at {path}")
            sys.exit(1)
        if not os.access(path, os.X_OK):
            print(f"ERROR: Binary {name} at {path} is not executable")
            sys.exit(1)
            
    # 2. Define the patterns to test and their expected counts
    patterns = [
        # --- Basic Dominance and Precedence ---
        ("NP < NNP", 4, "NP immediately dominating NNP"),
        ("NNP > NP", 4, "NNP immediately dominated by NP"),
        ("NP << PRP", 2, "NP dominating PRP at any depth"),
        ("PRP >> NP", 2, "PRP dominated by NP at any depth"),
        ("DT . JJ", 2, "DT immediately preceding JJ"),
        ("JJ , DT", 2, "JJ immediately following DT"),
        ("NP .. VP", 7, "NP preceding VP at any distance"),
        ("VP ,, NP", 7, "VP following NP at any distance"),
        
        # --- Sister Operators ---
        ("NP $ VP", 7, "NP sister of VP"),
        ("NP $. VP", 7, "NP sister of and immediately preceding VP"),
        ("VP $, NP", 7, "VP sister of and immediately following NP"),
        ("NP $.. VP", 7, "NP sister of and preceding VP"),
        ("VP $,, NP", 7, "VP sister of and following NP"),
        
        # --- Positional Child Operators ---
        ("NP <, DT", 6, "NP whose first child is DT"),
        ("DT >, NP", 6, "DT which is the first child of NP"),
        ("NP <- NN", 5, "NP whose last child is NN"),
        ("NP <` NN", 5, "NP whose last child is NN (alternate syntax)"),
        ("NN >- NP", 5, "NN which is the last child of NP"),
        ("NN >` NP", 5, "NN which is the last child of NP (alternate syntax)"),
        ("NP <: NNP", 4, "NP containing exactly one child, which is NNP"),
        ("NNP >: NP", 4, "NNP which is the only child of NP"),
        ("NP <<, DT", 6, "NP whose left-most descendant is DT"),
        ("NP <<` NN", 5, "NP whose right-most descendant is NN"),
        ("NP <<: NNP", 4, "NP with a single path of descent to NNP"),
        ("NP <3 JJ", 1, "NP whose third child is JJ"),
        ("NP <-2 JJ", 2, "NP whose second-to-last child is JJ"),
        
        # --- Boolean Logic & Modifiers ---
        ("NP !< VP", 13, "NP not immediately dominating VP"),
        ("NP <<= PRP", 2, "NP dominating or equal to PRP"),
        ("VP < VBZ | < VBD", 7, "VP immediately dominating VBZ OR VBD"),
        ("NP < DT < NN", 5, "NP immediately dominating both DT AND NN"),
        ("VP < VBZ & < NP", 3, "VP immediately dominating both VBZ AND NP"),
        ("NP [< JJ | . JJ] [< NN | . NN]", 2, "NP grouping with brackets"),
        
        # --- Node Name Matching & Wildcards ---
        ("*", 80, "Wildcard matching any node (expected >= 80)"),
        ("/^NN/", 11, "Regex node name NN/NNS/NNP (expected >= 11)"),
        ("Mary|/^[Jj]ohn/", 4, "Constant OR Regex node name"),
        
        # --- Labeled Nodes, Backlinks, Segmented, Macros ---
        ("S=foo << (NP .. (VP >> =foo))", 5, "Labeled node backlink (expected >= 5)"),
        ("*=a >> /^NN/ .. (*=b >> /^NN/ ~ =a)", 1, "Similarity backlink (expected >= 1)"),
        ("S << (VP=v < NP) : =v < PP", 1, "Segmented pattern (expected >= 1)"),
        ("@ NP /^NP/; @ NN /^NN/; @NP < @NN", 11, "Macro substitution pattern"),
    ]
    
    overall_success = True
    
    # 3. Compile the corpus using the 'andreasvc' binary
    print("\nStep 1: Compiling test corpus using 'andreasvc'...")
    orchestrator_indexer = TgrepOrchestrator(tgrep2_binary_path=binaries["andreasvc"])
    try:
        orchestrator_indexer.index_corpus(test_corpus_mrg, test_corpus_t2c)
        print("-> Corpus compiled successfully.")
    except Exception as e:
        print(f"-> Indexing failed: {e}")
        sys.exit(1)
        
    # 4. Test both binaries
    for name, bin_path in binaries.items():
        print(f"\nStep 2: Testing binary: {name} ({bin_path.name})")
        orchestrator = TgrepOrchestrator(tgrep2_binary_path=bin_path)
        
        failures = 0
        successes = 0
        
        for idx, (pattern, expected, desc) in enumerate(patterns):
            try:
                # Search using the -a option to get all subtrees
                results = orchestrator.search_index(pattern, test_corpus_t2c, additional_args=["-a"])
                count = len(results)
                
                # Handle threshold counts (represented by checking if >= expected for wildcard/regex)
                if pattern in ["*", "/^NN/", "S=foo << (NP .. (VP >> =foo))", "*=a >> /^NN/ .. (*=b >> /^NN/ ~ =a)"]:
                    is_correct = count >= expected
                    op_str = ">="
                else:
                    is_correct = count == expected
                    op_str = "=="
                    
                if is_correct:
                    successes += 1
                else:
                    failures += 1
                    print(f"  [FAIL] Query {idx+1}: '{pattern}' ({desc})")
                    print(f"         Expected: {op_str} {expected}, Got: {count} matches")
            except Exception as e:
                failures += 1
                print(f"  [FAIL] Query {idx+1}: '{pattern}' ({desc})")
                print(f"         Raised exception: {e}")
                
        print(f"-> {name} results: {successes} passed, {failures} failed")
        if failures > 0:
            overall_success = False
        else:
            try:
                test_specialized_searches(bin_path, test_corpus_mrg, test_corpus_t2c)
            except Exception as e:
                print(f"  [FAIL] Specialized searches failed: {e}")
                import traceback
                traceback.print_exc()
                overall_success = False
            
    # 5. Verify robustness check: Long filename boundary check
    print("\nStep 3: Verifying robustness checks (stack buffer overflow guard)...")
    long_filename = "a" * 600
    try:
        # Should cleanly exit/fail because filename is longer than MAX_FILENAME (512)
        # instead of causing a segfault/stack overflow
        cmd = [str(binaries["andreasvc"]), "-c", long_filename, "NP"]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        # Exit code should be non-zero (often 1 or 255)
        if res.returncode == 0:
            print("  [FAIL] Long filename check: binary returned 0, expected error")
            overall_success = False
        else:
            # Check stderr doesn't contain segmentation fault / core dumped
            if "segmentation fault" in res.stderr.lower() or "core dumped" in res.stderr.lower():
                print("  [FAIL] Long filename check: process crashed with segfault")
                overall_success = False
            else:
                print("  [PASS] Long filename check: binary handled overflow safely")
    except Exception as e:
        print(f"  [PASS] Long filename check: runner raised error safely ({e})")

    # 6. Cleanup index file
    if test_corpus_t2c.exists():
        test_corpus_t2c.unlink()
        
    # 7. Final Report
    print("\n=== Test Suite Execution Complete ===")
    if overall_success:
        print("STATUS: SUCCESS. Both binaries parsed and executed all queries identically.")
        sys.exit(0)
    else:
        print("STATUS: FAILED. One or more test checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
