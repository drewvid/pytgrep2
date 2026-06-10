# TGrep2 Patterns & Syntax: A Detailed Tutorial

This tutorial provides a comprehensive guide to the query patterns supported by TGrep2, using the test sentences and structure definitions from `check_manual_patterns.py` as concrete examples.

TGrep2 is essentially **"grep for syntax trees."** It allows you to query nested, hierarchical constituency trees (such as those in the Penn Treebank format) using a compact, declarative relationship language.

---

## 1. The Test Corpus Context

To understand the patterns, we use the following parsed sentences as our query corpus:
1. `John loves Mary.` 
   * `(S (NP (NNP John)) (VP (VBZ loves) (NP (NNP Mary))) (. .))`
2. `The smart dog barked at the big yellow cat.`
   * `(S (NP (DT The) (JJ smart) (NN dog)) (VP (VBD barked) (PP (IN at) (NP (DT the) (JJ big) (JJ yellow) (NN cat)))) (. .))`
3. `He runs fast.`
   * `(S (NP (PRP He)) (VP (VBZ runs) (ADVP (RB fast))) (. .))`
4. `She reads books quietly.`
   * `(S (NP (PRP She)) (VP (VBZ reads) (NP (NNS books)) (ADVP (RB quietly))) (. .))`
5. `The children laughed.`
   * `(S (NP (DT The) (NNS children)) (VP (VBD laughed)) (. .))`
6. `The dog saw the dog.`
   * `(S (NP (DT The) (NN dog)) (VP (VBD saw) (NP (DT the) (NN dog))) (. .))`
7. `John loves Mary in the garden.`
   * `(S (NP (NNP John)) (VP (VBZ loves) (NP (NNP Mary)) (PP (IN in) (NP (DT the) (NN garden)))) (. .))`

---

## 2. Basic Structural Operators

Basic operators describe the vertical (parent/child) and horizontal (order/precedence) relationships between nodes.

### Domination (Parent & Child)
* **Parent (`A < B`)**: Matches if node `A` is the immediate parent of node `B`.
  * *Example*: `NP < NNP`
  * *Meaning*: A Noun Phrase immediately dominating a Proper Noun.
  * *Matches*: The subject and object `NP`s of John and Mary in Sentences 1 and 7 (e.g., `(NP (NNP John))`).
* **Child (`A > B`)**: Matches if node `A` is a child of node `B`. (This is the mirror of `<`).
  * *Example*: `NNP > NP`
  * *Meaning*: A Proper Noun that is a child of a Noun Phrase.
  * *Matches*: The `NNP` leaf nodes corresponding to John and Mary.

### Ancestor & Descendant
* **Ancestor (`A << B`)**: Matches if node `A` dominates node `B` at any depth (parent, grandparent, etc.).
  * *Example*: `NP << PRP`
  * *Meaning*: A Noun Phrase dominating a Pronoun at any depth.
  * *Matches*: The subject `NP`s dominating `PRP` (e.g., `(NP (PRP He))` in S3 and `(NP (PRP She))` in S4).
* **Descendant (`A >> B`)**: Matches if node `A` is dominated by node `B` at any depth. (This is the mirror of `<<`).
  * *Example*: `PRP >> NP`
  * *Meaning*: A Pronoun that is dominated by a Noun Phrase.
  * *Matches*: The `PRP` leaf nodes (`He`, `She`).

### Precedence (Linear Word Order)
Precedence is defined over **disjoint subtrees** (i.e. neither node dominates the other) based on the linear ordering of their terminal leaf words.
* **Immediately Precedes (`A . B`)**: Matches if the last terminal word of `A` is directly followed by the first terminal word of `B`.
  * *Example*: `DT . JJ`
  * *Meaning*: A Determiner immediately preceding an Adjective.
  * *Matches*: `DT` "The" immediately preceding `JJ` "smart" in S2, and `DT` "the" preceding `JJ` "big" in S2.
* **Immediately Follows (`A , B`)**: Matches if `A` immediately follows `B`. (This is the mirror of `.`).
  * *Example*: `JJ , DT`
  * *Meaning*: An Adjective immediately following a Determiner.
  * *Matches*: `JJ` "smart" and `JJ` "big" in S2.
* **Precedes at Distance (`A .. B`)**: Matches if `A` precedes `B` at any distance in linear order.
  * *Example*: `NP .. VP`
  * *Meaning*: A Noun Phrase preceding a Verb Phrase.
  * *Matches*: The subject `NP` of each sentence preceding its respective `VP` (matches 7 times).
* **Follows at Distance (`A ,, B`)**: Matches if `A` follows `B` at any distance in linear order.
  * *Example*: `VP ,, NP`
  * *Meaning*: A Verb Phrase following a Noun Phrase.
  * *Matches*: Mirror of the above `NP .. VP` (matches 7 times).

---

## 3. Sister Operators

Sister operators describe relationships between sibling nodes—nodes that share the same immediate parent.

