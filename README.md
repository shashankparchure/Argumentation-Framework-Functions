# Argumentation Framework Functions

Code for Assignment 3 of CSL7650 Autonomous Systems (Chapter 5, "Argumentation among Agents", of Weiss, *Multiagent Systems*). The project contains the abstract argumentation engine, the strategic argumentation functions, tests against the textbook examples, a reproducible experiment runner, and an interactive Streamlit demo.

The engine, tests and experiments use only the Python standard library. The demo needs Streamlit.

## Quick start

Linux / macOS:

```bash
python3 -m unittest discover -s tests -t .        # 39 tests against the book's examples
python3 experiments.py                             # main run, self-attacks allowed  -> results/
python3 experiments.py --no-self-attacks           # same seeds, no self-attacks     -> results/no_self_attacks/
python3 experiments.py --stress 3000               # Q2 stress test                  -> results/stress_test.json

python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/streamlit run app.py                     # interactive demo at http://localhost:8501
```

Windows (PowerShell):

```powershell
python -m unittest discover -s tests -t .
python experiments.py
python experiments.py --no-self-attacks
python experiments.py --stress 3000
python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt
.\.venv\Scripts\streamlit run app.py
```

Each experiment run takes a few seconds. The main run evaluates 1,000 instances at each of `p = 0.15`, `0.25` and `0.35` with seed 2026. Use `--instances-per-p 10` for a quick preview.

## Experiment design

- Each instance has 6–8 arguments. Every ordered pair, including self-attacks unless `--no-self-attacks` is given, is an attack with probability p. Arguments are split uniformly at random among agents x, y and z, and each agent gets at least one.
- Strategyproofness (Theorem 5.3) is checked exhaustively. For each agent, the truthful report is compared with every subset report, against every combination of subsets the other agents could reveal.
- Theorem 5.4's "odd-length path" is checked as an odd walk, using a breadth-first search over (argument, parity) states, so cycles are handled. Pairs with α = β count, so a self-attack or an odd cycle through an owned argument violates the condition. The simple-path reading is reported alongside; on every generated instance the two readings agree.
- For every instance where the condition fails but the mechanism is strategyproof (assignment question 3), `analysis.py` labels the reason: every target attacks itself, only odd cycles, only direct conflicts within a type, or a live indirect path that is neutralised as in Example 5.11.
- The same seed generates the same graphs in both runs; the second run simply drops the self-attacks.

## Generated files

In `results/` (and `results/no_self_attacks/`):

- `experiment_instances.csv`: one row per instance, with the graph, the agent types, both classifications and the question 3 category.
- `experiment_summary.json`: per-p fractions, 95 % Wilson intervals, self-attack counts and question 3 category counts.
- `interesting_cases.json`: every instance that contradicts Theorem 5.4's sufficiency (question 2, none found so far) and every condition-fails-but-strategyproof instance (question 3), each with its explanation and an exhaustive truthfulness audit.
- `stress_test.json` (main folder only): result of `--stress`.
- `argumentation_demo.html`: the older static page built by `demo.py`. The Streamlit app supersedes it.

## Textbook misprints

- Example 5.10 attaches each of y's and z's utilities to the other agent's argument set. With A_y = {α2}, A_z = {α3} and outcome {α1, α3}, the utilities are u_y = 0 and u_z = 1.
- After Example 5.11, the argument that cancels x's indirect self-defeat is α6, not α5.

Both are checked in `tests/test_strategic.py`.

## Modules

- `argumentation.py`: framework representation, conflict-freeness, defence, characteristic function, admissible/complete checks, grounded/complete/preferred/stable/semi-stable extensions, labellings and acceptance status.
- `strategic.py`: the grounded direct mechanism, best responses, the exhaustive Theorem 5.3 check, and Theorem 5.4's odd-path condition (walk and simple-path readings, plus all witnesses).
- `analysis.py`: explains why an instance is strategyproof although Theorem 5.4's condition fails.
- `experiments.py`: random instance generation, the main experiment and the stress test.
- `app.py`: Streamlit demo with four tabs. Semantics covers step-by-step grounded construction, all extensions, labellings, acceptance status and a set tester. The strategic mechanism tab covers report toggles, utilities, best-response tables, Theorem 5.3 counterexamples and Theorem 5.4 path highlighting. Experiments has charts and a browser for the question 3 cases. Notes lists the misprints and modelling choices.
- `ui.py`: presentation layer for the demo: theme CSS, the animated SVG argument graph (labelling changes morph in place, odd paths pulse, hover shows attacks), styled tables, chips and animated charts. `.streamlit/config.toml` sets the dark theme and fonts.
- `tests/`: unit tests for Figures 5.1–5.3, Examples 5.5–5.8, 5.10 and 5.11, odd-path edge cases and the generator.
