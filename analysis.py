"""Explain why Theorem 5.4's condition can fail on a strategyproof mechanism.

Theorem 5.4 is sufficient but not necessary. For an instance whose condition
fails, every owned pair ``(a, b)`` with an odd path ``a`` ↪ ``b`` is a
potential incentive to hide ``a``. This module labels each such pair with the
structural reason it may be harmless and summarises the instance by the most
demanding reason present.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations

from argumentation import Argument, ArgumentSet, ArgumentationFramework
from strategic import AgentTypes, odd_path_witnesses


PAIR_REASONS = {
    "self_attacking_victim": "The target attacks itself, so it is never accepted.",
    "dead_victim": "The target is not accepted for any set of revealed arguments.",
    "odd_cycle": "The path is an odd cycle from an argument back to itself.",
    "direct_conflict": "The source directly attacks the target (the type is not conflict-free).",
    "indirect_path": "A live indirect odd path of length three or more.",
}

CATEGORIES = {
    "neutralised_indirect_path": (
        "Live indirect odd path neutralised (Example 5.11 type)",
        "Some agent has a length-3+ odd path to an argument that can be accepted, but "
        "another argument also defends the target, or breaking the chain costs the agent "
        "exactly as much as it frees, so hiding never strictly pays.",
    ),
    "direct_conflicts_only": (
        "Only direct conflicts between own arguments",
        "The only live odd paths are single attacks a ⇀ b inside one type. Hiding a can "
        "free b, but a is then lost, so the trade is at best one-for-one.",
    ),
    "odd_cycles_only": (
        "Only odd cycles back to the same argument",
        "The only live odd paths return to their starting argument through other agents' "
        "arguments; hiding that argument cannot increase its own acceptance.",
    ),
    "dead_victims_only": (
        "Every target can never be accepted",
        "Every odd path ends at an argument that is rejected for every revealed set, so "
        "nothing is lost by revealing the source.",
    ),
    "self_attacking_victims_only": (
        "Every target attacks itself",
        "Every odd path ends at a self-attacking argument, which grounded semantics never "
        "accepts, so nothing is lost by revealing the source.",
    ),
}

_CATEGORY_PRIORITY = (
    ("indirect_path", "neutralised_indirect_path"),
    ("direct_conflict", "direct_conflicts_only"),
    ("odd_cycle", "odd_cycles_only"),
    ("dead_victim", "dead_victims_only"),
    ("self_attacking_victim", "self_attacking_victims_only"),
)


@dataclass(frozen=True)
class PairExplanation:
    """Why one owned odd-path pair may be harmless."""

    agent: object
    source: Argument
    target: Argument
    path: tuple[Argument, ...]
    reason: str


@dataclass(frozen=True)
class ConditionFailureExplanation:
    """Instance-level category plus the per-pair reasons behind it."""

    category: str
    pairs: tuple[PairExplanation, ...]

    @property
    def title(self) -> str:
        return CATEGORIES[self.category][0]

    @property
    def description(self) -> str:
        return CATEGORIES[self.category][1]


def _subsets(values: Iterable[Argument]) -> Iterable[ArgumentSet]:
    ordered = sorted(values, key=repr)
    for size in range(len(ordered) + 1):
        for members in combinations(ordered, size):
            yield frozenset(members)


def ever_accepted(framework: ArgumentationFramework) -> ArgumentSet:
    """Arguments in the grounded extension of at least one induced subframework."""

    accepted: set[Argument] = set()
    for revealed in _subsets(framework.arguments):
        accepted |= framework.induced_subframework(revealed).grounded_extension()
    return frozenset(accepted)


def explain_condition_failure(
    framework: ArgumentationFramework,
    agent_types: AgentTypes,
) -> ConditionFailureExplanation | None:
    """Classify the odd-path pairs of an instance; ``None`` if the condition holds."""

    witnesses = odd_path_witnesses(framework, agent_types)
    if not witnesses:
        return None

    self_attacking = {source for source, target in framework.attacks if source == target}
    alive = ever_accepted(framework)
    pairs: list[PairExplanation] = []
    for witness in witnesses:
        if witness.target in self_attacking:
            reason = "self_attacking_victim"
        elif witness.target not in alive:
            reason = "dead_victim"
        elif witness.source == witness.target:
            reason = "odd_cycle"
        elif (witness.source, witness.target) in framework.attacks:
            reason = "direct_conflict"
        else:
            reason = "indirect_path"
        pairs.append(
            PairExplanation(witness.agent, witness.source, witness.target, witness.path, reason)
        )

    reasons = {pair.reason for pair in pairs}
    category = next(name for reason, name in _CATEGORY_PRIORITY if reason in reasons)
    return ConditionFailureExplanation(category, tuple(pairs))


__all__ = [
    "CATEGORIES",
    "PAIR_REASONS",
    "ConditionFailureExplanation",
    "PairExplanation",
    "ever_accepted",
    "explain_condition_failure",
]
