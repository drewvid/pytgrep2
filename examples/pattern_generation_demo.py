import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from pytgrep2 import TgrepQueryGenerator

def main():
    # Retrieve API key from standard environment variables
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: Neither GEMINI_API_KEY nor GOOGLE_API_KEY environment variable is set.")
        print("Please configure one of these variables with your Google GenAI API key and run again.")
        sys.exit(1)

    cache_file = Path("demo_cache.pkl.gz")
    if cache_file.exists():
        cache_file.unlink()

    print("=" * 70)
    print("      pytgrep2 Google GenAI Syntactic Pattern Generation Demo")
    print("=" * 70)
    print(f"Initializing query generator. Cache file: {cache_file}...")
    
    generator = TgrepQueryGenerator(cache_path=cache_file, api_key=api_key)

    # Define queries with varying levels of complexity
    queries = [
        # --- Level 1: Simple ---
        {
            "level": "Simple",
            "desc": "A noun phrase dominating an adjective"
        },
        {
            "level": "Simple",
            "desc": "A determiner immediately preceding a singular noun"
        },
        
        # --- Level 2: Medium ---
        {
            "level": "Medium",
            "desc": "A prepositional phrase dominating a noun phrase whose last child is a plural noun"
        },
        {
            "level": "Medium",
            "desc": "A verb phrase dominating a modal auxiliary verb and immediately preceding another verb phrase"
        },
        
        # --- Level 3: Complex ---
        {
            "level": "Complex",
            "desc": "A noun phrase which is a sister of and immediately precedes a verb phrase, where the verb phrase dominates a past-tense verb and a direct object noun phrase"
        },
        {
            "level": "Complex",
            "desc": "Passive voice construction (a verb phrase dominating an auxiliary verb which immediately precedes a verb phrase dominating a past participle)"
        }
    ]

    # Run query generation
    for idx, q in enumerate(queries, 1):
        print(f"\n[{idx}] [{q['level']}] Generating pattern...")
        print(f"  NL Query: \"{q['desc']}\"")
        try:
            pattern = generator.generate_pattern(q["desc"])
            print(f"  Pattern : {pattern}")
        except Exception as e:
            print(f"  Error   : Failed to generate pattern: {e}")

    # Demonstrate cache capability
    print("\n" + "=" * 70)
    print("      Demonstrating Cache Performance (Subsequent Call)")
    print("=" * 70)
    
    test_desc = queries[0]["desc"]
    print(f"Requesting pattern for: \"{test_desc}\" again...")
    
    # Temporarily remove active GenAI client to prove it resolves strictly via the cache
    generator.client = None
    
    try:
        cached_pattern = generator.generate_pattern(test_desc)
        print(f"  Result (from Cache): {cached_pattern}")
        print("  Status             : Success (No API call was made)")
    except Exception as e:
        print(f"  Status             : Failed ({e})")

    # Clean up the demo cache
    if cache_file.exists():
        cache_file.unlink()
        print("\nCleaned up cache file.")

    print("\nDemo finished successfully!")

if __name__ == "__main__":
    # Ensure local modified package can be imported if running directly from repo root
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
    main()
