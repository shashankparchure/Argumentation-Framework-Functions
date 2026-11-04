"""Reproducible random experiments for strategic argumentation Assignment 3."""

from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from itertools import combinations, product
from pathlib import Path
from typing import Any

from analysis import CATEGORIES, explain_condition_failure
from argumentation import ArgumentationFramework
from strategic import (
    check_theorem_5_3,
    check_theorem_5_4,
    grounded_direct_argumentation_mechanism,
)


PROBABILITIES = (0.15, 0.25, 0.35)
AGENTS = ("x", "y", "z")
ARGUMENT_COUNTS = (6, 7, 8)


def _sorted_arguments(values: Any) -> list[str]:
    return sorted(values, key=str)


def _random_nonempty_partition(
    arguments: list[str],
    rng: random.Random,
) -> dict[str, frozenset[str]]:
    """Sample an assignment uniformly, conditioned on all three agents owning arguments."""

    while True:
        owners = [rng.choice(AGENTS) for _ in arguments]
        if set(owners) == set(AGENTS):
            return {
                agent: frozenset(
                    argument
                    for argument, owner in zip(arguments, owners)
                    if owner == agent
                )
                for agent in AGENTS
            }


def _format_path(path: tuple[str, ...] | None) -> dict[str, Any] | None:
    if path is None:
        return None
    return {"arguments": list(path), "length": len(path) - 1}


def _type_record(agent_types: dict[str, frozenset[str]]) -> dict[str, list[str]]:
    return {
        agent: _sorted_arguments(arguments)
        for agent, arguments in agent_types.items()
    }


def _counterexample_record(result: Any) -> dict[str, Any] | None:
    violation = result.counterexample
    if violation is None:
        return None
    return {
        "agent": violation.agent,
        "other_reports": _type_record(dict(violation.other_reports)),
        "truthful_report": _sorted_arguments(violation.truthful_report),
        "profitable_report": _sorted_arguments(violation.profitable_report),
        "truthful_utility": violation.truthful_utility,
        "profitable_utility": violation.profitable_utility,
        "truthful_outcome": _sorted_arguments(violation.truthful_outcome),
        "profitable_outcome": _sorted_arguments(violation.profitable_outcome),
    }


def _wilson_interval(successes: int, trials: int) -> tuple[float, float]:
    """Return a 95% Wilson score interval for a binomial proportion."""

    if trials == 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    proportion = successes / trials
    denominator = 1.0 + z * z / trials
    center = (proportion + z * z / (2.0 * trials)) / denominator
    margin = (
        z
        * ((proportion * (1.0 - proportion) / trials) + z * z / (4.0 * trials * trials)) ** 0.5
        / denominator
    )
    return (max(0.0, center - margin), min(1.0, center + margin))


def _make_instance(
    probability: float,
    instance_seed: int,
    allow_self_attacks: bool = True,
) -> tuple[list[str], list[tuple[str, str]], dict[str, frozenset[str]]]:
    rng = random.Random(instance_seed)
    argument_count = rng.choice(ARGUMENT_COUNTS)
    arguments = [f"a{index}" for index in range(1, argument_count + 1)]
    # rng.random() is drawn for every pair so that a seed yields the same graph
    # with and without self-attacks.
    attacks = [
        (source, target)
        for source in arguments
        for target in arguments
        if rng.random() < probability and (allow_self_attacks or source != target)
    ]
    agent_types = _random_nonempty_partition(arguments, rng)
    return arguments, attacks, agent_types


def _build_case_record(
    instance_id: str,
    probability: float,
    instance_seed: int,
    arguments: list[str],
    attacks: list[tuple[str, str]],
    agent_types: dict[str, frozenset[str]],
    theorem53: Any,
    theorem54: Any,
) -> dict[str, Any]:
    witness = theorem54.witness
    return {
        "instance_id": instance_id,
        "seed": instance_seed,
        "p": probability,
        "arguments": arguments,
        "attacks": [[source, target] for source, target in attacks],
        "agent_types": _type_record(agent_types),
        "theorem54_witness": None if witness is None else {
            "agent": witness.agent,
            "source": witness.source,
            "target": witness.target,
            **(_format_path(witness.path) or {}),
        },
        "theorem53_comparisons_checked": theorem53.comparisons_checked,
        "theorem53_counterexample": _counterexample_record(theorem53),
    }


