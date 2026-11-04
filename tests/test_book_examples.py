"""Argumentation engine checked against Chapter 5 of Weiss (ed.), Multiagent Systems.

Figure numbers and examples refer to that chapter (Rahwan, "Argumentation
among Agents"). Arguments αi are written ai.
"""

import unittest

from argumentation import ArgumentationFramework, NoExtensionsError


def sets(extensions):
    return sorted(sorted(extension) for extension in extensions)


# Figure 5.1: a3 -> a2 -> a1 <- a4 <- a5
FIGURE_5_1 = ArgumentationFramework(
    ["a1", "a2", "a3", "a4", "a5"],
    [("a2", "a1"), ("a4", "a1"), ("a3", "a2"), ("a5", "a4")],
)

# Figure 5.2: a1 <-> a2, a3 unattacked
FIGURE_5_2 = ArgumentationFramework(["a1", "a2", "a3"], [("a1", "a2"), ("a2", "a1")])

# Figure 5.3(i): b -> a, c -> b, d -> b, c <-> d, e -> d
FIGURE_5_3 = ArgumentationFramework(
    "abcde",
    [("b", "a"), ("c", "b"), ("d", "b"), ("c", "d"), ("d", "c"), ("e", "d")],
)


class Figure51(unittest.TestCase):
    af = FIGURE_5_1

    def test_defence_from_text(self):
        # "In Figure 5.1, for example, {α3, α5} defends α1."
        self.assertTrue(self.af.defends({"a3", "a5"}, "a1"))
        self.assertFalse(self.af.defends({"a3"}, "a1"))

    def test_conflict_free(self):
        self.assertTrue(self.af.is_conflict_free({"a1", "a3", "a5"}))
        self.assertFalse(self.af.is_conflict_free({"a1", "a2"}))

    def test_example_5_5_admissible_sets(self):
        for candidate in [set(), {"a3"}, {"a5"}, {"a3", "a5"}, {"a1", "a3", "a5"}]:
            with self.subTest(candidate=candidate):
                self.assertTrue(self.af.is_admissible(candidate))
        self.assertFalse(self.af.is_admissible({"a1"}))

    def test_example_5_6_characteristic_function(self):
        self.assertEqual(self.af.characteristic_function({"a3"}), {"a3", "a5"})
        self.assertEqual(self.af.characteristic_function({"a5"}), {"a3", "a5"})
        self.assertEqual(self.af.characteristic_function({"a3", "a5"}), {"a1", "a3", "a5"})

    def test_example_5_6_complete(self):
        self.assertFalse(self.af.is_complete({"a3", "a5"}))
        self.assertFalse(self.af.is_complete({"a3"}))
        self.assertTrue(self.af.is_complete({"a1", "a3", "a5"}))
        self.assertEqual(sets(self.af.complete_extensions()), [["a1", "a3", "a5"]])

    def test_grounded_iteration_from_text(self):
        # F^1(∅) = {α3, α5}; F^2(∅) = {α1, α3, α5} = F^3(∅)
        first = self.af.characteristic_function(set())
        self.assertEqual(first, {"a3", "a5"})
        second = self.af.characteristic_function(first)
        self.assertEqual(second, {"a1", "a3", "a5"})
        self.assertEqual(self.af.characteristic_function(second), second)
        self.assertEqual(self.af.grounded_extension(), {"a1", "a3", "a5"})

    def test_example_5_8_single_preferred(self):
        self.assertEqual(sets(self.af.preferred_extensions()), [["a1", "a3", "a5"]])
        self.assertEqual(sets(self.af.stable_extensions()), [["a1", "a3", "a5"]])
        self.assertEqual(sets(self.af.semi_stable_extensions()), [["a1", "a3", "a5"]])

    def test_unique_labelling(self):
        self.assertEqual(
            self.af.legal_labellings(),
            [{"a1": "in", "a2": "out", "a3": "in", "a4": "out", "a5": "in"}],
        )


class Figure52(unittest.TestCase):
    af = FIGURE_5_2

    def test_example_5_7_complete_extensions(self):
        self.assertEqual(
            sets(self.af.complete_extensions()),
            [["a1", "a3"], ["a2", "a3"], ["a3"]],
        )

    def test_grounded_is_minimal_complete(self):
        self.assertEqual(self.af.grounded_extension(), {"a3"})

    def test_example_5_8_two_preferred(self):
        self.assertEqual(sets(self.af.preferred_extensions()), [["a1", "a3"], ["a2", "a3"]])

    def test_stable_and_semi_stable(self):
        self.assertEqual(sets(self.af.stable_extensions()), [["a1", "a3"], ["a2", "a3"]])
        self.assertEqual(sets(self.af.semi_stable_extensions()), [["a1", "a3"], ["a2", "a3"]])

    def test_three_labellings_match_figure(self):
        labellings = self.af.legal_labellings()
        expected = [
            {"a1": "undec", "a2": "undec", "a3": "in"},  # L^G
            {"a1": "out", "a2": "in", "a3": "in"},       # L1
            {"a1": "in", "a2": "out", "a3": "in"},       # L2
        ]
        self.assertEqual(len(labellings), 3)
        for labelling in expected:
            self.assertIn(labelling, labellings)

    def test_labelling_in_sets_are_complete_extensions(self):
        in_sets = sets(
            {argument for argument, label in labelling.items() if label == "in"}
            for labelling in self.af.legal_labellings()
        )
        self.assertEqual(in_sets, sets(self.af.complete_extensions()))

    def test_definition_5_8_acceptance_status(self):
        a1_preferred = self.af.acceptance_status("a1", "preferred")
        self.assertFalse(a1_preferred.skeptically_accepted)
        self.assertTrue(a1_preferred.credulously_accepted)
        self.assertFalse(a1_preferred.rejected)

        a3_preferred = self.af.acceptance_status("a3", "preferred")
        self.assertTrue(a3_preferred.skeptically_accepted)

        a1_grounded = self.af.acceptance_status("a1", "grounded")
        self.assertTrue(a1_grounded.rejected)


class Figure53(unittest.TestCase):
    def test_grounded(self):
        self.assertEqual(FIGURE_5_3.grounded_extension(), {"a", "c", "e"})

    def test_preferred_equals_grounded(self):
        self.assertEqual(sets(FIGURE_5_3.preferred_extensions()), [["a", "c", "e"]])


class EdgeCases(unittest.TestCase):
    def test_self_attack_is_never_accepted(self):
        af = ArgumentationFramework(["a", "b"], [("a", "a"), ("a", "b")])
        self.assertEqual(af.grounded_extension(), frozenset())
        self.assertEqual(af.legal_labellings(), [{"a": "undec", "b": "undec"}])
        self.assertEqual(af.stable_extensions(), [])

    def test_no_stable_extension_raises(self):
        af = ArgumentationFramework(["a"], [("a", "a")])
        with self.assertRaises(NoExtensionsError):
            af.acceptance_status("a", "stable")

    def test_odd_cycle_has_empty_grounded_and_no_stable(self):
        af = ArgumentationFramework("abc", [("a", "b"), ("b", "c"), ("c", "a")])
        self.assertEqual(af.grounded_extension(), frozenset())
        self.assertEqual(af.stable_extensions(), [])
        self.assertEqual(sets(af.preferred_extensions()), [[]])

    def test_unknown_arguments_rejected(self):
        with self.assertRaises(ValueError):
            ArgumentationFramework(["a"], [("a", "b")])
        with self.assertRaises(ValueError):
            FIGURE_5_1.is_conflict_free({"zzz"})


if __name__ == "__main__":
    unittest.main()
