"""Strategic reporting functions for grounded argumentation mechanisms.

Agent types may overlap. An agent's utility is the number of arguments in its
true type that are in the mechanism outcome, regardless of which arguments it
reports. All best-response and strategyproofness checks are exhaustive.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Hashable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from itertools import combinations, product
from types import MappingProxyType
from typing import TypeAlias

from argumentation import Argument, ArgumentSet, ArgumentationFramework


Agent: TypeAlias = Hashable
AgentTypes: TypeAlias = Mapping[Agent, Iterable[Argument]]


@dataclass(frozen=True)
class BestResponseResult:
    """All reports attaining an agent's maximum utility against fixed reports."""

    agent: Agent
    utility: int
    best_reports: tuple[ArgumentSet, ...]
    utilities_by_report: Mapping[ArgumentSet, int]
    outcomes_by_report: Mapping[ArgumentSet, ArgumentSet]


@dataclass(frozen=True)
class StrategyproofnessViolation:
    """A profile at which withholding arguments improves an agent's utility."""

    agent: Agent
    other_reports: Mapping[Agent, ArgumentSet]
    truthful_report: ArgumentSet
    profitable_report: ArgumentSet
    truthful_utility: int
    profitable_utility: int
    truthful_outcome: ArgumentSet
    profitable_outcome: ArgumentSet


@dataclass(frozen=True)
class Theorem53Result:
    """Result of the exhaustive strategyproofness check in Theorem 5.3."""

    strategyproof: bool
    comparisons_checked: int
    counterexample: StrategyproofnessViolation | None = None


@dataclass(frozen=True)
class OddPathWitness:
    """An odd-length directed walk between two arguments owned by one agent.

    Vertices may repeat. This parity-walk interpretation makes cycle handling
    finite and includes odd cycles that return to their starting argument.
    """

    agent: Agent
    source: Argument
    target: Argument
    path: tuple[Argument, ...]

    @property
    def length(self) -> int:
        """Number of attack edges in the witness."""

        return len(self.path) - 1


@dataclass(frozen=True)
class Theorem54Result:
    """Result of checking Theorem 5.4's odd-path sufficient condition."""

    condition_holds: bool
    pairs_checked: int
    witness: OddPathWitness | None = None


def _ordered(values: Iterable[Hashable]) -> tuple[Hashable, ...]:
    """Use a stable order for exhaustive enumeration and reproducible reports."""

    return tuple(sorted(values, key=repr))


def _powerset(values: Iterable[Argument]) -> tuple[ArgumentSet, ...]:
    ordered_values = _ordered(values)
    return tuple(
        frozenset(members)
        for size in range(len(ordered_values) + 1)
        for members in combinations(ordered_values, size)
    )


def _normalize_agent_types(
    framework: ArgumentationFramework,
    agent_types: AgentTypes,
) -> dict[Agent, ArgumentSet]:
    """Copy and validate agent types against the full framework."""

    normalized: dict[Agent, ArgumentSet] = {}
    for agent, arguments in agent_types.items():
        try:
            owned = frozenset(arguments)
        except TypeError as error:
            raise TypeError(f"The type for agent {agent!r} must contain hashable arguments.") from error
        unknown = owned - framework.arguments
        if unknown:
            raise ValueError(
                f"The type for agent {agent!r} contains arguments outside the framework: {unknown!r}."
            )
        normalized[agent] = owned
    return normalized


def _normalize_reports(
    agent_types: Mapping[Agent, ArgumentSet],
    reports: Mapping[Agent, Iterable[Argument]],
    *,
    omitted_agents_report_empty: bool,
) -> dict[Agent, ArgumentSet]:
    unknown_agents = set(reports) - set(agent_types)
    if unknown_agents:
        raise ValueError(f"Reports were supplied for unknown agents: {unknown_agents!r}.")

    normalized: dict[Agent, ArgumentSet] = {}
    for agent, report in reports.items():
        try:
            revealed = frozenset(report)
        except TypeError as error:
            raise TypeError(f"The report for agent {agent!r} must contain hashable arguments.") from error
        if not revealed.issubset(agent_types[agent]):
            extra = revealed - agent_types[agent]
            raise ValueError(
                f"Agent {agent!r} reported arguments outside its type: {extra!r}."
            )
        normalized[agent] = revealed

    if omitted_agents_report_empty:
        for agent in agent_types:
            normalized.setdefault(agent, frozenset())
    return normalized


