#!/usr/bin/env bash
set -euo pipefail

# Location of the corpus (Penn Treebank style .mrg)
MRG="${1:-corpus_benepar.mrg}"
T2C="${MRG%.mrg}.t2c"

# 1) Build (idempotent)
(cd ..; make clean; make -C "$(dirname "$0")" -j >/dev/null)

# 2) Preprocess once (if missing or stale)
if [[ ! -f "$T2C" || "$MRG" -nt "$T2C" ]]; then
  echo "# Preprocessing corpus: $MRG -> $T2C"
  ../tgrep2 -p "$MRG" "$T2C"
fi

# 3) Use compiled corpus
export TGREP2_CORPUS="$T2C"

run() {
  echo "# $*"
  if ! ../tgrep2 -i -w "$1"; then
    echo "ERROR running: $1" >&2
  fi
  echo
}

# ---------------- Queries ----------------

# D1_S1 (Why…)
run "( /^ID_.*/ << ( SBARQ << /^WH.*/ ) )"
run "( /^ID_.*/ << (  SQ   << /^WH.*/ ) )"   # may be empty in this corpus

# D1_S2 (Before…)
run "( /^ID_.*/ << ( S << (SBAR < (IN < /^(before|after|when|while|until|since)$/)) ) )"

# D1_S3 (Because…)
run "( /^ID_.*/ << ( S << (SBAR < (IN < /^(because|since|as)$/)) ) )"

# D1_S4 (First… then… next…)
run "( /^ID_.*/ << ( S << (ADVP < (RB < /^(first|then|next|finally)$/)) ) )"
run "( /^ID_.*/ << ( S << (ADVP < (JJ < /^(first|last|next)$/)) ) )"   # JJ under ADVP

# D1_S5 (might … so …)
run "( /^ID_.*/ << ( VP < (MD < /^(might|may|could|would|should)$/) ) )"
run "( /^ID_.*/ << ( S << ( (RB|CC) < /^so$/ ) ) )"

# D1_S6 (between …)
run "( /^ID_.*/ << ( S << (PP < (IN < /^(under|over|between|behind|above|below|inside|outside|near|far|in|on)$/)) ) )"

# D1_S7 (is … that …)
# Use dominance (<<) and support both WH-relative and explicit 'that' variants.
run "( /^ID_.*/ << ( S < (NP $.. (VP < (VBZ|VBP < /^(is|are)$/) << (SBAR < (WHNP|WHPP|WHADVP))) ) ) )"
run "( /^ID_.*/ << ( S < (NP $.. (VP < (VBZ|VBP < /^(is|are)$/) << (SBAR < (WHNP < (WDT < /^that$/))) ) ) ) )"
run "( /^ID_.*/ << ( S < (NP $.. (VP < (VBZ|VBP < /^(is|are)$/) << (SBAR < (IN < /^that$/)) ) ) ) )"