def _truthfulness_margin_audit(
    framework: ArgumentationFramework,
    agent_types: dict[str, frozenset[str]],
) -> dict[str, Any]:
    """Explain an SP result with each agent's worst exhaustive hiding margin."""

    def powerset(arguments: frozenset[str]) -> tuple[frozenset[str], ...]:
        ordered = sorted(arguments)
        return tuple(
            frozenset(members)
            for size in range(len(ordered) + 1)
            for members in combinations(ordered, size)
        )

    outcome_cache: dict[frozenset[str], frozenset[str]] = {}

    def outcome(reports: dict[str, frozenset[str]]) -> frozenset[str]:
        union = frozenset().union(*reports.values())
        if union not in outcome_cache:
            outcome_cache[union] = grounded_direct_argumentation_mechanism(framework, reports)
        return outcome_cache[union]

    audit: dict[str, Any] = {}
    for agent in AGENTS:
        others = tuple(other for other in AGENTS if other != agent)
        other_options = tuple(powerset(agent_types[other]) for other in others)
        own_alternatives = tuple(
            report for report in powerset(agent_types[agent])
            if report != agent_types[agent]
        )
        profile_count = 0
        strict_truthful_count = 0
        tied_best_withholding_count = 0
        min_margin: int | None = None
        worst_case: dict[str, Any] | None = None

        for selected in product(*other_options):
            other_reports = dict(zip(others, selected))
            truthful_profile = {**other_reports, agent: agent_types[agent]}
            truthful_outcome = outcome(truthful_profile)
            truthful_utility = len(agent_types[agent] & truthful_outcome)

            alternatives: list[tuple[int, frozenset[str], frozenset[str]]] = []
            for report in own_alternatives:
                profile = {**other_reports, agent: report}
                result = outcome(profile)
                alternatives.append((len(agent_types[agent] & result), report, result))

            profile_count += 1
            if not alternatives:
                continue
            best_utility = max(item[0] for item in alternatives)
            margin = truthful_utility - best_utility
            if margin > 0:
                strict_truthful_count += 1
            elif margin == 0:
                tied_best_withholding_count += 1

            if min_margin is None or margin < min_margin:
                min_margin = margin
                best_alternative = next(item for item in alternatives if item[0] == best_utility)
                worst_case = {
                    "other_reports": {
                        other: sorted(report)
                        for other, report in other_reports.items()
                    },
                    "truthful_utility": truthful_utility,
                    "best_withholding_report": sorted(best_alternative[1]),
                    "best_withholding_utility": best_alternative[0],
                    "margin_truthful_minus_best_withholding": margin,
                }

        audit[agent] = {
            "opponent_profiles_checked": profile_count,
            "minimum_truthful_utility_margin": min_margin,
            "profiles_truthful_strictly_better": strict_truthful_count,
            "profiles_with_a_tied_best_withholding_report": tied_best_withholding_count,
            "profitable_profiles": profile_count - strict_truthful_count - tied_best_withholding_count,
            "worst_case": worst_case,
        }
    return audit


def _default_output(allow_self_attacks: bool) -> Path:
    results = Path(__file__).resolve().parent / "results"
    return results if allow_self_attacks else results / "no_self_attacks"


def _resolve_output(output_directory: Path | str | None, allow_self_attacks: bool) -> Path:
    if output_directory is None:
        output_path = _default_output(allow_self_attacks)
    else:
        output_path = Path(output_directory).expanduser().resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _explanation_record(explanation: Any) -> dict[str, Any]:
    return {
        "category": explanation.category,
        "title": explanation.title,
        "pairs": [
            {
                "agent": pair.agent,
                "source": pair.source,
                "target": pair.target,
                "path": list(pair.path),
                "reason": pair.reason,
            }
            for pair in explanation.pairs
        ],
    }