def _outcome_for_union(
    framework: ArgumentationFramework,
    revealed_arguments: ArgumentSet,
    cache: dict[ArgumentSet, ArgumentSet],
) -> ArgumentSet:
    outcome = cache.get(revealed_arguments)
    if outcome is None:
        outcome = framework.induced_subframework(revealed_arguments).grounded_extension()
        cache[revealed_arguments] = outcome
    return outcome


def grounded_direct_argumentation_mechanism(
    framework: ArgumentationFramework,
    reports: Mapping[Agent, Iterable[Argument]] | Iterable[Iterable[Argument]],
) -> ArgumentSet:
    """Return the grounded extension induced by the union of all reports.

    ``reports`` can be a mapping from agent identifiers to reports or any
    iterable containing one report set per agent. Reports may overlap.
    """

    report_sets = reports.values() if isinstance(reports, Mapping) else reports
    revealed: set[Argument] = set()
    for report in report_sets:
        try:
            revealed.update(report)
        except TypeError as error:
            raise TypeError("Every report must contain hashable arguments.") from error

    induced = framework.induced_subframework(revealed)
    return induced.grounded_extension()


def best_responses(
    framework: ArgumentationFramework,
    agent_types: AgentTypes,
    agent: Agent,
    other_reports: Mapping[Agent, Iterable[Argument]],
) -> BestResponseResult:
    """Enumerate all best reports for ``agent`` against fixed other reports.

    The selected agent must be omitted from ``other_reports``. Other agents
    omitted from that mapping are treated as reporting the empty set.
    """

    types = _normalize_agent_types(framework, agent_types)
    if agent not in types:
        raise KeyError(f"Unknown agent: {agent!r}.")
    if agent in other_reports:
        raise ValueError("other_reports must not include the agent whose best response is sought.")

    others = _normalize_reports(
        types,
        other_reports,
        omitted_agents_report_empty=False,
    )
    cache: dict[ArgumentSet, ArgumentSet] = {}
    utilities: dict[ArgumentSet, int] = {}
    outcomes: dict[ArgumentSet, ArgumentSet] = {}
    true_arguments = types[agent]

    for own_report in _powerset(true_arguments):
        complete_profile = dict(others)
        complete_profile[agent] = own_report
        union = frozenset().union(*complete_profile.values())
        outcome = _outcome_for_union(framework, union, cache)
        outcomes[own_report] = outcome
        utilities[own_report] = len(true_arguments & outcome)

    maximum_utility = max(utilities.values())
    best = tuple(
        report for report in _powerset(true_arguments)
        if utilities[report] == maximum_utility
    )
    return BestResponseResult(
        agent=agent,
        utility=maximum_utility,
        best_reports=best,
        utilities_by_report=MappingProxyType(utilities),
        outcomes_by_report=MappingProxyType(outcomes),
    )


def _other_report_profiles(
    agent_types: Mapping[Agent, ArgumentSet],
    excluded_agent: Agent,
) -> Iterator[dict[Agent, ArgumentSet]]:
    other_agents = tuple(
        agent for agent in _ordered(agent_types) if agent != excluded_agent
    )
    report_options = tuple(_powerset(agent_types[agent]) for agent in other_agents)
    for selected_reports in product(*report_options):
        yield dict(zip(other_agents, selected_reports))