* **Sister (`A $ B`)**: Matches if `A` and `B` share the same parent and `A != B`.
  * *Example*: `NP $ VP`
  * *Meaning*: Noun Phrase sister to a Verb Phrase.
  * *Matches*: All subject `NP`s and `VP`s under their parent `S` node.
* **Sister Immediate Precedence (`A $. B`)**: Matches if `A` is a sister of `B` and immediately precedes it.
  * *Example*: `NP $. VP`
  * *Meaning*: Subject NP immediately preceding its sister VP.
  * *Matches*: All main sentence subject-verb boundaries (7 matches).
* **Sister Immediate Follows (`A $, B`)**: Mirror of `$.`. Matches if `A` is a sister of and immediately follows `B`.
  * *Example*: `VP $, NP`
  * *Matches*: The main `VP`s immediately following their sister subject `NP`s.
* **Sister Precedence at Distance (`A $.. B`)**: Matches if `A` is a sister of `B` and precedes it at any distance.
  * *Example*: `NP $.. VP`
  * *Matches*: Subject NPs preceding sister VPs.
* **Sister Follows at Distance (`A $,, B`)**: Mirror of `$..`. Matches if `A` is a sister of and follows `B` at any distance.
  * *Example*: `VP $,, NP`
  * *Matches*: VPs following their sister NPs.

---

## 4. Advanced Child and Descendant Positional Operators

These operators check the exact position of a child or descendant.

### Boundary Children
* **First Child (`A <, B` or `A <1 B`)**: Matches if `B` is the first child of `A`.
  * *Example*: `NP <, DT`
  * *Meaning*: Noun Phrase whose first child is a Determiner.
  * *Matches*: `(NP (DT The) ...)` in S2, S5, S6, and S7.
* **Is First Child (`A >, B` or `A >1 B`)**: Matches if `A` is the first child of `B`.
  * *Example*: `DT >, NP`
  * *Matches*: Determiners that are the first child of an NP.
