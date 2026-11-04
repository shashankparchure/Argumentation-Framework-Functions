"""A small, dependency-free engine for Dung argumentation frameworks.

Arguments may be any hashable Python values.  An attack ``(source, target)``
means that ``source`` attacks ``target``.  Frameworks and returned argument
sets are immutable from the caller's point of view.

Extension enumeration is exhaustive and therefore exponential in the number of
arguments.  This is suitable for the small frameworks used in the assignment.
"""

from __future__ import annotations

from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass
from itertools import combinations, product
from typing import TypeAlias


Argument: TypeAlias = Hashable
Attack: TypeAlias = tuple[Argument, Argument]
ArgumentSet: TypeAlias = frozenset[Argument]


class NoExtensionsError(ValueError):
    """Raised when acceptance status is requested for empty semantics."""


@dataclass(frozen=True)
class AcceptanceStatus:
    """Acceptance status of one argument under a chosen semantics.

    Skeptical and credulous acceptance intentionally overlap: an argument in
    every extension is also in at least one extension.
    """

    semantics: str
    skeptically_accepted: bool
    credulously_accepted: bool
    rejected: bool


class ArgumentationFramework:
    """A finite abstract argumentation framework ``(arguments, attacks)``.

    Args:
        arguments: Iterable of unique, hashable argument identifiers.
        attacks: Iterable of directed ``(attacker, target)`` pairs.

    Raises:
        TypeError: If an argument or attack endpoint is not hashable.
        ValueError: If an attack refers to an argument outside the framework.
    """

    __slots__ = ("_arguments", "_ordered_arguments", "_attacks", "_attackers", "_attacked")

    def __init__(
        self,
        arguments: Iterable[Argument],
        attacks: Iterable[Attack] = (),
    ) -> None:
        self._arguments = frozenset(arguments)
        self._ordered_arguments = tuple(sorted(self._arguments, key=repr))

        normalized_attacks: set[Attack] = set()
        for edge in attacks:
            try:
                endpoints = tuple(edge)
            except TypeError as error:
                raise ValueError(f"An attack must be a pair, got {edge!r}.") from error
            if len(endpoints) != 2:
                raise ValueError(f"An attack must contain exactly two arguments, got {edge!r}.")
            source, target = endpoints
            if source not in self._arguments or target not in self._arguments:
                raise ValueError(
                    f"Attack {source!r} -> {target!r} refers to an argument outside the framework."
                )
            normalized_attacks.add((source, target))

        self._attacks = frozenset(normalized_attacks)

        attackers: dict[Argument, set[Argument]] = {
            argument: set() for argument in self._arguments
        }
        attacked: dict[Argument, set[Argument]] = {
            argument: set() for argument in self._arguments
        }
        for source, target in self._attacks:
            attackers[target].add(source)
            attacked[source].add(target)

        self._attackers: Mapping[Argument, ArgumentSet] = {
            argument: frozenset(values) for argument, values in attackers.items()
        }
        self._attacked: Mapping[Argument, ArgumentSet] = {
            argument: frozenset(values) for argument, values in attacked.items()
        }

    @property
    def arguments(self) -> ArgumentSet:
        """The framework's arguments as an immutable set."""

        return self._arguments

    @property
    def attacks(self) -> frozenset[Attack]:
        """The framework's directed attacks as an immutable set."""

        return self._attacks

    def __len__(self) -> int:
        return len(self._arguments)

    def __repr__(self) -> str:
        return (
            f"ArgumentationFramework(arguments={self._arguments!r}, "
            f"attacks={self._attacks!r})"
        )

    def _validate_argument(self, argument: Argument) -> None:
        if argument not in self._arguments:
            raise ValueError(f"Unknown argument: {argument!r}.")

    def _validate_set(self, arguments: Iterable[Argument], name: str = "argument set") -> ArgumentSet:
        result = frozenset(arguments)
        unknown = result - self._arguments
        if unknown:
            raise ValueError(f"{name} contains unknown arguments: {unknown!r}.")
        return result

    def attackers_of(self, argument: Argument) -> ArgumentSet:
        """Return all arguments that attack ``argument``."""

        self._validate_argument(argument)
        return self._attackers[argument]

    def attacked_by(self, arguments: Iterable[Argument]) -> ArgumentSet:
        """Return the set ``S+`` of arguments attacked by a set ``S``."""

        source_set = self._validate_set(arguments)
        return frozenset(
            target
            for source in source_set
            for target in self._attacked[source]
        )

    def is_conflict_free(self, arguments: Iterable[Argument]) -> bool:
        """Return whether no argument in the set attacks another in the set."""

        candidate = self._validate_set(arguments)
        return self.attacked_by(candidate).isdisjoint(candidate)

    def defends(self, arguments: Iterable[Argument], argument: Argument) -> bool:
        """Return whether ``arguments`` attacks every attacker of ``argument``."""

        defenders = self._validate_set(arguments)
        self._validate_argument(argument)
        return self._attackers[argument].issubset(self.attacked_by(defenders))

    def characteristic_function(self, arguments: Iterable[Argument]) -> ArgumentSet:
        """Return ``F(S)``, the set of arguments defended by ``S``."""

        candidate = self._validate_set(arguments)
        attacked_by_candidate = self.attacked_by(candidate)
        return frozenset(
            argument
            for argument in self._ordered_arguments
            if self._attackers[argument].issubset(attacked_by_candidate)
        )

    def is_admissible(self, arguments: Iterable[Argument]) -> bool:
        """Return whether the set is conflict-free and defends itself."""

        candidate = self._validate_set(arguments)
        return (
            self.is_conflict_free(candidate)
            and candidate.issubset(self.characteristic_function(candidate))
        )

    def is_complete(self, arguments: Iterable[Argument]) -> bool:
        """Return whether the set is conflict-free and equals ``F(S)``."""

        candidate = self._validate_set(arguments)
        return (
            self.is_conflict_free(candidate)
            and candidate == self.characteristic_function(candidate)
        )

    def grounded_extension(self) -> ArgumentSet:
        """Compute the unique grounded extension by iterating ``F`` from empty."""

        current: ArgumentSet = frozenset()
        while True:
            following = self.characteristic_function(current)
            if following == current:
                return current
            current = following

    def complete_extensions(self) -> list[ArgumentSet]:
        """Enumerate all complete extensions in deterministic order."""

        results: list[ArgumentSet] = []
        for size in range(len(self._ordered_arguments) + 1):
            for members in combinations(self._ordered_arguments, size):
                candidate = frozenset(members)
                if self.is_complete(candidate):
                    results.append(candidate)
        return results

    def preferred_extensions(self) -> list[ArgumentSet]:
        """Return the inclusion-maximal complete extensions."""

        complete = self.complete_extensions()
        return [
            extension
            for extension in complete
            if not any(extension < other for other in complete)
        ]

    def stable_extensions(self) -> list[ArgumentSet]:
        """Return conflict-free sets that attack every argument outside them."""

        results: list[ArgumentSet] = []
        for size in range(len(self._ordered_arguments) + 1):
            for members in combinations(self._ordered_arguments, size):
                candidate = frozenset(members)
                if (
                    self.is_conflict_free(candidate)
                    and self.attacked_by(candidate) == self._arguments - candidate
                ):
                    results.append(candidate)
        return results

    def semi_stable_extensions(self) -> list[ArgumentSet]:
        """Return complete extensions with inclusion-maximal ranges ``E union E+``."""

        complete = self.complete_extensions()
        ranges = {
            extension: extension | self.attacked_by(extension)
            for extension in complete
        }
        return [
            extension
            for extension in complete
            if not any(ranges[extension] < other_range for other_range in ranges.values())
        ]

    def legal_labellings(self) -> list[dict[Argument, str]]:
        """Enumerate all legal total labellings using ``in/out/undec`` strings."""

        labels = ("in", "out", "undec")
        labellings: list[dict[Argument, str]] = []
        for values in product(labels, repeat=len(self._ordered_arguments)):
            labeling = dict(zip(self._ordered_arguments, values))
            in_arguments = frozenset(
                argument for argument, label in labeling.items() if label == "in"
            )
            out_arguments = frozenset(
                argument for argument, label in labeling.items() if label == "out"
            )

            is_legal = True
            for argument, label in labeling.items():
                attackers = self._attackers[argument]
                has_in_attacker = not attackers.isdisjoint(in_arguments)
                all_attackers_out = attackers.issubset(out_arguments)

                if label == "in":
                    is_legal = all_attackers_out
                elif label == "out":
                    is_legal = has_in_attacker
                else:
                    is_legal = not has_in_attacker and not all_attackers_out

                if not is_legal:
                    break

            if is_legal:
                labellings.append(labeling)
        return labellings

    def extensions_for(self, semantics: str = "grounded") -> list[ArgumentSet]:
        """Return extensions for ``grounded``, ``complete``, ``preferred``,
        ``stable``, or ``semi_stable`` semantics.
        """

        normalized = semantics.strip().lower().replace("-", "_").replace(" ", "_")
        if normalized == "grounded":
            return [self.grounded_extension()]
        if normalized == "complete":
            return self.complete_extensions()
        if normalized == "preferred":
            return self.preferred_extensions()
        if normalized == "stable":
            return self.stable_extensions()
        if normalized in {"semi_stable", "semistable"}:
            return self.semi_stable_extensions()
        raise ValueError(
            "Unknown semantics. Choose grounded, complete, preferred, stable, or semi-stable."
        )

    def acceptance_status(
        self,
        argument: Argument,
        semantics: str = "grounded",
    ) -> AcceptanceStatus:
        """Classify an argument under the selected extension semantics.

        Raises ``NoExtensionsError`` when the selected semantics has no
        extensions (possible with stable semantics), since acceptance status
        over an empty extension family is otherwise ambiguous.
        """

        self._validate_argument(argument)
        normalized = semantics.strip().lower().replace("-", "_").replace(" ", "_")
        extensions = self.extensions_for(normalized)
        if not extensions:
            raise NoExtensionsError(
                f"There are no {normalized} extensions for this framework."
            )

        credulous = any(argument in extension for extension in extensions)
        skeptical = all(argument in extension for extension in extensions)
        return AcceptanceStatus(
            semantics=normalized,
            skeptically_accepted=skeptical,
            credulously_accepted=credulous,
            rejected=not credulous,
        )

    def induced_subframework(self, arguments: Iterable[Argument]) -> ArgumentationFramework:
        """Return the framework induced by the selected arguments."""

        selected = self._validate_set(arguments, "induced argument set")
        return ArgumentationFramework(
            selected,
            (
                (source, target)
                for source, target in self._attacks
                if source in selected and target in selected
            ),
        )


__all__ = [
    "AcceptanceStatus",
    "Argument",
    "ArgumentationFramework",
    "ArgumentSet",
    "Attack",
    "NoExtensionsError",
]
