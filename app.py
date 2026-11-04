"""Interactive demonstration for Assignment 3 (run with ``streamlit run app.py``).

Every number shown is computed by ``argumentation.py``, ``strategic.py`` and
``analysis.py``; the app and ``ui.py`` contain presentation code only.
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import streamlit as st

import ui
from analysis import CATEGORIES, PAIR_REASONS, explain_condition_failure
from argumentation import ArgumentationFramework, NoExtensionsError
from experiments import _make_instance
from strategic import (
    best_responses,
    check_theorem_5_3,
    grounded_direct_argumentation_mechanism,
    odd_path_witnesses,
)

RESULTS = Path(__file__).resolve().parent / "results"
DATASETS = {
    "With self-attacks (default run)": RESULTS,
    "Without self-attacks": RESULTS / "no_self_attacks",
}
AGENTS = ("x", "y", "z")
SEMANTICS = ("grounded", "complete", "preferred", "stable", "semi-stable")
EXHAUSTIVE_LIMIT = 12

TAB_SEMANTICS = "Semantics"
TAB_MECHANISM = "Strategic mechanism"
TAB_EXPERIMENTS = "Experiments"
TAB_NOTES = "Notes"

PRESETS = {
    "Figure 5.1 · simple argument graph": dict(
        arguments=["a1", "a2", "a3", "a4", "a5"],
        attacks=[("a2", "a1"), ("a4", "a1"), ("a3", "a2"), ("a5", "a4")],
        owners=None,
        note="α1 has defeaters α2 and α4, which are defeated by α3 and α5. "
        "Grounded = preferred = stable = {α1, α3, α5} (Examples 5.5, 5.6, 5.8).",
    ),
    "Figure 5.2 · three labellings": dict(
        arguments=["a1", "a2", "a3"],
        attacks=[("a1", "a2"), ("a2", "a1")],
        owners=None,
        note="Three complete extensions {α3}, {α1, α3}, {α2, α3} (Example 5.7); "
        "grounded {α3}; two preferred extensions (Example 5.8).",
    ),
    "Figure 5.3 · dispute-tree graph": dict(
        arguments=["a", "b", "c", "d", "e"],
        attacks=[("b", "a"), ("c", "b"), ("d", "b"), ("c", "d"), ("d", "c"), ("e", "d")],
        owners=None,
        note="The graph behind the dispute tree of Example 5.9. e is unattacked, so d is out, "
        "c is in, b is out and a is in.",
    ),
    "Example 5.10 · hiding pays": dict(
        arguments=["a1", "a2", "a3", "a4", "a5"],
        attacks=[("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5")],
        owners={"a1": "x", "a2": "y", "a3": "z", "a4": "x", "a5": "x"},
        note="Truthful outcome {α1, α3}: x gets 1, y gets 0, z gets 1 (the book swaps y and z). "
        "Hiding α1 gives {α2, α4, α5}, so x gets 2.",
    ),
    "Example 5.11 · condition fails, still strategyproof": dict(
        arguments=["a1", "a2", "a3", "a4", "a5", "a6"],
        attacks=[("a1", "a2"), ("a2", "a3"), ("a3", "a4"), ("a3", "a5"), ("a6", "a3")],
        owners={"a1": "x", "a2": "y", "a3": "z", "a4": "x", "a5": "x", "a6": "x"},
        note="α1 ↪ α4 and α1 ↪ α5, yet truth-telling is dominant for x because α6 defeats α3. "
        "(The book says α5 here; it is α6.)",
    ),
}


# --------------------------------------------------------------------------- helpers

def fmt(arguments) -> str:
    return "{" + ", ".join(map(str, sorted(arguments, key=ui.sort_key))) + "}"


def subsets(values):
    ordered = sorted(values, key=ui.sort_key)
    for size in range(len(ordered) + 1):
        for members in combinations(ordered, size):
            yield frozenset(members)


@st.cache_data
def load_json(path: str):
    file = Path(path)
    return json.loads(file.read_text(encoding="utf-8")) if file.exists() else None


def grounded_labelling(af: ArgumentationFramework) -> dict:
    grounded = af.grounded_extension()
    out = af.attacked_by(grounded)
    return {a: "in" if a in grounded else "out" if a in out else "undec" for a in af.arguments}


def card(name: str):
    return st.container(border=True, key=f"card-{name}")


def parse_custom(attack_text: str, owner_text: str):
    attacks, arguments = [], []
    for line in attack_text.replace(",", "\n").splitlines():
        line = line.strip()
        if not line:
            continue
        if "->" not in line:
            raise ValueError(f"Cannot read attack '{line}'. Use the form a -> b.")
        source, target = (part.strip() for part in line.split("->", 1))
        attacks.append((source, target))
        arguments += [source, target]
    owners = {}
    for line in owner_text.splitlines():
        if ":" not in line:
            continue
        agent, members = line.split(":", 1)
        agent = agent.strip().lower()
        if agent not in AGENTS:
            raise ValueError(f"Unknown agent '{agent}'. Use x, y or z.")
        for argument in members.replace(",", " ").split():
            owners[argument] = agent
            arguments.append(argument)
    ordered = list(dict.fromkeys(arguments))
    return ordered, attacks, owners or None


# --------------------------------------------------------------------------- framework source

def load_case_into_lab(dataset: str, case_id: str) -> None:
    st.session_state["source"] = "Experiment case"
    st.session_state["case_dataset"] = dataset
    st.session_state["case_id"] = case_id
    st.session_state["tab"] = TAB_MECHANISM


def all_cases(dataset: str) -> dict:
    data = load_json(str(DATASETS[dataset] / "interesting_cases.json")) or {}
    cases = {}
    for group, records in data.items():
        for record in records:
            record = dict(record)
            record["group"] = group
            cases[record["instance_id"]] = record
    return cases


def choose_framework():
    ui.brand()
    sources = list(PRESETS) + ["Random instance", "Experiment case", "Custom framework"]
    source = st.sidebar.selectbox("Framework", sources, key="source")

    if source in PRESETS:
        preset = PRESETS[source]
        return source, preset["arguments"], preset["attacks"], preset["owners"], preset["note"]

    if source == "Random instance":
        p = st.sidebar.select_slider("Attack probability p", [0.15, 0.25, 0.35], value=0.25)
        seed = st.sidebar.number_input("Instance seed", 0, 10**9, 7, step=1)
        allow_self = st.sidebar.toggle("Allow self-attacks", value=True)
        arguments, attacks, types = _make_instance(p, int(seed), allow_self)
        owners = {a: agent for agent, members in types.items() for a in members}
        note = (
            f"Generated exactly like the experiment: {len(arguments)} arguments, "
            f"each ordered pair attacked with probability {p}, arguments split among x, y, z."
        )
        return f"random:{p}:{seed}:{allow_self}", arguments, attacks, owners, note

    if source == "Experiment case":
        dataset = st.sidebar.selectbox("Dataset", list(DATASETS), key="case_dataset")
        cases = all_cases(dataset)
        if not cases:
            st.sidebar.warning("Run `python experiments.py` first.")
            return "empty", [], [], None, ""
        ids = sorted(cases)
        if st.session_state.get("case_id") not in cases:
            st.session_state["case_id"] = ids[0]
        case_id = st.sidebar.selectbox("Instance", ids, key="case_id")
        case = cases[case_id]
        owners = {a: agent for agent, members in case["agent_types"].items() for a in members}
        attacks = [tuple(edge) for edge in case["attacks"]]
        if case["group"] == "condition_false_but_strategyproof":
            note = f"Condition fails but strategyproof · {case['explanation']['title']}."
        else:
            note = "Condition holds but NOT strategyproof (a counterexample to Theorem 5.4)."
        return f"case:{dataset}:{case_id}", case["arguments"], attacks, owners, note

    st.sidebar.caption("One attack per line (`a -> b`). Owners are optional.")
    attack_text = st.sidebar.text_area(
        "Attacks", "a1 -> a2\na2 -> a3\na3 -> a4\na3 -> a5\na6 -> a3", height=150
    )
    owner_text = st.sidebar.text_area("Owners", "x: a1 a4 a5 a6\ny: a2\nz: a3", height=90)
    try:
        arguments, attacks, owners = parse_custom(attack_text, owner_text)
    except ValueError as error:
        st.sidebar.error(str(error))
        return "empty", [], [], None, ""
    return f"custom:{attack_text}:{owner_text}", arguments, attacks, owners, "Custom framework."


# --------------------------------------------------------------------------- tab 1: semantics

def semantics_tab(af: ArgumentationFramework, fw_id: str, owners) -> None:
    arguments = sorted(af.arguments, key=ui.sort_key)
    if len(arguments) > EXHAUSTIVE_LIMIT:
        st.warning(f"Exhaustive semantics are limited to {EXHAUSTIVE_LIMIT} arguments.")
        return

    labellings = af.legal_labellings()
    grounded = af.grounded_extension()
    complete = af.complete_extensions()
    preferred = af.preferred_extensions()
    stable = af.stable_extensions()
    semi = af.semi_stable_extensions()

    def tags(in_set):
        found = ["complete"]
        if in_set == grounded:
            found.append("grounded")
        if in_set in preferred:
            found.append("preferred")
        if in_set in stable:
            found.append("stable")
        if in_set in semi:
            found.append("semi-stable")
        return found

    options = ["Grounded labelling"] + [
        f"Labelling {i + 1}: in = {fmt(a for a, l in lab.items() if l == 'in')}"
        for i, lab in enumerate(labellings)
    ]

    top_left, top_right = st.columns([1.55, 1], gap="medium")
    with top_left, card("sem-graph"):
        ui.section("Argument graph", "Definition 5.1",
                   "Hover a node to see its attacks. Pick a labelling to recolour the graph.")
        view = st.selectbox("Colour the graph by", options, key=f"view::{fw_id}",
                            label_visibility="collapsed")
        selected = st.session_state.get(f"S::{fw_id}", [])
        labels = (
            grounded_labelling(af)
            if view == options[0]
            else labellings[options.index(view) - 1]
        )
        ui.graph("semantics", arguments, sorted(af.attacks), owners=owners, labels=labels,
                 selected=selected)

    with top_right, card("sem-steps"):
        ui.section("Grounded extension, step by step", "Definition 5.3 · least fixed point",
                   "Apply the characteristic function F to ∅ until nothing changes. "
                   "Newly added arguments glow green.")
        steps, current, index = [], frozenset(), 1
        while True:
            following = af.characteristic_function(current)
            fixed = following == current
            sup = "".join("⁰¹²³⁴⁵⁶⁷⁸⁹"[int(d)] for d in str(index))
            tag = ui.chip("fixed point", "good", dot=True) if fixed else ""
            steps.append(
                f'<div class="step{" fixed" if fixed else ""}" style="--r:{index - 1}">'
                f'<span class="k">F{sup}(∅)</span>{ui.set_html(following, following - current)}'
                f'<span class="tag">{tag}</span></div>'
            )
            if fixed:
                break
            current, index = following, index + 1
        ui.render(f'<div class="steps">{"".join(steps)}</div>')
        ui.render(f'<div class="sec-c" style="margin-top:.7rem">Grounded extension = '
                  f'{ui.set_html(grounded, grounded, tone="in")}</div>')

    left, right = st.columns(2, gap="medium")
    with left:
        with card("sem-set"):
            ui.section("Test a set S", "Definitions 5.2 – 5.4",
                       "S is drawn with a dashed halo on the graph above.")
            selected = st.multiselect("Arguments in S", arguments, key=f"S::{fw_id}",
                                      placeholder="Choose arguments")
            S = frozenset(selected)
            F_S = af.characteristic_function(S)
            checks = [
                ("Conflict-free", af.is_conflict_free(S)),
                ("Admissible", af.is_admissible(S)),
                ("Complete", af.is_complete(S)),
            ]
            ui.tiles([(name, "yes" if ok else "no", "", "good" if ok else "bad") for name, ok in checks])
            alpha = st.selectbox("Does S defend α?", arguments, key=f"alpha::{fw_id}")
            attackers = af.attackers_of(alpha)
            defended = af.defends(S, alpha)
            ui.callout(
                "good" if defended else "bad",
                f"<b>{'S defends' if defended else 'S does not defend'} {ui.arg_html(alpha)}.</b> "
                f"Attackers of {ui.arg_html(alpha)}: {ui.set_html(attackers)}; "
                f"S attacks {ui.set_html(af.attacked_by(S) & attackers)} of them.<br>"
                f"<b>F(S)</b> = {ui.set_html(F_S)} — every argument S defends (Definition 5.3).",
            )

    with right:
        with card("sem-ext"):
            ui.section("Extensions", "Definitions 5.4 – 5.5")
            rows = [
                ("grounded", [grounded]), ("complete", complete), ("preferred", preferred),
                ("stable", stable), ("semi-stable", semi),
            ]
            ui.table(["semantics", "extensions"], [
                [f"<b>{name}</b>", " ".join(ui.set_html(e) for e in exts) or ui.chip("none", "bad")]
                for name, exts in rows
            ])

    with card("sem-lab"):
        ui.section(f"Legal labellings ({len(labellings)})", "Definition 5.6 · Table 5.1",
                   "Every legal labelling is a complete extension. grounded = maximal undec · "
                   "preferred = maximal in · semi-stable = minimal undec · stable = no undec")
        rows = []
        for index, labelling in enumerate(labellings, 1):
            in_set = frozenset(a for a, l in labelling.items() if l == "in")
            rows.append(
                [f'<span class="num">{index}</span>']
                + [ui.label_html(labelling[a]) for a in arguments]
                + [" ".join(ui.chip(t, "info" if t != "complete" else "muted") for t in tags(in_set))]
            )
        ui.table(["#"] + [str(a) for a in arguments] + ["matches"], rows, max_height=330)

    with card("sem-acc"):
        ui.section("Acceptance status", "Definition 5.8",
                   "skeptical = in every extension · credulous = in at least one · "
                   "rejected = in none")
        tone = {"skeptical": "good", "credulous": "info", "rejected": "muted"}
        rows = []
        for argument in arguments:
            row = [f"<b>{ui.arg_html(argument)}</b>"]
            for semantics in SEMANTICS:
                try:
                    status = af.acceptance_status(argument, semantics)
                except NoExtensionsError:
                    row.append(ui.chip("no extension", "bad"))
                    continue
                name = ("skeptical" if status.skeptically_accepted
                        else "credulous" if status.credulously_accepted else "rejected")
                row.append(ui.chip(name, tone[name]))
            rows.append(row)
        ui.table(["argument"] + list(SEMANTICS), rows)


# --------------------------------------------------------------------------- tab 2: mechanism

def owner_editor(arguments, default_owners, fw_id):
    with st.expander("Agent types — who owns which argument", expanded=default_owners is None):
        st.caption("Change an owner to see how strategyproofness depends on the type profile.")
        columns = st.columns(min(len(arguments), 8) or 1)
        owners = {}
        for index, argument in enumerate(arguments):
            default = (default_owners or {}).get(argument, AGENTS[index % 3])
            key = f"own::{fw_id}::{argument}"
            if key not in st.session_state:
                st.session_state[key] = default
            owners[argument] = columns[index % len(columns)].selectbox(
                str(argument), AGENTS, key=key
            )
    return owners


def set_reports(fw_id: str, arguments, revealed) -> None:
    for argument in arguments:
        st.session_state[f"rep::{fw_id}::{argument}"] = argument in revealed


def mechanism_tab(af: ArgumentationFramework, fw_id: str, default_owners) -> None:
    arguments = sorted(af.arguments, key=ui.sort_key)
    if len(arguments) > EXHAUSTIVE_LIMIT:
        st.warning(f"Exhaustive strategic checks are limited to {EXHAUSTIVE_LIMIT} arguments.")
        return
    owners = owner_editor(arguments, default_owners, fw_id)
    types = {agent: frozenset(a for a in arguments if owners[a] == agent) for agent in AGENTS}
    types = {agent: members for agent, members in types.items() if members}

    for argument in arguments:
        st.session_state.setdefault(f"rep::{fw_id}::{argument}", True)

    theorem53 = check_theorem_5_3(af, types)
    witnesses = odd_path_witnesses(af, types)

    graph_col, reports_col = st.columns([1.55, 1], gap="medium")
    outcome_col, theorem_col = st.columns(2, gap="medium")

    with reports_col, card("mech-reports"):
        ui.section("Reports", "Definition 5.21 · direct mechanism",
                   "Tick = revealed. Agents can only hide arguments, never invent them.")
        report_columns = st.columns(len(types))
        for column, (agent, members) in zip(report_columns, types.items()):
            column.html(ui.agent_chip(agent, short=True))
            for argument in sorted(members, key=ui.sort_key):
                column.checkbox(str(argument), key=f"rep::{fw_id}::{argument}")
        st.button(
            "↺  Everyone tells the truth",
            help="Every agent reveals its whole type.",
            on_click=set_reports,
            args=(fw_id, arguments, set(arguments)),
            width="stretch",
        )
        if theorem53.counterexample is not None:
            violation = theorem53.counterexample
            profitable = set(violation.profitable_report).union(*violation.other_reports.values())
            st.button(
                f"⚡  Show agent {violation.agent}'s profitable lie",
                help="Load the profile where hiding arguments pays, found by the Theorem 5.3 check.",
                on_click=set_reports,
                args=(fw_id, arguments, profitable),
                type="primary",
                width="stretch",
            )

    reports = {
        agent: frozenset(a for a in members if st.session_state[f"rep::{fw_id}::{a}"])
        for agent, members in types.items()
    }
    revealed = frozenset().union(*reports.values())
    outcome = grounded_direct_argumentation_mechanism(af, reports)
    truthful_outcome = grounded_direct_argumentation_mechanism(af, types)
    labels = grounded_labelling(af.induced_subframework(revealed))

    path = ()
    with theorem_col:
        with card("mech-54"):
            ui.section("Odd paths inside one type", "Theorem 5.4 · sufficient condition")
            if witnesses:
                choices = ["none"] + [
                    f"{w.agent}: {' → '.join(map(str, w.path))} (length {w.length})"
                    for w in witnesses
                ]
                picked = st.selectbox(
                    f"Condition fails — {len(witnesses)} owned pair(s) with an odd path. "
                    "Highlight one on the graph:",
                    choices,
                    index=1,
                    key=f"witness::{fw_id}",
                )
                if picked != "none":
                    path = witnesses[choices.index(picked) - 1].path
            else:
                ui.callout("good", "<b>Condition holds.</b> No agent owns α, β with an odd path "
                           "α ↪ β, so Theorem 5.4 guarantees strategyproofness.")

        with card("mech-53"):
            ui.section("Exhaustive strategyproofness check", "Theorem 5.3")
            if theorem53.strategyproof:
                ui.callout("good", f"<b>Strategyproof.</b> Truthful reporting is a best response for "
                           f"every agent against every combination of the others' reports "
                           f"({theorem53.comparisons_checked:,} comparisons).")
                if witnesses:
                    explanation = explain_condition_failure(af, types)
                    ui.callout("info", f"<b>Why, although Theorem 5.4's condition fails:</b> "
                               f"{ui.esc(explanation.title)}. {ui.esc(explanation.description)}")
            else:
                v = theorem53.counterexample
                others = ", ".join(f"{a} reveals {ui.set_html(r)}" for a, r in v.other_reports.items())
                ui.callout(
                    "bad",
                    f"<b>Not strategyproof.</b> When {others}, agent <b>{v.agent}</b> gets "
                    f"{v.truthful_utility} by revealing {ui.set_html(v.truthful_report)} but "
                    f"<b>{v.profitable_utility}</b> by revealing only {ui.set_html(v.profitable_report)}."
                    f"<br>Outcome {ui.set_html(v.truthful_outcome)} → {ui.set_html(v.profitable_outcome)}",
                )

    hidden = set(arguments) - revealed
    with graph_col, card("mech-graph"):
        ui.section("Revealed graph", "Grounded extension of the reports",
                   "Withheld arguments fade out with a dashed ring; the labelling is recomputed live.")
        ui.graph("mechanism", arguments, sorted(af.attacks), owners=owners, labels=labels,
                 hidden=hidden, path=path)

    with outcome_col, card("mech-outcome"):
        ui.section("Mechanism outcome and utilities", "Definition 5.22",
                   "Utility uᵢ = |Aᵢ ∩ outcome|, counted against the agent's true type.")
        ui.callout(
            "info",
            f"<b>Outcome</b> {ui.set_html(outcome, outcome, tone='in')}<br>"
            f"Truthful outcome {ui.set_html(truthful_outcome)}"
            + (f"<br>{len(hidden)} argument(s) withheld." if hidden else ""),
        )
        rows = []
        for agent, members in types.items():
            utility = len(members & outcome)
            truthful = len(members & truthful_outcome)
            rows.append([
                ui.agent_chip(agent),
                ui.set_html(members),
                ui.set_html(reports[agent]),
                ui.set_html(members & outcome, members & outcome, tone="in"),
                f'<span class="num">{utility}</span>',
                ui.delta_html(utility - truthful),
            ])
        ui.table(["agent", "true type Aᵢ", "reported", "accepted", "utility", "vs truth"], rows)

    with card("mech-br"):
        ui.section("Best-response explorer", "Every report an agent could make")
        agent = st.segmented_control(
            "Agent", list(types), default=list(types)[0], key=f"br_agent::{fw_id}",
            format_func=lambda a: f"agent {a}",
        ) or list(types)[0]
        others = {other: reports[other] for other in types if other != agent}
        result = best_responses(af, types, agent, others)
        st.caption(
            f"Every subset agent {agent} could reveal, with the other agents' reports fixed as "
            f"ticked above. Best utility = {result.utility}."
        )
        rows, best_rows = [], []
        for index, report in enumerate(subsets(types[agent])):
            is_best = report in result.best_reports
            if is_best:
                best_rows.append(index)
            rows.append([
                ui.set_html(report),
                ui.set_html(result.outcomes_by_report[report]),
                f'<span class="num">{result.utilities_by_report[report]}</span>',
                ui.chip("★ best", "good") if is_best else "",
                ui.chip("truthful", "info") if report == types[agent] else "",
            ])
        ui.table(["report", "outcome", "utility", "", ""], rows, highlight=best_rows, max_height=420)


# --------------------------------------------------------------------------- tab 3: experiments

def experiments_tab() -> None:
    summaries = {
        name: load_json(str(path / "experiment_summary.json")) for name, path in DATASETS.items()
    }
    if not any(summaries.values()):
        st.info("No results yet. Run `python experiments.py` and "
                "`python experiments.py --no-self-attacks`.")
        return

    with card("exp-q1"):
        ui.section("How often is the mechanism strategyproof?", "Question 1",
                   "3 agents · 6–8 arguments · 1000 random instances per p. Denser graphs give agents "
                   "more chains to break, so manipulation becomes common.")
        panels = []
        for name, summary in summaries.items():
            if summary:
                panels.append((name, [
                    (r["p"], r["strategyproof_fraction"], r["strategyproof_ci95"][0],
                     r["strategyproof_ci95"][1], r["theorem54_condition_fraction"])
                    for r in summary["results"]
                ]))
        ui.q1_chart(panels)

    dataset = st.segmented_control("Dataset", list(DATASETS), default=list(DATASETS)[0],
                                   key="exp_dataset") or list(DATASETS)[0]
    summary = summaries[dataset]
    if not summary:
        st.info("This dataset has not been generated yet.")
        return
    totals = summary["totals"]

    with card("exp-table"):
        ui.section("Per-probability results", dataset)
        ui.table(
            ["p", "strategyproof", "95 % CI", "self-attack instances", "Thm 5.4 holds",
             "Q2 · holds, not SP", "Q3 · fails, SP"],
            [
                [
                    f'<span class="num">{r["p"]:.2f}</span>',
                    f'<span class="num">{r["strategyproof_count"]}</span> '
                    f'<span style="color:var(--muted)">({r["strategyproof_fraction"]:.1%})</span>',
                    f'{r["strategyproof_ci95"][0]:.1%} – {r["strategyproof_ci95"][1]:.1%}',
                    f'<span class="num">{r.get("self_attack_instances", "—")}</span>',
                    f'<span class="num">{r["theorem54_condition_count"]}</span>',
                    ui.chip(str(r["condition_true_but_not_strategyproof"]),
                            "good" if r["condition_true_but_not_strategyproof"] == 0 else "bad"),
                    f'<span class="num">{r["condition_false_but_strategyproof"]}</span>',
                ]
                for r in summary["results"]
            ],
        )
        if totals.get("self_attack_instances"):
            ui.callout(
                "warn",
                f"<b>{totals['self_attack_instances']:,} of {totals['instances']:,}</b> instances "
                "contain a self-attacking argument. Its owner's type is then not conflict-free, so "
                "Theorem 5.4's condition fails for that reason alone. Compare with the dataset "
                "without self-attacks.",
            )

    with card("exp-q2"):
        ui.section("Does the condition ever hold without strategyproofness?", "Question 2",
                   "Theorem 5.4 predicts never — the counts below should all be zero.")
        stress = load_json(str(RESULTS / "stress_test.json"))
        items = [
            ("condition holds · this run", totals["theorem54_condition"], "instances", "info"),
            ("of those, not strategyproof", totals["condition_true_but_not_strategyproof"],
             "counterexamples", "good" if totals["condition_true_but_not_strategyproof"] == 0 else "bad"),
        ]
        if stress:
            items += [
                ("stress test · condition holds", stress["condition_holding_instances"],
                 f"kept from {stress['instances_sampled']:,} sampled", "info"),
                ("of those, not strategyproof", stress["not_strategyproof"], "counterexamples",
                 "good" if stress["not_strategyproof"] == 0 else "bad"),
            ]
        ui.tiles(items)
        if not stress:
            st.caption("Run `python experiments.py --stress 3000` for a larger test.")

    categories = totals.get("q3_categories", {})
    names = [k for k, v in categories.items() if v]
    with card("exp-q3"):
        ui.section("Why is the mechanism strategyproof although the condition fails?", "Question 3",
                   f"{sum(categories.values()):,} instances, classified by the reason the odd path "
                   "does not translate into a profitable lie.")
        if categories:
            ui.hbars(sorted(((CATEGORIES[k][0], v) for k, v in categories.items() if v),
                            key=lambda item: -item[1]))
    if not names:
        return

    cases = all_cases(dataset)
    q3 = [c for c in cases.values() if c["group"] == "condition_false_but_strategyproof"]
    with card("exp-browse"):
        ui.section("Browse an instance", "Question 3 · examples")
        c1, c2 = st.columns([1.4, 1])
        category = c1.selectbox("Category", names, format_func=lambda k: CATEGORIES[k][0],
                                key="exp_category")
        members = sorted(c["instance_id"] for c in q3 if c["explanation"]["category"] == category)
        case_id = c2.selectbox(f"Instance ({len(members)} in this category)", members,
                               key="exp_case")
        st.caption(CATEGORIES[category][1])
        case = cases[case_id]
        owners = {a: agent for agent, ms in case["agent_types"].items() for a in ms}
        attacks = [tuple(edge) for edge in case["attacks"]]
        first = case["explanation"]["pairs"][0]
        labels = grounded_labelling(ArgumentationFramework(case["arguments"], attacks))
        left, right = st.columns([1.2, 1], gap="large")
        with left:
            ui.graph("experiment", case["arguments"], attacks, owners=owners, labels=labels,
                     path=tuple(first["path"]))
        with right:
            ui.table(["agent", "odd path", "reason"], [
                [ui.agent_chip(p['agent']),
                 '<span class="set">' + " → ".join(ui.arg_html(a) for a in p["path"]) + "</span>",
                 ui.esc(PAIR_REASONS[p["reason"]])]
                for p in case["explanation"]["pairs"]
            ], max_height=300)
            st.button("Open this instance in the mechanism tab →", type="primary",
                      on_click=load_case_into_lab, args=(dataset, case_id), width="stretch")


# --------------------------------------------------------------------------- tab 4: notes

NOTES = """
### Corrections to the textbook (as flagged in the assignment)
* **Example 5.10** prints u_y(o) = 1 and u_z(o) = 0, attaching each utility to the other agent's
  argument set. With A_y = {α2} and A_z = {α3} and outcome {α1, α3}, it is **u_y = 0, u_z = 1**.