* **Last Child (`A <- B` or `A <` B`)**: Matches if `B` is the last child of `A`. 
  > [!NOTE]
  > In standard ASCII, the backtick `` ` `` is used as a synonym for last-child.
  * *Example*: `NP <- NN` or `` NP <` NN ``
  * *Meaning*: Noun Phrase whose last child is a singular noun.
  * *Matches*: `(NP (DT The) (JJ smart) (NN dog))` where `NN` is the last child of the NP.
* **Is Last Child (`A >- B` or `A >` B`)**: Matches if `A` is the last child of `B`.
  * *Example*: `NN >- NP` or `` NN >` NP ``
  * *Matches*: Singular nouns that close their parent Noun Phrase.

### Positional Index Children
* **Nth Child (`A <N B`)**: Matches if `B` is the Nth child of `A` (1-indexed).
  * *Example*: `NP <3 JJ`
  * *Meaning*: Noun Phrase whose third child is an Adjective.
  * *Matches*: S2's object NP `(NP (DT the) (JJ big) (JJ yellow) (NN cat))` where "yellow" is the 3rd child of the NP.
* **Nth-to-last Child (`A <-N B`)**: Matches if `B` is the Nth-to-last child of `A` (`<-1` is the last child, `<-2` is the second-to-last, etc.).
  * *Example*: `NP <-2 JJ`
  * *Meaning*: Noun Phrase whose second-to-last child is an Adjective.
  * *Matches*: S2's subject NP `(NP (DT The) (JJ smart) (NN dog))` ("smart" is second-to-last child) and S2's object NP (where "yellow" is second-to-last child).

### Only Child
* **Only Child (`A <: B`)**: Matches if `B` is the only child of `A`.
  * *Example*: `NP <: NNP`
  * *Meaning*: Noun Phrase containing exactly one child, which is a Proper Noun.
  * *Matches*: `(NP (NNP John))` and `(NP (NNP Mary))` in S1 and S7.
* **Is Only Child (`A >: B`)**: Matches if `A` is the only child of `B`.
  * *Example*: `NNP >: NP`
  * *Matches*: Proper Noun leaf nodes that have no siblings under their parent NP.

### Boundary Descendants
* **Left-most Descendant (`A <<, B`)**: Matches if `B` is the left-most descendant of `A` (i.e. obtained by following first-child links recursively).
  * *Example*: `NP <<, DT`
  * *Matches*: Noun Phrases whose recursive first descendant is a Determiner.
* **Right-most Descendant (`A <<` B`)**: Matches if `B` is the right-most descendant of `A` (recursively following last-child links).
  * *Example*: `` NP <<` NN ``
  * *Matches*: Noun Phrases terminating in a noun.
* **Single Path of Descent (`A <<: B`)**: Matches if there is a unique, unbranched path of descent from `A` to `B` (i.e., every node in the path between them has exactly one child).
  * *Example*: `NP <<: NNP`
  * *Matches*: Single-proper-noun NPs (`NP` -> `NNP`).

---

## 5. Boolean Logic & Modifiers

TGrep2 allows complex logical expressions for matching node relationships.

* **Negation (`!`)**: Negates a relationship.
  * *Example*: `NP !< VP`
  * *Meaning*: Noun Phrase that does *not* immediately dominate a Verb Phrase.
  * *Matches*: All NPs in our corpus (since none immediately dominate a VP).
* **Identity / Equal (`=`)**: Matches if the link targets the node itself. Useful for reflexivity or optional self-matches.
  * *Example*: `NP <<= PRP`
  * *Meaning*: NP that dominates a PRP or is equal to PRP itself.
* **Logical OR (`|`)**: Disjunction of relationships.
  * *Example*: `VP < VBZ | < VBD`
  * *Meaning*: Verb Phrase immediately dominating a `VBZ` OR a `VBD` verb tag.
  * *Matches*: Present verbs in S1, S3, S4, S7 and past verbs in S2, S5, S6.
* **Logical AND (`&` or space)**: Conjunction of relationships. Chaining relationships with spaces implicitly acts as an AND. An explicit `&` can also be used.
  * *Example (implicit)*: `NP < DT < NN`
  * *Meaning*: NP dominating both a DT and an NN.
  * *Example (explicit)*: `VP < VBZ & < NP`
  * *Meaning*: VP dominating both a VBZ AND a sister NP.
* **Optional Links (`?`)**: Allows a relationship to fail to match without failing the overall query. (Useful when marking nodes for printing).
  * *Example*: `NP ?< JJ`
  * *Meaning*: Matches any NP, but if it has a JJ child, that child is bound.
* **Grouping (`[]`)**: Square brackets group relationships to control boolean precedence. (AND binds tighter than OR).
  * *Example*: `NP [< JJ | . JJ] [< NN | . NN]`
  * *Meaning*: NP that (dominates or precedes JJ) AND (dominates or precedes NN).

---

## 6. Node Name Matching (Regex, Wildcards, Negation)

These patterns match the text labels of the nodes themselves.

* **Wildcard (`*`)**: Matches any node label in the tree.
  * *Example*: `*`
* **Regular Expressions (`/.../`)**: Matches node labels using standard regex syntax.
  * *Example*: `/^NN/`
  * *Meaning*: Matches any tag starting with NN (matches `NN`, `NNS`, and `NNP` leaf tags).
* **Negated Name (`!LABEL`)**: Matches any node label except the specified one.
  * *Example*: `!DT`
  * *Meaning*: Any node that is not a Determiner.
* **ORed Names (`A|B`)**: Disjunction of names.
  * *Example*: `Mary|/^[Jj]ohn/`
  * *Meaning*: Node name is exactly "Mary" or matches regex `/^[Jj]ohn/`.

---

## 7. Labeled Nodes & Back Links

Labeled nodes allow you to build graph-like queries that contain cycles (such as referencing the same node multiple times).

* **Node Labeling (`Name=label`)**: Assigns a label to a matched node.
* **Identity Back-Link (`=label`)**: Refers back to the node bound to that label.
  * *Example*: `S=foo << (NP .. (VP >> =foo))`
  * *Meaning*: Find a sentence `S` (bind to `foo`) that dominates an `NP` and a `VP`, where the `VP` is dominated by that *same* sentence `foo` (not some other nested clause).
* **Similarity Back-Link (`~label`)**: Refers back to a node that has the same text/word-form name as the bound label (even if they are different nodes).
  * *Example*: `*=a >> /^NN/ .. (*=b >> /^NN/ ~ =a)`
  * *Meaning*: Find a noun node (bound to `a`) and a subsequent noun node (bound to `b`) that share the same word text (`~ =a`).
  * *Matches*: S6 `"The dog saw the dog."` where the first "dog" matches `a` and the second "dog" matches `b` because they have the same name.

---

## 8. Segmented Queries and Multiple Patterns

These features facilitate query writing and running multiple rules at once.

* **Segmented Queries (`:`)**: Splits a query into segments. Each segment after the first must start with a reference to a label defined in a previous segment. This eliminates complex nested parentheses.
  * *Example*: `S << (VP=v < NP) : =v < PP`
  * *Equivalent to*: `S << (VP=v < NP < PP)`
  * *Meaning*: S dominates VP `v` which dominates an NP, and `v` also dominates a PP.
* **Multiple Patterns (`;`)**: Separates independent queries in a single string. TGrep2 executes all of them in a single sweep.
  * *Example*: `NP < JJ; NP < DT`
* **Macros (`@name value;`)**: Declares a macro. Macros are expanded as simple text substitution prior to parsing. 
  * *Example*:
    ```text
    @ NP /^NP/; 
    @ NN /^NN/; 
    @NP < @NN
    ```
  * *Meaning*: Defines `NP` to expand to `/^NP/`, `NN` to `/^NN/`, and performs the search `@NP < @NN` (Noun Phrase dominating a Noun). Note that macro definitions require a space after the `@`, while macro references must have no space.
