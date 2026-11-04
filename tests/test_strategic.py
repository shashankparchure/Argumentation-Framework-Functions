"""Strategic argumentation checked against Examples 5.10 and 5.11.

Two misprints in the book are corrected here, as noted in the assignment:
Example 5.10 swaps the utilities of y and z, and the argument that cancels the
indirect self-defeat after Example 5.11 is α6, not α5.
"""

import unittest

from analysis import explain_condition_failure
from argumentation import ArgumentationFramework
from experiments import _make_instance
from strategic import (
    best_responses,
    check_theorem_5_3,
    check_theorem_5_4,
    find_odd_length_path,
    find_odd_simple_path,
    grounded_direct_argumentation_mechanism,
    odd_path_witnesses,
)


EXAMPLE_5_10 = ArgumentationFramework(
    ["a1", "a2", "a3", "a4", "a5"],
    [("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")],
)
TYPES_5_10 = {"x": {"a1", "a4", "a5"}, "y": {"a2"}, "z": {"a3"}}

EXAMPLE_5_11 = ArgumentationFramework(
    ["a1", "a2", "a3", "a4", "a5", "a6"],
    [("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5"), ("a6", "a3")],
)
TYPES_5_11 = {"x": {"a1", "a4", "a5", "a6"}, "y": {"a2"}, "z": {"a3"}}


def utilities(outcome, types):
    return {agent: len(outcome & set(arguments)) for agent, arguments in types.items()}


class Example510(unittest.TestCase):
    def test_truthful_outcome_and_corrected_utilities(self):
        outcome = grounded_direct_argumentation_mechanism(EXAMPLE_5_10, TYPES_5_10)
        self.assertEqual(outcome, {"a1", "a3"})
        # The book prints u_y = 1 and u_z = 0; with A_y = {a2}, A_z = {a3} it is the reverse.
        self.assertEqual(utilities(outcome, TYPES_5_10), {"x": 1, "y": 0, "z": 1})

    def test_reports_may_be_a_list(self):
        outcome = grounded_direct_argumentation_mechanism(
            EXAMPLE_5_10, [{"a4", "a5"}, {"a2"}, {"a3"}]
        )
        self.assertEqual(outcome, {"a2", "a4", "a5"})

    def test_hiding_a1_gives_x_two(self):
        reports = {"x": {"a4", "a5"}, "y": {"a2"}, "z": {"a3"}}
        outcome = grounded_direct_argumentation_mechanism(EXAMPLE_5_10, reports)
        self.assertEqual(outcome, {"a2", "a4", "a5"})
        self.assertEqual(utilities(outcome, TYPES_5_10)["x"], 2)

    def test_best_response_of_x(self):
        result = best_responses(EXAMPLE_5_10, TYPES_5_10, "x", {"y": {"a2"}, "z": {"a3"}})
        self.assertEqual(result.utility, 2)
        self.assertEqual(result.best_reports, (frozenset({"a4", "a5"}),))
        self.assertEqual(len(result.utilities_by_report), 8)

    def test_truth_weakly_dominates_for_y_and_z(self):
        for agent, others in [("y", {"x": {"a1", "a4", "a5"}, "z": {"a3"}}),
                              ("z", {"x": {"a1", "a4", "a5"}, "y": {"a2"}})]:
            with self.subTest(agent=agent):
                result = best_responses(EXAMPLE_5_10, TYPES_5_10, agent, others)
                self.assertIn(frozenset(TYPES_5_10[agent]), result.best_reports)

    def test_not_strategyproof(self):
        result = check_theorem_5_3(EXAMPLE_5_10, TYPES_5_10)
        self.assertFalse(result.strategyproof)
        violation = result.counterexample
        self.assertEqual(violation.agent, "x")
        self.assertGreater(violation.profitable_utility, violation.truthful_utility)

    def test_theorem_5_4_witness(self):
        result = check_theorem_5_4(EXAMPLE_5_10, TYPES_5_10)
        self.assertFalse(result.condition_holds)
        self.assertEqual(result.witness.path, ("a1", "a2", "a3", "a4"))


