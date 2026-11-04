# Argumentation Framework Functions

Code for Assignment 3 of CSL7650 Autonomous Systems. The project currently contains the abstract argumentation engine, strategic argumentation functions, a reproducible experiment runner, and an offline interactive demo.

## Run in the existing `as_env` environment

From PowerShell, in this project directory:

```powershell
& ..\as_env\Scripts\Activate.ps1
python experiments.py --instances-per-p 1000 --seed 2026
python demo.py
Start-Process .\results\argumentation_demo.html
```

The experiment command runs 1,000 instances at each of `p = 0.15`, `0.25`, and `0.35` (3,000 total). It uses only the Python standard library; no package installation is required.

For a quick preview before the full run, use:

```powershell
python experiments.py --instances-per-p 10 --seed 2026
python demo.py
Start-Process .\results\argumentation_demo.html
```

## Generated files

- `results/experiment_instances.csv` — one row per random instance, including graph, agent types, and both classifications.
- `results/experiment_summary.json` — aggregate fractions and 95% Wilson intervals, with the generator settings.
- `results/interesting_cases.json` — all cases where Theorem 5.4's condition fails but the mechanism is strategyproof, plus any cases that appear to contradict its sufficiency.
- `results/argumentation_demo.html` — self-contained interactive page with the textbook examples and experiment charts.

The generator samples 6–8 arguments, includes self-attacks among the possible directed attacks, and assigns arguments uniformly to three nonempty agent types. Its fixed seed makes the run reproducible. The browser demo has no external assets or JavaScript dependencies.

## Modules

- `argumentation.py` — framework representation, semantics, extensions, labellings, and acceptance status.
- `strategic.py` — grounded direct mechanism, best responses, and exhaustive checks for Theorems 5.3 and 5.4.
- `experiments.py` — random-instance generation and CSV/JSON result collection.
- `demo.py` — HTML generator for the interactive graph and result dashboard.