def run_experiments(
    instances_per_probability: int = 1000,
    seed: int = 2026,
    output_directory: Path | str | None = None,
    allow_self_attacks: bool = True,
) -> dict[str, Any]:
    """Run all required random instances and write CSV/JSON results.

    Output goes to ``./results`` by default, or ``./results/no_self_attacks``
    when ``allow_self_attacks`` is false. The same seed produces the same
    graphs in both settings, minus the self-attacks.
    """

    if instances_per_probability < 1:
        raise ValueError("instances_per_probability must be at least 1.")
    output_path = _resolve_output(output_directory, allow_self_attacks)

    master_rng = random.Random(seed)
    summary_rows: list[dict[str, Any]] = []
    unexpected_cases: list[dict[str, Any]] = []
    condition_not_necessary_cases: list[dict[str, Any]] = []
    csv_path = output_path / "experiment_instances.csv"

    fieldnames = (
        "instance_id",
        "instance_seed",
        "p",
        "argument_count",
        "attack_count",
        "has_self_attack",
        "arguments",
        "attacks",
        "agent_types",
        "strategyproof",
        "theorem54_condition",
        "theorem54_condition_simple_path",
        "theorem53_comparisons_checked",
        "theorem54_pairs_checked",
        "condition_true_but_not_strategyproof",
        "condition_false_but_strategyproof",
        "q3_category",
    )

    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()

        for probability in PROBABILITIES:
            strategyproof_count = 0
            condition_count = 0
            simple_condition_count = 0
            condition_true_not_sp = 0
            simple_condition_true_not_sp = 0
            condition_false_sp = 0
            self_attack_instances = 0
            q3_categories: Counter[str] = Counter()
            argument_count_totals = {count: 0 for count in ARGUMENT_COUNTS}

            print(
                f"Running p={probability:.2f}: 0/{instances_per_probability}",
                flush=True,
            )
            for index in range(1, instances_per_probability + 1):
                instance_seed = master_rng.getrandbits(64)
                instance_id = f"p{int(probability * 100):02d}_{index:04d}"
                arguments, attacks, agent_types = _make_instance(
                    probability, instance_seed, allow_self_attacks
                )
                framework = ArgumentationFramework(arguments, attacks)
                theorem53 = check_theorem_5_3(framework, agent_types)
                theorem54 = check_theorem_5_4(framework, agent_types)
                simple_holds = check_theorem_5_4(
                    framework, agent_types, reading="simple"
                ).condition_holds

                strategyproof = theorem53.strategyproof
                condition_holds = theorem54.condition_holds
                has_self_attack = any(source == target for source, target in attacks)
                strategyproof_count += int(strategyproof)
                condition_count += int(condition_holds)
                simple_condition_count += int(simple_holds)
                condition_true_not_sp += int(condition_holds and not strategyproof)
                simple_condition_true_not_sp += int(simple_holds and not strategyproof)
                condition_false_sp += int(not condition_holds and strategyproof)
                self_attack_instances += int(has_self_attack)
                argument_count_totals[len(arguments)] += 1

                case_record = _build_case_record(
                    instance_id,
                    probability,
                    instance_seed,
                    arguments,
                    attacks,
                    agent_types,
                    theorem53,
                    theorem54,
                )
                q3_category = ""
                if condition_holds and not strategyproof:
                    unexpected_cases.append(case_record)
                if not condition_holds and strategyproof:
                    explanation = explain_condition_failure(framework, agent_types)
                    q3_category = explanation.category
                    q3_categories[q3_category] += 1
                    case_record["explanation"] = _explanation_record(explanation)
                    case_record["truthfulness_audit"] = _truthfulness_margin_audit(
                        framework,
                        agent_types,
                    )
                    condition_not_necessary_cases.append(case_record)

                writer.writerow(
                    {
                        "instance_id": instance_id,
                        "instance_seed": instance_seed,
                        "p": f"{probability:.2f}",
                        "argument_count": len(arguments),
                        "attack_count": len(attacks),
                        "has_self_attack": has_self_attack,
                        "arguments": json.dumps(arguments),
                        "attacks": json.dumps([[a, b] for a, b in attacks]),
                        "agent_types": json.dumps(_type_record(agent_types)),
                        "strategyproof": strategyproof,
                        "theorem54_condition": condition_holds,
                        "theorem54_condition_simple_path": simple_holds,
                        "theorem53_comparisons_checked": theorem53.comparisons_checked,
                        "theorem54_pairs_checked": theorem54.pairs_checked,
                        "condition_true_but_not_strategyproof": condition_holds and not strategyproof,
                        "condition_false_but_strategyproof": not condition_holds and strategyproof,
                        "q3_category": q3_category,
                    }
                )

                if index % 100 == 0 or index == instances_per_probability:
                    print(
                        f"Running p={probability:.2f}: {index}/{instances_per_probability}",
                        flush=True,
                    )

            interval = _wilson_interval(strategyproof_count, instances_per_probability)
            summary_rows.append(
                {
                    "p": probability,
                    "instances": instances_per_probability,
                    "strategyproof_count": strategyproof_count,
                    "strategyproof_fraction": strategyproof_count / instances_per_probability,
                    "strategyproof_ci95": [interval[0], interval[1]],
                    "self_attack_instances": self_attack_instances,
                    "theorem54_condition_count": condition_count,
                    "theorem54_condition_fraction": condition_count / instances_per_probability,
                    "theorem54_condition_simple_path_count": simple_condition_count,
                    "condition_true_but_not_strategyproof": condition_true_not_sp,
                    "condition_true_but_not_strategyproof_simple_path": simple_condition_true_not_sp,
                    "condition_false_but_strategyproof": condition_false_sp,
                    "q3_categories": {name: q3_categories[name] for name in CATEGORIES},
                    "argument_count_distribution": {
                        str(count): number for count, number in argument_count_totals.items()
                    },
                }
            )

    def total(key: str) -> int:
        return sum(row[key] for row in summary_rows)

    summary = {
        "schema_version": 2,
        "seed": seed,
        "generator": {
            "instances_per_probability": instances_per_probability,
            "probabilities": list(PROBABILITIES),
            "argument_count_choices": list(ARGUMENT_COUNTS),
            "agents": list(AGENTS),
            "self_attacks": allow_self_attacks,
            "attack_sampling": (
                "Each ordered pair, including self-attacks, is sampled independently with probability p."
                if allow_self_attacks
                else "Each ordered pair of distinct arguments is sampled independently with probability p."
            ),
            "agent_partition": "Arguments are assigned uniformly at random to x, y, and z, conditioned on each agent receiving at least one argument.",
            "utility": "Number of arguments in the agent's true type that occur in the grounded outcome.",
            "strategyproof_test": "Truthful report is compared with every subset report against every combination of other-agent reports.",
            "theorem54_reading": "Odd walk (vertices may repeat); the simple-path reading is reported alongside.",
        },
        "q3_category_titles": {name: title for name, (title, _) in CATEGORIES.items()},
        "results": summary_rows,
        "totals": {
            "instances": total("instances"),
            "strategyproof": total("strategyproof_count"),
            "self_attack_instances": total("self_attack_instances"),
            "theorem54_condition": total("theorem54_condition_count"),
            "theorem54_condition_simple_path": total("theorem54_condition_simple_path_count"),
            "condition_true_but_not_strategyproof": total("condition_true_but_not_strategyproof"),
            "condition_true_but_not_strategyproof_simple_path": total(
                "condition_true_but_not_strategyproof_simple_path"
            ),
            "condition_false_but_strategyproof": total("condition_false_but_strategyproof"),
            "q3_categories": {
                name: sum(row["q3_categories"][name] for row in summary_rows)
                for name in CATEGORIES
            },
        },
    }

    summary_path = output_path / "experiment_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    cases_path = output_path / "interesting_cases.json"
    cases_path.write_text(
        json.dumps(
            {
                "condition_true_but_not_strategyproof": unexpected_cases,
                "condition_false_but_strategyproof": condition_not_necessary_cases,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"\nSaved instance data: {csv_path}")
    print(f"Saved summary:       {summary_path}")
    print(f"Saved cases:         {cases_path}")
    print(f"Self-attacks allowed: {allow_self_attacks}")
    print("\np       strategyproof    Thm 5.4 condition    cond. true / SP false    cond. false / SP true")
    for row in summary_rows:
        print(
            f"{row['p']:.2f}    "
            f"{row['strategyproof_count']:4d}/{row['instances']:<4d} "
            f"({row['strategyproof_fraction'] * 100:5.1f}%)    "
            f"{row['theorem54_condition_count']:4d}/{row['instances']:<4d} "
            f"({row['theorem54_condition_fraction'] * 100:5.1f}%)    "
            f"{row['condition_true_but_not_strategyproof']:6d}                  "
            f"{row['condition_false_but_strategyproof']:6d}"
        )
    print("\nWhy the condition fails on strategyproof instances (Q3):")
    for name, (title, _) in CATEGORIES.items():
        print(f"  {summary['totals']['q3_categories'][name]:5d}  {title}")
    return summary


def run_stress_test(
    target_instances: int = 3000,
    seed: int = 2026,
    output_directory: Path | str | None = None,
    allow_self_attacks: bool = False,
) -> dict[str, Any]:
    """Sample instances until ``target_instances`` satisfy Theorem 5.4, then test SP.

    The ordinary experiment yields few condition-holding instances, so it says
    little about sufficiency (Q2). Instances are kept when the weaker
    simple-path reading of the condition holds; this includes every instance
    where the walk reading holds.
    """

    if target_instances < 1:
        raise ValueError("target_instances must be at least 1.")
    output_path = _resolve_output(
        output_directory if output_directory is not None else _default_output(True),
        allow_self_attacks,
    )

    rng = random.Random(seed)
    sampled = 0
    kept_by_p: Counter[float] = Counter()
    walk_holds = 0
    violations: list[dict[str, Any]] = []
    while sum(kept_by_p.values()) < target_instances:
        sampled += 1
        probability = rng.choice(PROBABILITIES)
        instance_seed = rng.getrandbits(64)
        arguments, attacks, agent_types = _make_instance(
            probability, instance_seed, allow_self_attacks
        )
        framework = ArgumentationFramework(arguments, attacks)
        if not check_theorem_5_4(framework, agent_types, reading="simple").condition_holds:
            continue
        kept_by_p[probability] += 1
        walk = check_theorem_5_4(framework, agent_types).condition_holds
        walk_holds += int(walk)
        theorem53 = check_theorem_5_3(framework, agent_types)
        if not theorem53.strategyproof:
            violations.append(
                {
                    "instance_seed": instance_seed,
                    "p": probability,
                    "walk_condition_holds": walk,
                    "arguments": arguments,
                    "attacks": [[a, b] for a, b in attacks],
                    "agent_types": _type_record(agent_types),
                    "theorem53_counterexample": _counterexample_record(theorem53),
                }
            )
        kept = sum(kept_by_p.values())
        if kept % 500 == 0:
            print(f"Stress test: {kept}/{target_instances} condition-holding instances", flush=True)

    result = {
        "seed": seed,
        "self_attacks": allow_self_attacks,
        "instances_sampled": sampled,
        "condition_holding_instances": sum(kept_by_p.values()),
        "condition_holding_by_p": {f"{p:.2f}": kept_by_p[p] for p in PROBABILITIES},
        "walk_condition_holds": walk_holds,
        "not_strategyproof": len(violations),
        "not_strategyproof_with_walk_condition": sum(
            1 for case in violations if case["walk_condition_holds"]
        ),
        "violations": violations,
    }
    stress_path = output_path / "stress_test.json"
    stress_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"\nSampled {sampled} instances; {result['condition_holding_instances']} satisfy "
        f"Theorem 5.4 (simple-path reading, {walk_holds} also under the walk reading); "
        f"{len(violations)} are not strategyproof."
    )
    print(f"Saved stress test:   {stress_path}")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the Assignment 3 strategic argumentation experiments."
    )
    parser.add_argument(
        "--instances-per-p",
        type=int,
        default=1000,
        help="number of random instances for each of the three p values (default: 1000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=2026,
        help="master random seed for reproducibility (default: 2026)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="directory for output (default: ./results, or ./results/no_self_attacks)",
    )
    parser.add_argument(
        "--no-self-attacks",
        action="store_true",
        help="never sample attacks of an argument on itself",
    )
    parser.add_argument(
        "--stress",
        type=int,
        metavar="N",
        default=None,
        help="instead of the main experiment, sample until N instances satisfy "
        "Theorem 5.4 and test each for strategyproofness (self-attacks are always "
        "excluded, since they violate the condition)",
    )
    args = parser.parse_args()
    if args.stress is not None:
        run_stress_test(args.stress, args.seed, args.output_dir)
    else:
        run_experiments(
            args.instances_per_p,
            args.seed,
            args.output_dir,
            allow_self_attacks=not args.no_self_attacks,
        )


if __name__ == "__main__":
    main()