def check_theorem_5_3(
    framework: ArgumentationFramework,
    agent_types: AgentTypes,
) -> Theorem53Result:
    """Check whether truthful reporting is a best response in every profile.

    This is an exhaustive check: for each agent it enumerates every possible
    combination of reports by the others and every subset the agent could
    report. Ties count as truthful reporting being a best response.
    """

    types = _normalize_agent_types(framework, agent_types)
    cache: dict[ArgumentSet, ArgumentSet] = {}
    comparisons = 0

    for agent in _ordered(types):
        true_arguments = types[agent]
        own_reports = _powerset(true_arguments)
        for others in _other_report_profiles(types, agent):
            truthful_profile = dict(others)
            truthful_profile[agent] = true_arguments
            truthful_union = frozenset().union(*truthful_profile.values())
            truthful_outcome = _outcome_for_union(framework, truthful_union, cache)
            truthful_utility = len(true_arguments & truthful_outcome)

            for alternative in own_reports:
                comparisons += 1
                deviating_profile = dict(others)
                deviating_profile[agent] = alternative
                deviating_union = frozenset().union(*deviating_profile.values())
                deviating_outcome = _outcome_for_union(framework, deviating_union, cache)
                deviating_utility = len(true_arguments & deviating_outcome)

                if deviating_utility > truthful_utility:
                    violation = StrategyproofnessViolation(
                        agent=agent,
                        other_reports=MappingProxyType(dict(others)),
                        truthful_report=true_arguments,
                        profitable_report=alternative,
                        truthful_utility=truthful_utility,
                        profitable_utility=deviating_utility,
                        truthful_outcome=truthful_outcome,
                        profitable_outcome=deviating_outcome,
                    )
                    return Theorem53Result(
                        strategyproof=False,
                        comparisons_checked=comparisons,
                        counterexample=violation,
                    )

    return Theorem53Result(strategyproof=True, comparisons_checked=comparisons)


def find_odd_length_path(
    framework: ArgumentationFramework,
    source: Argument,
    target: Argument,
) -> tuple[Argument, ...] | None:
    """Find an odd-length directed walk from ``source`` to ``target``.

    A breadth-first search over ``(argument, length parity)`` states terminates
    even in cyclic graphs. It permits repeated vertices, including returning
    to ``source`` along an odd directed cycle.
    """

    # These calls validate both endpoints using the framework's public API.
    framework.attackers_of(source)
    framework.attackers_of(target)

    outgoing: dict[Argument, set[Argument]] = {
        argument: set() for argument in framework.arguments
    }
    for attacker, attacked in framework.attacks:
        outgoing[attacker].add(attacked)

    start = (source, 0)
    goal = (target, 1)
    parents: dict[tuple[Argument, int], tuple[Argument, int] | None] = {start: None}
    queue: deque[tuple[Argument, int]] = deque([start])

    while queue:
        argument, parity = queue.popleft()
        if (argument, parity) == goal:
            break
        next_parity = 1 - parity
        for attacked in _ordered(outgoing[argument]):
            next_state = (attacked, next_parity)
            if next_state not in parents:
                parents[next_state] = (argument, parity)
                queue.append(next_state)

    if goal not in parents:
        return None

    path_reversed: list[Argument] = []
    state: tuple[Argument, int] | None = goal
    while state is not None:
        path_reversed.append(state[0])
        state = parents[state]
    return tuple(reversed(path_reversed))


def check_theorem_5_4(
    framework: ArgumentationFramework,
    agent_types: AgentTypes,
) -> Theorem54Result:
    """Check Theorem 5.4's condition for every pair in every agent type.

    The condition holds exactly when no agent owns a pair ``(a, b)`` with an
    odd-length directed walk from ``a`` to ``b`` in the full framework.
    """

    types = _normalize_agent_types(framework, agent_types)
    pairs_checked = 0
    for agent in _ordered(types):
        arguments = _ordered(types[agent])
        for source in arguments:
            for target in arguments:
                pairs_checked += 1
                path = find_odd_length_path(framework, source, target)
                if path is not None:
                    return Theorem54Result(
                        condition_holds=False,
                        pairs_checked=pairs_checked,
                        witness=OddPathWitness(
                            agent=agent,
                            source=source,
                            target=target,
                            path=path,
                        ),
                    )

    return Theorem54Result(condition_holds=True, pairs_checked=pairs_checked)


__all__ = [
    "Agent",
    "AgentTypes",
    "BestResponseResult",
    "OddPathWitness",
    "StrategyproofnessViolation",
    "Theorem53Result",
    "Theorem54Result",
    "best_responses",
    "check_theorem_5_3",
    "check_theorem_5_4",
    "find_odd_length_path",
    "grounded_direct_argumentation_mechanism",
]
