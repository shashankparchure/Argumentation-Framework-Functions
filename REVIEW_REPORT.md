# Review of the Assignment 3 Repository (Argumentation Framework Functions)

Reviewed against: *Argumentation Framework Functions.pdf* (assignment brief) and Chapter 5, "Argumentation among Agents" (Rahwan), of *Multiagent Systems* (Weiss, ed.).
Code reviewed: commit `36a9765` ("implemented experiments").

> **Status update.** Steps 1, 3, 4 and 5 of the action plan (§7) are now done. There are 39 tests in `tests/`. `experiments.py` gained `--no-self-attacks` and `--stress`, and writes the Q3 categories from `analysis.py`. A Streamlit demo is in `app.py`. The written assignment report (step 2) and the remaining hygiene items are still open. See `README.md` for the commands.

---

## 1. Verdict in one paragraph

The core code is **correct**. Every engine function and every strategic function the brief asks for exists, and all of them give the textbook answers on every example in Chapter 5 that I could test (Figures 5.1, 5.2, 5.3 and Examples 5.5–5.8, 5.10, 5.11). The experiment runs the required 3 × 1000 instances, and re-running it with seed 2026 gives byte-identical results. The submission is **not complete**, though, and the analysis is thinner than it looks:

1. There are **no tests**, even though the brief says "Test your functions on the examples given in the book".
2. There is **no report**. The brief requires Code, README, Report and Demonstration.
3. The experiment results are **dominated by self-attacks**. 69–96 % of instances contain a self-attacking argument, and that alone breaks Theorem 5.4's condition. Only **44 of 3000** instances satisfy the condition, so the answer to Q2 ("0 violations") rests on 44 data points.
4. Q3 is answered with a 2.8 MB JSON dump. No instance is explained.
5. The demo covers only the strategic half, uses its own JavaScript copy of the grounded semantics, and can only draw the two hard-coded textbook examples.

All of these can be fixed. Sections 4–7 give concrete numbers and a plan.

---

## 2. Requirement-by-requirement check

