import sys
from pathlib import Path

# Add repository root to path to enable local import of pytgrep2
base_dir = Path(__file__).parent.parent.resolve()
sys.path.append(str(base_dir))

from pytgrep2 import TgrepOrchestrator

def print_results_demo(label, results):
    print(f"  * {label}: found {len(results)} matches")
    for idx, match in enumerate(results[:2]):
        print(f"    Match {idx + 1}:")
        print(f"      Sentence Index: {match['sentence_index']}")
        print(f"      Subtree:        {match['subtree']}")
        print(f"      Tree:           {match['tree']}")
        print(f"      Sentence:       {match['sentence']}")

def main():
    print("=== TGREP2 Specialized Structural Search Example ===")
    
    # 1. Initialize the orchestrator
    # It automatically resolves and uses the compiled tgrep2-andreasvc binary
    orchestrator = TgrepOrchestrator()
    print(f"Using binary: {orchestrator.tgrep2_binary_path}\n")
    
    # 2. Define Penn Treebank structures for our demo corpus
    trees = [
        "(ROOT (S (NP (DT The) (JJ quick) (JJ brown) (NN fox)) (VP (VBZ jumps) (PP (IN over) (NP (DT the) (JJ lazy) (NN dog)))) (. .)))",
        "(ROOT (S (NP (NNP John)) (VP (VBZ loves) (NP (NNP Mary)) (, ,) (CC but) (S (NP (NNP Mary)) (VP (VBZ loves) (NP (NNP Bill))))) (. .)))",
        "(ROOT (S (NP (DT A) (JJ smart) (NN dog)) (VP (VBD barked) (PP (IN at) (NP (DT the) (JJ big) (JJ yellow) (NN cat)))) (. .)))",
        "(ROOT (S (NP (PRP She)) (VP (VBZ reads) (NP (NNS books)) (ADVP (RB quietly)) (PP (IN in) (NP (DT the) (NN library)))) (. .)))"
    ]
    
    mrg_path = Path("mrg-t2c/search_demo_corpus.mrg")
    t2c_path = Path("mrg-t2c/search_demo_corpus.t2c")
    
    try:
        # Create directory and write the PTB trees directly
        print("Step 1: Creating Penn Treebank corpus (.mrg)...")
        mrg_path.parent.mkdir(parents=True, exist_ok=True)
        with mrg_path.open("w", encoding="utf-8") as f:
            for tree in trees:
                f.write(tree + "\n")
        
        print("Step 2: Compiling .mrg file to binary .t2c index...")
        orchestrator.index_corpus(mrg_path, t2c_path)
        print("-> Corpus compiled successfully.\n")
        
        # ----------------------------------------------------
        # 1. Demonstration of search_word
        # ----------------------------------------------------
        print("=== 1. search_word() Options ===")
        
        # Default: Case-insensitive, returns list of dicts (subtree, tree, sentence)
        res_default = orchestrator.search_word("loves", t2c_path)
        print_results_demo("Word 'loves' (default, case-insensitive)", res_default)
        
        # Case-sensitive check
        res_case_sensitive = orchestrator.search_word("Loves", t2c_path, case_insensitive=False)
        print_results_demo("Word 'Loves' (case-sensitive)", res_case_sensitive)
        
        # Filtering by POS (Verb Third Person Singular Present)
        res_pos = orchestrator.search_word("loves", t2c_path, pos="VBZ")
        print_results_demo("Word 'loves' under POS 'VBZ'", res_pos)
        
        # Matching punctuation (handles escaping automatically)
        res_punct = orchestrator.search_word(".", t2c_path)
        print_results_demo("Punctuation '.'", res_punct)
        
        # Return raw sentences instead of parse subtrees (explicit return_type="sentence")
        res_sentences = orchestrator.search_word("Mary", t2c_path, return_type="sentence")
        print(f"  * Word 'Mary' returning raw sentence text (return_type='sentence'): {res_sentences}\n")
        
        # ----------------------------------------------------
        # 2. Demonstration of search_collocation
        # ----------------------------------------------------
        print("=== 2. search_collocation() Options ===")
        
        # Immediate adjacency ('loves' followed immediately by 'Mary')
        res_coll_imm = orchestrator.search_collocation("loves", "Mary", t2c_path, relation="immediate")
        print_results_demo("Collocation 'loves' + 'Mary' (immediate adjacency)", res_coll_imm)
        
        # Precedence at any distance ('the' preceding 'cat')
        res_coll_prec = orchestrator.search_collocation("the", "cat", t2c_path, relation="precedes")
        print_results_demo("Collocation 'the' ... 'cat' (precedence at any distance)", res_coll_prec)
        
        # Precedence with maximum word-span distance limit (distance=2)
        # "the big yellow cat" -> "the" to "cat" is 3 words span, so distance=2 should NOT match
        res_coll_dist2 = orchestrator.search_collocation("the", "cat", t2c_path, relation="precedes", distance=2)
        print_results_demo("Collocation 'the' ... 'cat' (max distance = 2 words)", res_coll_dist2)
        
        # Precedence with maximum word-span distance limit (distance=3) -> matches
        res_coll_dist3 = orchestrator.search_collocation("the", "cat", t2c_path, relation="precedes", distance=3)
        print_results_demo("Collocation 'the' ... 'cat' (max distance = 3 words)", res_coll_dist3)
        
        # Sister precedence relation
        res_coll_sister = orchestrator.search_collocation("loves", "Mary", t2c_path, relation="sister")
        print_results_demo("Collocation 'loves' and 'Mary' as sister nodes", res_coll_sister)
        print()
        
        # ----------------------------------------------------
        # 3. Demonstration of search_pos
        # ----------------------------------------------------
        print("=== 3. search_pos() Options ===")
        
        # Match all Verbs using NOUN/VERB/ADJ group aliases
        res_verbs = orchestrator.search_pos("VERB", t2c_path)
        print_results_demo("Match all verbs (VERB alias)", res_verbs)
        
        # Match specific word under POS tag
        res_pos_word = orchestrator.search_pos("NN", t2c_path, word="dog")
        print_results_demo("Match specific word 'dog' under POS tag 'NN'", res_pos_word)
        print()
        
        # ----------------------------------------------------
        # 4. Demonstration of search_phrase
        # ----------------------------------------------------
        print("=== 4. search_phrase() Options ===")
        
        # Match all Verb Phrases
        res_vp = orchestrator.search_phrase("VP", t2c_path)
        print_results_demo("Match all verb phrases (VP)", res_vp)
        
        # Match S dominating NP and VP immediately
        res_s_immediate = orchestrator.search_phrase("S", t2c_path, contains=["NP", "VP"], immediate=True)
        print_results_demo("S dominating both NP and VP immediately (immediate=True)", res_s_immediate)
        
        # Match VP containing NP at any depth
        res_vp_deep = orchestrator.search_phrase("VP", t2c_path, contains=["NP"], immediate=False)
        print_results_demo("VP dominating NP at any depth (immediate=False)", res_vp_deep)
        
    except Exception as e:
        print(f"\nAn error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