class Example511(unittest.TestCase):
    def test_truthful_outcome(self):
        outcome = grounded_direct_argumentation_mechanism(EXAMPLE_5_11, TYPES_5_11)
        self.assertEqual(outcome, {"a1", "a4", "a5", "a6"})

    def test_strategyproof_although_condition_fails(self):
        self.assertTrue(check_theorem_5_3(EXAMPLE_5_11, TYPES_5_11).strategyproof)
        self.assertFalse(check_theorem_5_4(EXAMPLE_5_11, TYPES_5_11).condition_holds)

    def test_a6_not_a5_cancels_the_self_defeat(self):
        without_a6 = {"x": {"a1", "a4", "a5"}, "y": {"a2"}, "z": {"a3"}}
        outcome = grounded_direct_argumentation_mechanism(EXAMPLE_5_11, without_a6)
        self.assertNotIn("a4", outcome)
        self.assertNotIn("a5", outcome)

    def test_explained_as_neutralised_indirect_path(self):
        explanation = explain_condition_failure(EXAMPLE_5_11, TYPES_5_11)
        self.assertEqual(explanation.category, "neutralised_indirect_path")


class OddPaths(unittest.TestCase):
    def test_walk_and_simple_readings_differ_on_odd_cycle_through_self_loop(self):
        # a -> b -> b -> a is an odd walk; the only simple cycle a -> b -> a is even.
        af = ArgumentationFramework("ab", [("a", "b"), ("b", "a"), ("b", "b")])
        self.assertEqual(find_odd_length_path(af, "a", "a"), ("a", "b", "b", "a"))
        self.assertIsNone(find_odd_simple_path(af, "a", "a"))

    def test_even_cycle_has_no_odd_path_back(self):
        af = ArgumentationFramework("abcd", [("a", "b"), ("b", "c"), ("c", "d"), ("d", "a")])
        self.assertIsNone(find_odd_length_path(af, "a", "a"))
        self.assertIsNone(find_odd_length_path(af, "a", "c"))
        self.assertEqual(find_odd_length_path(af, "a", "d"), ("a", "b", "c", "d"))

    def test_self_attack_violates_condition_under_both_readings(self):
        af = ArgumentationFramework("ab", [("a", "a")])
        types = {"x": {"a"}, "y": {"b"}}
        for reading in ("walk", "simple"):
            with self.subTest(reading=reading):
                self.assertFalse(check_theorem_5_4(af, types, reading=reading).condition_holds)

    def test_all_witnesses(self):
        witnesses = odd_path_witnesses(EXAMPLE_5_10, TYPES_5_10)
        self.assertEqual(
            {(w.agent, w.source, w.target) for w in witnesses},
            {("x", "a1", "a4"), ("x", "a1", "a5")},
        )

    def test_condition_holds_on_even_paths_only(self):
        af = ArgumentationFramework("abc", [("a", "b"), ("b", "c")])
        types = {"x": {"a", "c"}, "y": {"b"}}
        self.assertTrue(check_theorem_5_4(af, types).condition_holds)
        self.assertTrue(check_theorem_5_3(af, types).strategyproof)
        self.assertIsNone(explain_condition_failure(af, types))


class Generator(unittest.TestCase):
    def test_same_seed_same_graph_without_self_attacks(self):
        for seed in range(50):
            with_self = _make_instance(0.35, seed, allow_self_attacks=True)
            without_self = _make_instance(0.35, seed, allow_self_attacks=False)
            self.assertEqual(with_self[0], without_self[0])
            self.assertEqual(with_self[2], without_self[2])
            self.assertEqual(
                [edge for edge in with_self[1] if edge[0] != edge[1]], without_self[1]
            )

    def test_instance_shape(self):
        for seed in range(50):
            arguments, attacks, types = _make_instance(0.25, seed)
            self.assertIn(len(arguments), (6, 7, 8))
            self.assertEqual(set(types), {"x", "y", "z"})
            self.assertTrue(all(types.values()))
            self.assertEqual(set().union(*types.values()), set(arguments))


if __name__ == "__main__":
    unittest.main()