* **After Example 5.11** the book says α5 cancels x's indirect self-defeat. It is **α6**, the new
  argument that defeats α3.

### Modelling choices
* **Utility** of agent i is |Aᵢ ∩ outcome|, always counted against the *true* type (Definition 5.22).
* **Lying** is limited to hiding arguments: each report is a subset of Aᵢ (Section 5.4).
* **Theorem 5.3 check** enumerates, for each agent, every combination of the other agents' subsets
  and every own subset. Ties count as truthful being a best response.
* **Theorem 5.4's "odd-length path"** is checked as an odd *walk* (vertices may repeat), found by a
  breadth-first search over (argument, parity) states that terminates on cyclic graphs. Pairs with
  α = β count, so a self-attack or an odd cycle through an owned argument violates the condition.
  On every generated instance the simple-path reading gives the same answer.
* **Self-attacks** are sampled like any other attack in the default run, because the assignment says
  "each possible attack". A second run excludes them, since a single self-attack already falsifies
  Theorem 5.4's condition.
"""


# --------------------------------------------------------------------------- main

def main() -> None:
    st.set_page_config(page_title="Argumentation Lab", page_icon="⚖️", layout="wide")
    ui.inject_css()
    fw_id, arguments, attacks, owners, note = choose_framework()
    ui.side_note(note, len(arguments), len(attacks))

    agents = sorted({o for o in (owners or {}).values()})
    ui.hero(st.session_state.get("source", ""), len(arguments), len(attacks), agents)

    st.session_state.setdefault("tab", TAB_SEMANTICS)
    tab_semantics, tab_mechanism, tab_experiments, tab_notes = st.tabs(
        [TAB_SEMANTICS, TAB_MECHANISM, TAB_EXPERIMENTS, TAB_NOTES], key="tab", on_change="rerun"
    )
    framework = ArgumentationFramework(arguments, attacks) if arguments else None
    with tab_semantics:
        if framework:
            semantics_tab(framework, fw_id, owners)
    with tab_mechanism:
        if framework:
            mechanism_tab(framework, fw_id, owners)
    with tab_experiments:
        experiments_tab()
    with tab_notes:
        with card("notes"):
            st.markdown(NOTES)


main()