| # | Brief requirement | Where | Status |
|---|---|---|---|
| E1 | Class for framework ⟨A, ⇀⟩ | `ArgumentationFramework` | ✅ Correct, validated, immutable |
| E2 | Conflict-free test | `is_conflict_free` | ✅ S ∩ S⁺ = ∅ (Def 5.2) |
| E3 | α defended by S | `defends` | ✅ α⁻ ⊆ S⁺ (Def 5.2) |
| E4 | Characteristic function F(S) | `characteristic_function` | ✅ Def 5.3 |
| E5 | Admissible / complete test | `is_admissible`, `is_complete` | ✅ Defs 5.4, 5.5 |
| E6A | Grounded extension | `grounded_extension` | ✅ Iterates F from ∅ (least fixed point) |
| E6B | All complete extensions | `complete_extensions` | ✅ Exhaustive (fine for ≤ ~15 args) |
| E6C | Preferred, stable, semi-stable | `preferred_/stable_/semi_stable_extensions` | ✅ Def 5.7 |
| E6D | All legal labellings | `legal_labellings` | ✅ Def 5.6. Doesn't mark which labelling is grounded/preferred/stable (Table 5.1) |
| E6E | Acceptance status | `acceptance_status` | ✅ Def 5.8. Returns 3 booleans, not a single label. Raises when there are no stable extensions (should be documented) |
| E-test | Test on book examples | — | ❌ **Missing**. No test file. |
| S1 | Mechanism: grounded extension of the union of reports | `grounded_direct_argumentation_mechanism` | ✅ Def 5.21 |
| S2 | Enumerate own subsets, return utility-maximising reports | `best_responses` | ✅ |
| S3 | Theorem 5.3 check (truth is a best response against all of the others' subsets) | `check_theorem_5_3` | ✅ Exhaustive. Returns the first counterexample |
| S4 | Theorem 5.4 odd-path check, handling cycles | `check_theorem_5_4`, `find_odd_length_path` | ✅ BFS over (node, parity). Uses the *walk* reading (see §5.2). Returns only the first witness |
| X  | ≥1000 instances, 6–8 args, p ∈ {0.15, 0.25, 0.35}, 3 agents | `experiments.py` | ✅ 1000 per p, seeded, Wilson CIs |
| X1 | SP fraction per p | `experiment_summary.json` | ✅ |
| X2 | Condition true but not SP: note and explain | `interesting_cases.json` | ⚠️ 0 found, but only 44 instances satisfy the condition, so the test has little power |
| X3 | SP although the condition fails: note and explain why | `interesting_cases.json` | ⚠️ 956 instances dumped as raw JSON. No categorisation or explanation |
| M  | Book misprints (Ex 5.10 utilities, α6 not α5) | — | ⚠️ Not mentioned anywhere. The demo text does use α6 correctly |
| D  | Code, README, Report, Demonstration | — | ⚠️ README is Windows/PowerShell-only. **No report.** The demo is partial (§6) |

---

## 3. Correctness verification against the textbook

I ran the engine on every graph in Chapter 5 that has a stated answer. **All 29 checks pass.**

| Source | What was checked | Result |
|---|---|---|
| Fig 5.1 (α3→α2→α1←α4←α5) | {α3,α5} defends α1; Ex 5.5 admissible sets ∅, {α3}, {α5}, {α3,α5}, {α1,α3,α5}; Ex 5.6 {α3,α5} not complete, F({α3}) = F({α5}) = {α3,α5}; unique complete = grounded = preferred = stable = {α1,α3,α5}; exactly 1 labelling | ✅ |
| Fig 5.2 (α1⇄α2, α3 isolated) | Ex 5.7 complete = {α3}, {α1,α3}, {α2,α3}; grounded {α3}; Ex 5.8 preferred = stable = semi-stable = {α1,α3}, {α2,α3}; 3 labellings; α1 credulously but not skeptically accepted under preferred; α1 rejected under grounded | ✅ |
| Fig 5.3 (b→a, c→b, d→b, c⇄d, e→d) | grounded = {a, c, e} | ✅ |
| Ex 5.10 | truthful outcome {α1,α3}; utilities x=1, **y=0, z=1** (book swaps y/z); hiding α1 gives {α2,α4,α5}; x's unique best response is {α4,α5}; not SP; Thm 5.4 witness α1→α2→α3→α4 | ✅ |
| Ex 5.11 | truthful outcome {α1,α4,α5,α6}; SP; Thm 5.4 condition fails (α1→α2→α3→α4). The argument that cancels the self-defeat is **α6** (the book says α5) | ✅ |

The script used is in §8. It should become `tests/test_book_examples.py`.

---

## 4. Experiment results (reproduced exactly)

| p | Strategyproof | 95 % CI | Thm 5.4 condition holds | Condition holds, not SP (Q2) | Condition fails, SP (Q3) |
|---|---|---|---|---|---|
| 0.15 | 578 / 1000 (57.8 %) | 54.7–60.8 % | 39 (3.9 %) | 0 | 539 |
| 0.25 | 275 / 1000 (27.5 %) | 24.8–30.3 % | 5 (0.5 %) | 0 | 270 |
| 0.35 | 147 / 1000 (14.7 %) | 12.6–17.0 % | 0 (0.0 %) | 0 | 147 |
| **Total** | **1000 / 3000** | | **44** | **0** | **956** |

Running `python3 experiments.py --seed 2026 --output-dir /tmp/rerun` gives identical numbers in about 6 s.

---

## 5. Problems with the experimental analysis (most important section)

### 5.1 Self-attacks swamp the Theorem 5.4 statistics

The generator samples every ordered pair, **including (a, a)**, with probability p. Each argument is owned by some agent, and a self-attack is an odd path of length 1 from α to α (the agent's type is then not conflict-free). So **any self-attack anywhere makes Theorem 5.4's condition fail.**

| p | Instances with ≥ 1 self-attack |
|---|---|
| 0.15 | 689 / 1000 |
| 0.25 | 859 / 1000 |
| 0.35 | 955 / 1000 |

This is why the condition holds in only 3.9 % / 0.5 % / 0 % of instances. The headline "1.5 %" in the demo mostly measures *how often the generator draws a self-loop*. It says little about the theorem itself.

The brief's phrase "each possible attack" is ambiguous, so including self-attacks is defensible. However, it should be **stated and justified in the report**, and the experiment should be **re-run without self-attacks** as a second setting. With the same seeds and self-attacks removed:

| p | SP | Condition holds (walk reading) | Condition holds (simple-path reading) | Q2 violations |
|---|---|---|---|---|
| 0.15 | 641 | 138 | 139 | 0 |
| 0.25 | 320 | 33 | 34 | 0 |
| 0.35 | 114 | 4 | 5 | 0 |

### 5.2 "Odd-length path": walk or simple path?

The book defines α ↪ β as "an odd-length *path* from α to β". The code uses an odd **walk**, which may repeat vertices. It also counts α = β, meaning an odd cycle that returns to the agent's own argument. Both choices are defensible, and the BFS over (node, parity) is the clean way to "deal with cycles" as the brief asks. The choice should still be stated explicitly in the report.

I implemented the simple-path reading as well (`find_odd_simple_path`, a DFS that never revisits a vertex; for α = β it looks for an odd simple cycle):

- The walk and simple-path readings agree on **every** instance: all 3000 in both runs, and all 3000 stress-test instances.
- What *does* matter is whether pairs with α = β count. Dropping them changes the verdict on 3 instances without self-attacks. All three have an odd cycle through an agent's own argument (e.g. `p25_0187`: x owns a1, and a1→a6→a4→a1), and all three are strategyproof anyway. Counting α = β is the safer reading of "∄ α1, α2 ∈ Aᵢ with α1 ↪ α2".
- **No reading produces a single Q2 violation.**

### 5.3 Q2 has too little data. A stress test fixes this.

"0 of 44" is weak evidence for "no counterexample to sufficiency". I ran a targeted stress test that sampled instances (self-attacks removed) until **3000 condition-holding instances** were collected. This took 55,982 samples. `python experiments.py --stress 3000` now reproduces the test with seed 2026 (53,955 samples, also 0 failures).
**Result: 0 of 3000 are not strategyproof.** This is strong empirical support that Theorem 5.4's condition is sufficient, as the book claims. It should go into the report in place of the bare "0".

Intuition worth giving in the report: when no agent has an odd path between two of its own arguments, every route from one of its arguments to another has even length. An argument then only ever *supports* (indirectly defends) the agent's other arguments and never undermines them, so withholding it can remove support but cannot remove a hidden self-defeat.

### 5.4 Q3 needs an explanation, not a JSON dump

I classified all 956 "condition fails but strategyproof" instances by **why** the odd path does no harm. For each agent and each odd-path pair (α, β) of its own arguments, I checked:
- whether the victim β is self-attacking or can never be accepted under any report profile, and
- whether the path is a direct attack, a longer indirect path, or an odd cycle back to α itself.

| Category (instance-level) | p = 0.15 | 0.25 | 0.35 | Total |
|---|---|---|---|---|
| **A. Every victim is a self-attacking argument.** It can never be accepted, so nothing is lost by revealing the attacker. | 104 | 45 | 8 | **157** |
| **B. Only odd cycles back to the same argument** (α ↪ α through other agents' arguments) | 8 | 11 | 13 | **32** |
| **C. Only direct own-conflicts** (α ⇀ β, both owned). Hiding α frees β but α itself is lost: at best a one-for-one swap | 261 | 64 | 19 | **344** |
| **D. Live indirect odd path that is neutralised** (Ex 5.11 type). Another argument defends the victim, or breaking the chain costs exactly what it gains | 166 | 150 | 107 | **423** |

Representative instances to discuss in the report:

- **A, `p15_0019`.** y owns a1, a4, a5. a1 attacks itself and is also attacked by a4 and a5. The odd paths all end at a1, which is never accepted, so revealing a4/a5 cannot hurt.
- **C, `p15_0001`.** x owns a1, a2, a6 and a6 ⇀ a1. Truthful gives {a6} for x, hiding a6 gives {a1}: a 1-for-1 tie, so truth is still a best response.
- **D, `p15_0402`.** z owns a1, a7 with a1 → a2 → a4 → a7 (length 3). But x's a6 also attacks a4, so a6 shields a7 just as α6 does in Ex 5.11. Truthful gives z {a1, a5, a7} = 3. If x withholds a6, z gets 2 either by telling the truth or by hiding a1 (a tie), so hiding a1 never strictly helps.

One more insight worth reporting: in **946 / 956** of these instances, the agent owning the odd path has **some** opponent profile where a withholding report **ties** with truth. Truth-telling there is only *weakly* dominant. These instances are on a knife edge: one extra attack would usually make them manipulable. This explains why the condition is sufficient but far from necessary.

---

## 6. The demonstration: what's wrong and how to make it much better

### 6.1 Issues with the current `results/argumentation_demo.html`

1. **Only Part 2 is shown.** Nothing from the engine half (conflict-free, defence, F, admissible/complete, the four semantics, labellings, acceptance status) is visible. That is half the assignment.
2. **Duplicated logic.** The page re-implements grounded semantics in JavaScript (`groundedOutcome`) instead of using the tested Python engine. The demo can silently disagree with the code being graded.
3. **Hard-coded geometry.** Node positions exist only for a1–a6, so the page cannot draw Figures 5.1–5.3 or any random instance. The 956 interesting cases are embedded (2.8 MB of JSON, making the HTML 1.5 MB), yet only the first is shown, as one sentence of text.
4. **Agent-X-specific UI.** The verdict line always talks about X's gain or loss.
5. **No strategic analysis is visualised.** There is no best-response table, no Theorem 5.3 counterexample display, and no highlighting of the Theorem 5.4 odd path. These are exactly what an examiner wants to see.
6. **Misleading metric.** "Theorem 5.4 condition: 1.5 %" has no explanation that self-attacks cause it.
7. **Small polish issues.** The graph card has a large empty area under a small graph, and the text says "each dot" while the chart shows bars.
8. **The book misprints are not mentioned.** The brief explicitly asks students to notice them.

### 6.2 Proposed demo (storyline for a ~5-minute live demonstration)

1. **Framework lab.** Load Fig 5.1, 5.2, 5.3, Ex 5.10, Ex 5.11, a random instance, or a custom edge list. Use auto-layout so any graph renders.
2. **Semantics panel** (Part 1):
   - step through F⁰(∅) → F¹ → F² with highlighting, until the fixed point (grounded) is reached;
   - list complete, preferred, stable and semi-stable extensions;
   - show each legal labelling coloured in/out/undec, tagged with which semantics it matches (Table 5.1);
   - click an argument to see its skeptical/credulous/rejected status under each semantics;
   - test conflict-free, admissible and complete on a user-selected set S.
3. **Mechanism panel** (Part 2):
   - assign arguments to agents and toggle reports;
   - show a best-response table for any agent (all 2^|Ai| reports with utility and outcome);
   - add a "Check Theorem 5.3" button that animates the found counterexample;
   - add a "Check Theorem 5.4" button that highlights the odd path on the graph.
4. **Experiments panel**:
   - SP fraction chart with and without self-attacks;
   - the self-attack breakdown;
   - the stress-test result for Q2;
   - the Q3 category bar (A–D) where clicking a category **loads a representative instance into the graph**, linking the statistics back to concrete pictures.
5. **Misprint callouts** on Ex 5.10 and Ex 5.11.

Implementation choice:
- **Streamlit app** (recommended). It calls `argumentation.py`/`strategic.py` directly, so there is one source of truth, and it takes about 300 lines. It needs `pip install streamlit` and runs with `streamlit run app.py`.
- **Upgrade of the existing static HTML.** Python precomputes everything (extensions, labellings, best-response tables, witnesses) into JSON and the page only renders it. It stays a single offline file, but custom graphs cannot be analysed live.

---

## 7. Prioritised action plan

**Must do before submission**
1. Add `tests/test_book_examples.py` covering every example in §3 (runnable with `python -m unittest` or `pytest`).
2. Write the report (PDF), answering X1–X3 with the tables and categories from §4–5, the walk-vs-path and self-attack discussion, and the two misprints.
3. Add a `--no-self-attacks` flag to `experiments.py` and report both settings.
4. Add the Q2 stress test (`--condition-holding N`) and the Q3 classifier as code, so the report's numbers are reproducible.

**Should do (the demo)**
5. Rebuild the demo per §6.2.

**Nice to have**
6. Add a `.gitignore` and remove the committed `__pycache__/`. Make the README cross-platform (it currently assumes PowerShell and `..\as_env`).
7. Make `check_theorem_5_4` return *all* witnesses, not just the first; the Q3 analysis needs them.
8. Make `acceptance_status` return a single label ("skeptically accepted" / "credulously accepted" / "rejected") alongside the booleans. Document the vacuous case (no stable extensions).
9. `experiments._truthfulness_margin_audit` duplicates the Theorem 5.3 loop. Fold it into `strategic.py`.
10. Optionally mark in `legal_labellings` which labelling is grounded, preferred, stable or semi-stable, and cross-check that the in-sets equal the complete extensions.

---

## 8. Reproducing this review

The checks in this report were run with throw-away scripts in `/tmp` (not committed):

- `verify_book.py`: the 29 textbook assertions in §3.
- `analyze.py`: compares the walk and simple-path readings, with and without self-attacks (§5.1–5.2).
- `stress.py`: samples until 3000 condition-holding instances are found (§5.3).
- `classify.py`: sorts the 956 Q3 instances into categories A–D (§5.4).

These can be turned into the test file and experiment flags in step 1–4 of §7.
