"""Build a self-contained, interactive HTML demonstration of the assignment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PAGE = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0b1020">
  <title>Argumentation Lab | Assignment 3</title>
  <style>
    :root {
      color-scheme: dark;
      --ink: #edf2ff;
      --muted: #9ba9c4;
      --faint: #70809e;
      --panel: rgba(18, 27, 49, .88);
      --panel-2: #111b31;
      --line: rgba(155, 174, 211, .16);
      --blue: #78a6ff;
      --mint: #44e0b0;
      --amber: #ffc76b;
      --coral: #ff7e86;
      --violet: #b39bff;
      --shadow: 0 24px 70px rgba(0, 0, 0, .26);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      background:
        radial-gradient(ellipse at 15% 0%, rgba(72, 108, 201, .2), transparent 34rem),
        radial-gradient(ellipse at 92% 12%, rgba(77, 205, 170, .11), transparent 29rem),
        #0b1020;
      line-height: 1.5;
    }
    button, input { font: inherit; }
    button { cursor: pointer; }
    .shell { width: min(1320px, calc(100% - 40px)); margin: 0 auto; }
    .topbar {
      display: flex; align-items: center; justify-content: space-between;
      padding: 22px 0 18px; border-bottom: 1px solid var(--line);
    }
    .brand { display: flex; align-items: center; gap: 12px; font-weight: 750; letter-spacing: .01em; }
    .brand-mark {
      display: grid; place-items: center; width: 36px; height: 36px; border-radius: 12px;
      color: #06151a; font-weight: 900; background: linear-gradient(135deg, var(--mint), #89dbff);
      box-shadow: 0 0 24px rgba(68, 224, 176, .2);
    }
    .brand small { display: block; color: var(--muted); font-size: 11px; font-weight: 600; letter-spacing: .13em; text-transform: uppercase; }
    .top-links { display: flex; gap: 22px; color: var(--muted); font-size: 13px; }
    .top-links a { color: inherit; text-decoration: none; }
    .top-links a:hover { color: var(--ink); }
    .hero { padding: 54px 0 30px; }
    .eyebrow { display: inline-flex; align-items: center; gap: 8px; color: var(--mint); font-size: 11px; font-weight: 800; letter-spacing: .17em; text-transform: uppercase; }
    .eyebrow::before { content: ""; width: 20px; height: 1px; background: currentColor; }
    h1 { max-width: 850px; margin: 14px 0 16px; font-size: clamp(38px, 6vw, 68px); line-height: 1.02; letter-spacing: -.055em; }
    .hero h1 span { color: transparent; background: linear-gradient(90deg, #8fb5ff, #52e1b5 65%, #ffd078); background-clip: text; }
    .hero-copy { max-width: 730px; margin: 0; color: #b5c1d7; font-size: 16px; }
    .hero-tags { display: flex; flex-wrap: wrap; gap: 9px; margin-top: 23px; }
    .tag { border: 1px solid var(--line); border-radius: 999px; padding: 6px 11px; color: #c5d1e7; background: rgba(255,255,255,.025); font-size: 12px; }
    .section { padding: 28px 0; }
    .section-head { display: flex; justify-content: space-between; align-items: end; gap: 24px; margin-bottom: 17px; }
    .section-kicker { color: var(--blue); font-size: 11px; font-weight: 800; letter-spacing: .15em; text-transform: uppercase; }
    h2 { margin: 5px 0 0; font-size: clamp(23px, 3vw, 32px); letter-spacing: -.035em; }
    .section-head p { max-width: 550px; margin: 0; color: var(--muted); font-size: 13px; }
    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .metric, .card {
      border: 1px solid var(--line); border-radius: 18px; background: var(--panel);
      box-shadow: var(--shadow); backdrop-filter: blur(14px);
    }
    .metric { min-height: 112px; padding: 17px 18px; }
    .metric-label { color: var(--muted); font-size: 11px; font-weight: 700; letter-spacing: .1em; text-transform: uppercase; }
    .metric-value { margin-top: 8px; font-size: 29px; font-weight: 780; letter-spacing: -.04em; }
    .metric-detail { color: var(--faint); font-size: 11px; }
    .lab-grid { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(300px, .8fr); gap: 14px; align-items: stretch; }
    .card { padding: 21px; }
    .graph-card { padding: 0; overflow: hidden; }
    .card-top { display: flex; justify-content: space-between; align-items: start; gap: 12px; padding: 21px 21px 0; }
    .card-title { font-size: 17px; font-weight: 740; letter-spacing: -.02em; }
    .card-subtitle { margin-top: 4px; color: var(--muted); font-size: 12px; }
    .segmented { display: inline-flex; gap: 4px; padding: 4px; border: 1px solid var(--line); border-radius: 12px; background: #0c1427; }
    .segmented button { border: 0; border-radius: 8px; padding: 8px 10px; color: var(--muted); background: transparent; font-size: 12px; font-weight: 700; }
    .segmented button.active { color: #09121d; background: var(--mint); }
    .graph-wrap { padding: 8px 10px 0; }
    #argument-graph { display: block; width: 100%; min-height: 250px; overflow: visible; }
    .edge { fill: none; stroke: #7182a1; stroke-width: 2; opacity: .18; transition: opacity .2s, stroke .2s; }
    .edge.active { stroke: #a8b9da; opacity: .78; }
    .edge.active.conflict { stroke: var(--coral); }
    .node circle { stroke-width: 2.4; transition: fill .2s, stroke .2s, opacity .2s; }
    .node .arg-label { fill: #f3f6ff; font-size: 16px; font-weight: 800; text-anchor: middle; dominant-baseline: middle; }
    .node .owner-label { font-size: 9px; font-weight: 800; letter-spacing: .1em; text-anchor: middle; text-transform: uppercase; }
    .node .state-label { font-size: 8px; font-weight: 800; letter-spacing: .09em; text-anchor: middle; text-transform: uppercase; }
    .node.owner-x .owner-label { fill: var(--blue); }
    .node.owner-y .owner-label { fill: var(--violet); }
    .node.owner-z .owner-label { fill: var(--amber); }
    .node.state-in circle { fill: #123b36; stroke: var(--mint); }
    .node.state-out circle { fill: #3b202d; stroke: var(--coral); }
    .node.state-undec circle { fill: #392f1e; stroke: var(--amber); }
    .node.state-hidden circle { fill: #202a3e; stroke: #68758d; stroke-dasharray: 5 5; opacity: .68; }
    .node.state-hidden .arg-label, .node.state-hidden .owner-label { opacity: .55; }
    .node.state-in .state-label { fill: var(--mint); }
    .node.state-out .state-label { fill: var(--coral); }
    .node.state-undec .state-label { fill: var(--amber); }
    .node.state-hidden .state-label { fill: #a1aec5; }
    .legend { display: flex; flex-wrap: wrap; gap: 12px; padding: 7px 21px 16px; color: var(--muted); font-size: 10px; }
    .legend span { display: inline-flex; align-items: center; gap: 6px; }
    .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; }
    .dot.in { background: var(--mint); } .dot.out { background: var(--coral); } .dot.undec { background: var(--amber); } .dot.hidden { background: #68758d; }
    .live-panel { display: flex; flex-direction: column; gap: 14px; }
    .live-panel .card { box-shadow: none; }
    .controls-heading { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
    .controls-heading h3, .outcome-card h3 { margin: 0; font-size: 14px; }
    .controls-heading span { color: var(--faint); font-size: 10px; }
    #report-controls { display: flex; flex-wrap: wrap; gap: 7px; margin-top: 13px; }
    .report-toggle { display: inline-flex; align-items: center; gap: 7px; border: 1px solid var(--line); border-radius: 10px; padding: 7px 9px; color: #c5d1e7; background: #0e172b; cursor: pointer; font-size: 11px; }
    .report-toggle input { accent-color: var(--mint); width: 13px; height: 13px; margin: 0; }
    .report-toggle.owner-x { border-color: rgba(120,166,255,.3); }
    .report-toggle.owner-y { border-color: rgba(179,155,255,.3); }
    .report-toggle.owner-z { border-color: rgba(255,199,107,.3); }
    .quick-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
    .action-button { border: 1px solid rgba(120,166,255,.35); border-radius: 10px; padding: 8px 10px; color: #dbe6ff; background: rgba(120,166,255,.09); font-size: 11px; font-weight: 700; }
    .action-button:hover { background: rgba(120,166,255,.17); }
    .action-button.primary { color: #061714; border-color: transparent; background: var(--mint); }
    .owner-utilities { display: grid; gap: 11px; margin-top: 14px; }
    .utility-row { display: grid; grid-template-columns: 32px 1fr auto; gap: 9px; align-items: center; }
    .owner-badge { display: grid; place-items: center; width: 28px; height: 28px; border: 1px solid var(--line); border-radius: 9px; font-size: 11px; font-weight: 800; }
    .owner-badge.x { color: var(--blue); } .owner-badge.y { color: var(--violet); } .owner-badge.z { color: var(--amber); }
    .utility-track { height: 7px; overflow: hidden; border-radius: 99px; background: #26324a; }
    .utility-fill { height: 100%; border-radius: inherit; background: linear-gradient(90deg, #4dbfa2, #6be8bd); transition: width .25s; }
    .utility-meta { min-width: 46px; color: var(--ink); font-size: 11px; font-weight: 750; text-align: right; }
    .utility-meta small { display: block; color: var(--faint); font-size: 9px; font-weight: 600; }
    .outcome-box { margin-top: 12px; padding: 12px; border: 1px solid rgba(68,224,176,.2); border-radius: 12px; background: rgba(68,224,176,.055); }
    .outcome-label { color: var(--muted); font-size: 10px; font-weight: 750; letter-spacing: .1em; text-transform: uppercase; }
    #accepted-set { margin-top: 6px; color: var(--mint); font-size: 14px; font-weight: 800; }
    #live-verdict { margin-top: 9px; color: var(--muted); font-size: 11px; }
    #live-verdict.gain { color: var(--mint); } #live-verdict.loss { color: var(--amber); }
    .case-note { min-height: 110px; border-left: 2px solid var(--blue); padding: 2px 0 2px 13px; color: #b8c4da; font-size: 12px; }
    .case-note strong { color: var(--ink); }
    .experiment-layout { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(300px, .65fr); gap: 14px; }
    .chart-card { min-height: 370px; }
    #experiment-chart { width: 100%; min-height: 255px; margin-top: 13px; }
    .chart-axis { stroke: #52617c; stroke-width: 1; }
    .chart-grid { stroke: rgba(133,151,184,.2); stroke-width: 1; stroke-dasharray: 3 5; }
    .chart-text { fill: #9ba9c4; font-family: inherit; font-size: 10px; }
    .chart-value { fill: #eaf0ff; font-family: inherit; font-size: 10px; font-weight: 750; }
    .bar-sp { fill: #52d6ad; } .bar-thm { fill: #8daaff; }
    .ci-line { stroke: #d6e0f2; stroke-width: 1.4; }
    .chart-legend { display: flex; flex-wrap: wrap; gap: 14px; color: var(--muted); font-size: 10px; }
    .chart-legend span { display: inline-flex; align-items: center; gap: 6px; }
    .chart-swatch { width: 10px; height: 10px; border-radius: 3px; }
    .experiment-table { width: 100%; margin-top: 13px; border-collapse: collapse; font-size: 11px; }
    .experiment-table th { padding: 9px 6px; color: var(--muted); font-size: 9px; letter-spacing: .07em; text-align: left; text-transform: uppercase; border-bottom: 1px solid var(--line); }
    .experiment-table td { padding: 10px 6px; border-bottom: 1px solid rgba(155,174,211,.09); }
    .experiment-table td:first-child { color: var(--mint); font-weight: 800; }
    .audit-good, .audit-alert, .empty-state { border-radius: 13px; padding: 13px 14px; font-size: 11px; }
    .finding-card { margin-top: 12px; border: 1px solid rgba(179,155,255,.23); border-radius: 13px; padding: 13px 14px; color: #c6d0e5; background: rgba(179,155,255,.055); font-size: 11px; }
    .finding-card strong { color: #e4dcff; }
    .audit-good { border: 1px solid rgba(68,224,176,.23); color: #b6f3de; background: rgba(68,224,176,.06); }
    .audit-alert { border: 1px solid rgba(255,126,134,.3); color: #ffd1d4; background: rgba(255,126,134,.08); }
    .empty-state { margin-top: 18px; border: 1px dashed rgba(155,174,211,.3); color: var(--muted); background: rgba(255,255,255,.02); }
    .empty-state code { color: var(--mint); }
    .method-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
    .method-card { min-height: 145px; padding: 17px; border: 1px solid var(--line); border-radius: 15px; background: rgba(18,27,49,.62); }
    .method-number { color: var(--mint); font-size: 10px; font-weight: 850; letter-spacing: .14em; }
    .method-card h3 { margin: 8px 0 5px; font-size: 14px; }
    .method-card p { margin: 0; color: var(--muted); font-size: 11px; }
    footer { display: flex; justify-content: space-between; gap: 16px; margin-top: 25px; padding: 21px 0 34px; border-top: 1px solid var(--line); color: var(--faint); font-size: 10px; }
    @media (max-width: 900px) {
      .lab-grid, .experiment-layout { grid-template-columns: 1fr; }
      .metrics { grid-template-columns: repeat(2, 1fr); }
      .method-grid { grid-template-columns: 1fr; }
      .section-head { align-items: start; flex-direction: column; }
    }
    @media (max-width: 560px) {
      .shell { width: min(100% - 24px, 1320px); }
      .top-links { display: none; }
      .hero { padding-top: 38px; }
      .metrics { gap: 8px; }
      .metric { min-height: 96px; padding: 13px; }
      .metric-value { font-size: 23px; }
      .card { padding: 16px; }
      .card-top { flex-direction: column; }
      .graph-card .card-top { padding: 16px 16px 0; }
      .segmented { width: 100%; }
      .segmented button { flex: 1; }
      .graph-wrap { padding: 3px 0 0; }
      #argument-graph { min-height: 205px; }
      .legend { padding-left: 16px; }
      .experiment-table { font-size: 9px; }
      .experiment-table th, .experiment-table td { padding-left: 3px; padding-right: 3px; }
      footer { flex-direction: column; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header class="topbar">
      <div class="brand"><div class="brand-mark">A</div><div>Argumentation Lab<small>Autonomous Systems · Assignment 3</small></div></div>
      <nav class="top-links" aria-label="Page sections"><a href="#live-lab">Live mechanism</a><a href="#experiments">Experiments</a><a href="#method">Method</a></nav>
    </header>

    <main>
      <section class="hero">
        <div class="eyebrow">Grounded semantics · strategic reporting</div>
        <h1>When does hiding an argument <span>change the outcome?</span></h1>
        <p class="hero-copy">Explore how the grounded extension responds to each agent's report, then compare the theorem's sufficient condition with exhaustive strategyproofness checks across random frameworks.</p>
        <div class="hero-tags"><span class="tag">Live argument graph</span><span class="tag">Truthful vs. hidden reports</span><span class="tag">Reproducible random study</span></div>
      </section>

      <section class="section" aria-label="Experiment overview">
        <div class="metrics">
          <div class="metric"><div class="metric-label">Instances analyzed</div><div class="metric-value" id="metric-instances">—</div><div class="metric-detail" id="metric-instances-detail">Run experiments to populate</div></div>
          <div class="metric"><div class="metric-label">Strategyproof</div><div class="metric-value" id="metric-strategyproof">—</div><div class="metric-detail">Truthful report is never worse</div></div>
          <div class="metric"><div class="metric-label">Theorem 5.4 condition</div><div class="metric-value" id="metric-condition">—</div><div class="metric-detail">No owned pair joined by an odd path</div></div>
          <div class="metric"><div class="metric-label">Condition fails, still SP</div><div class="metric-value" id="metric-not-necessary">—</div><div class="metric-detail">Sufficient does not mean necessary</div></div>
        </div>
      </section>

      <section id="live-lab" class="section">
        <div class="section-head"><div><div class="section-kicker">01 / Interactive case study</div><h2>Change the reports. Watch the graph settle.</h2></div><p>Toggle an argument to reveal or withhold it. The graph recomputes the grounded extension and each agent's utility from its true argument set.</p></div>
        <div class="lab-grid">
          <div class="card graph-card">
            <div class="card-top"><div><div class="card-title" id="example-title">Example 5.10 · Hiding can pay</div><div class="card-subtitle" id="example-subtitle">The report profile determines which arguments are in the induced graph.</div></div>
              <div class="segmented" role="group" aria-label="Choose textbook example"><button id="select-ex10" class="active" type="button">Example 5.10</button><button id="select-ex11" type="button">Example 5.11</button></div>
            </div>
            <div class="graph-wrap"><svg id="argument-graph" viewBox="0 0 820 390" role="img" aria-label="Interactive argumentation graph"></svg></div>
            <div class="legend"><span><i class="dot in"></i>in / accepted</span><span><i class="dot out"></i>out / defeated</span><span><i class="dot undec"></i>undecided</span><span><i class="dot hidden"></i>withheld</span><span>Arrow = attack</span></div>
          </div>

          <div class="live-panel">
            <div class="card">
              <div class="controls-heading"><h3>Agent reports</h3><span>Checked = revealed</span></div>
              <div id="report-controls"></div>
              <div class="quick-actions"><button class="action-button primary" id="truth-button" type="button">Reveal all arguments</button><button class="action-button" id="example-action" type="button">Try the profitable report</button></div>
            </div>
            <div class="card outcome-card">
              <h3>Mechanism outcome</h3>
              <div class="outcome-box"><div class="outcome-label">Grounded extension</div><div id="accepted-set">{ }</div><div id="live-verdict"></div></div>
              <div class="owner-utilities" id="owner-utilities"></div>
            </div>
            <div class="card"><div id="case-note" class="case-note"></div></div>
          </div>
        </div>
      </section>

      <section id="experiments" class="section">
        <div class="section-head"><div><div class="section-kicker">02 / Randomized experiment</div><h2>Does the sufficient condition explain strategyproofness?</h2></div><p>Each dot comes from exhaustive report comparisons, not sampled strategies. The confidence whiskers summarize uncertainty in the observed strategyproof fraction.</p></div>
        <div class="experiment-layout">
          <div class="card chart-card">
            <div class="card-title">Observed fractions by attack probability</div><div class="card-subtitle" id="experiment-caption">Three independent probability settings · Wilson 95% intervals shown for strategyproofness</div>
            <div id="experiment-chart"></div>
            <div class="chart-legend"><span><i class="chart-swatch" style="background:#52d6ad"></i>Strategyproof</span><span><i class="chart-swatch" style="background:#8daaff"></i>Theorem 5.4 condition holds</span></div>
            <div id="experiment-empty" class="empty-state">Experiment results will appear here after running <code>python experiments.py</code>. The demo does not invent sample results.</div>
          </div>
          <div class="card">
            <div class="card-title">Results at a glance</div><div class="card-subtitle" id="seed-caption">No experiment summary loaded</div>
            <table class="experiment-table"><thead><tr><th>p</th><th>SP</th><th>Thm 5.4</th><th>Cond. true / SP false</th><th>Cond. false / SP</th></tr></thead><tbody id="experiment-rows"></tbody></table>
            <div id="theorem-audit" style="margin-top:14px"></div>
            <div id="interesting-case"></div>
          </div>
        </div>
      </section>

      <section id="method" class="section">
        <div class="section-head"><div><div class="section-kicker">03 / How to read the demo</div><h2>One outcome rule. Two different checks.</h2></div></div>
        <div class="method-grid">
          <div class="method-card"><div class="method-number">01 · MECHANISM</div><h3>Union, induce, ground</h3><p>The mechanism unions reported arguments, keeps attacks between those arguments, and returns the least fixed point of the characteristic function.</p></div>
          <div class="method-card"><div class="method-number">02 · THEOREM 5.3</div><h3>Exhaustive truthfulness</h3><p>For each agent, every other-agent report profile and every subset report are compared against revealing the full true type. Ties count as truthful best responses.</p></div>
          <div class="method-card"><div class="method-number">03 · THEOREM 5.4</div><h3>Odd-path certificate</h3><p>A parity-state search checks for an odd-length directed walk between arguments belonging to the same agent, including walks that pass through cycles.</p></div>
        </div>
      </section>
    </main>

    <footer><span>CSL7650 · Autonomous Systems · Assignment 3</span><span>Self-contained page · works offline · no browser libraries</span></footer>
  </div>

  <script>
    const experimentSummary = __EXPERIMENT_JSON__;
    const interestingCases = __INTERESTING_CASES__;
    const examples = {
      ex10: {
        title: "Example 5.10 · Hiding can pay",
        subtitle: "The report profile determines which arguments are in the induced graph.",
        arguments: ["a1", "a2", "a3", "a4", "a5"],
        attacks: [["a1","a2"],["a2","a3"],["a3","a4"],["a3","a5"]],
        owners: {a1:"x",a2:"y",a3:"z",a4:"x",a5:"x"},
        note: "<strong>Reference result.</strong> Full revelation gives X one accepted argument ({a1, a4, a5} ∩ {a1, a3} = {a1}). Hiding a1 breaks the chain and gives X two accepted arguments, {a4, a5}. Utilities are always counted against each agent's own true type.",
        actionLabel: "Apply X's profitable report",
        action: reports => { reports.a1 = false; }
      },
      ex11: {
        title: "Example 5.11 · The condition is sufficient",
        subtitle: "Argument a6 attacks a3, shielding X's downstream arguments.",
        arguments: ["a1", "a2", "a3", "a4", "a5", "a6"],
        attacks: [["a1","a2"],["a2","a3"],["a3","a4"],["a3","a5"],["a6","a3"]],
        owners: {a1:"x",a2:"y",a3:"z",a4:"x",a5:"x",a6:"x"},
        note: "<strong>Odd-path witness.</strong> X owns a1, a4, a5, and a6; there are length-3 walks a1 → a2 → a3 → a4 and a1 → a2 → a3 → a5. So Theorem 5.4's condition fails. With all reports revealed, however, the grounded extension accepts all four of X's arguments: a6 defeats a3 and protects a4 and a5.",
        actionLabel: "Withhold a6",
        action: reports => { reports.a6 = false; }
      }
    };

    const positions = {a1:[105,200], a2:[300,200], a3:[495,200], a4:[690,115], a5:[690,285], a6:[495,55]};
    const agentNames = {x:"Agent X", y:"Agent Y", z:"Agent Z"};
    const agentClasses = {x:"owner-x", y:"owner-y", z:"owner-z"};
    let currentExample = "ex10";
    let revealed = {};

    function groundedOutcome(data, activeArguments) {
      const active = new Set(activeArguments);
      const attacks = data.attacks.filter(([source,target]) => active.has(source) && active.has(target));
      let accepted = new Set();
      for (let step = 0; step <= active.size + 1; step++) {
        const next = new Set();
        for (const argument of active) {
          const attackers = attacks.filter(([,target]) => target === argument).map(([source]) => source);
          const defended = attackers.every(attacker => attacks.some(([defender,target]) => accepted.has(defender) && target === attacker));
          if (defended) next.add(argument);
        }
        if (next.size === accepted.size && [...next].every(argument => accepted.has(argument))) {
          accepted = next;
          break;
        }
        accepted = next;
      }
      const out = new Set();
      for (const [source,target] of attacks) if (accepted.has(source)) out.add(target);
      const statuses = {};
      for (const argument of data.arguments) {
        if (!active.has(argument)) statuses[argument] = "hidden";
        else if (accepted.has(argument)) statuses[argument] = "in";
        else if (out.has(argument)) statuses[argument] = "out";
        else statuses[argument] = "undec";
      }
      return {accepted, statuses};
    }

    function evaluate(data, report) {
      const active = data.arguments.filter(argument => report[argument]);
      const grounded = groundedOutcome(data, active);
      const utilities = {x:0,y:0,z:0};
      for (const argument of grounded.accepted) utilities[data.owners[argument]] += 1;
      return {active, ...grounded, utilities};
    }

    function truthfulReports(data) {
      return Object.fromEntries(data.arguments.map(argument => [argument, true]));
    }

    function renderControls(data) {
      const controls = document.getElementById("report-controls");
      controls.innerHTML = data.arguments.map(argument => {
        const owner = data.owners[argument];
        return `<label class="report-toggle ${agentClasses[owner]}"><input type="checkbox" data-argument="${argument}" ${revealed[argument] ? "checked" : ""}><span>${argument}</span><small>${owner.toUpperCase()}</small></label>`;
      }).join("");
      controls.querySelectorAll("input").forEach(input => input.addEventListener("change", event => {
        revealed[event.target.dataset.argument] = event.target.checked;
        updateLab();
      }));
    }

    function renderGraph(data, result) {
      const svg = document.getElementById("argument-graph");
      const edgeMarkup = data.attacks.map(([source,target]) => {
        const [x1,y1] = positions[source], [x2,y2] = positions[target];
        const dx=x2-x1, dy=y2-y1, length=Math.sqrt(dx*dx+dy*dy) || 1;
        const sx=x1+dx*34/length, sy=y1+dy*34/length;
        const ex=x2-dx*39/length, ey=y2-dy*39/length;
        const active = revealed[source] && revealed[target];
        const conflict = active && result.accepted.has(source) && result.accepted.has(target);
        return `<path class="edge ${active ? "active" : ""} ${conflict ? "conflict" : ""}" d="M ${sx} ${sy} L ${ex} ${ey}" marker-end="url(#arrow)"/>`;
      }).join("");
      const nodeMarkup = data.arguments.map(argument => {
        const [x,y] = positions[argument], owner=data.owners[argument], state=result.statuses[argument];
        const statusText = state === "hidden" ? "WITHHELD" : state.toUpperCase();
        return `<g class="node ${agentClasses[owner]} state-${state}"><circle cx="${x}" cy="${y}" r="31"/><text class="arg-label" x="${x}" y="${y}">${argument}</text><text class="owner-label" x="${x}" y="${y+45}">${owner.toUpperCase()} · ${agentNames[owner]}</text><text class="state-label" x="${x}" y="${y+59}">${statusText}</text></g>`;
      }).join("");
      svg.innerHTML = `<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L8,4 L0,8 z" fill="#a8b9da"/></marker></defs>${edgeMarkup}${nodeMarkup}`;
    }

    function renderUtilities(data, result, truthful) {
      const holder = document.getElementById("owner-utilities");
      holder.innerHTML = ["x","y","z"].map(agent => {
        const size = data.arguments.filter(argument => data.owners[argument] === agent).length;
        const value = result.utilities[agent], baseline = truthful.utilities[agent];
        const delta = value - baseline;
        const deltaText = delta > 0 ? `+${delta} vs truth` : delta < 0 ? `${delta} vs truth` : "same as truth";
        return `<div class="utility-row"><div class="owner-badge ${agent}">${agent.toUpperCase()}</div><div class="utility-track" aria-label="${agentNames[agent]} accepted ${value} of ${size}"><div class="utility-fill" style="width:${size ? value/size*100 : 0}%"></div></div><div class="utility-meta">${value}/${size}<small>${deltaText}</small></div></div>`;
      }).join("");
      const accepted = [...result.accepted].sort((a,b)=>Number(a.slice(1))-Number(b.slice(1)));
      document.getElementById("accepted-set").textContent = `{ ${accepted.join(", ")} }`;
      const xDelta = result.utilities.x - truthful.utilities.x;
      const verdict = document.getElementById("live-verdict");
      if (xDelta > 0) {
        verdict.className = "gain";
        verdict.textContent = `X gains ${xDelta} accepted argument${xDelta===1?"":"s"} compared with full revelation.`;
      } else if (xDelta < 0) {
        verdict.className = "loss";
        verdict.textContent = `X loses ${Math.abs(xDelta)} accepted argument${xDelta===-1?"":"s"} compared with full revelation.`;
      } else {
        verdict.className = "";
        verdict.textContent = "X's utility matches the full-revelation baseline for this report profile.";
      }
    }

    function updateLab() {
      const data = examples[currentExample];
      const result = evaluate(data, revealed);
      const truthful = evaluate(data, truthfulReports(data));
      renderGraph(data, result);
      renderUtilities(data, result, truthful);
    }

    function selectExample(key) {
      currentExample = key;
      const data = examples[key];
      revealed = truthfulReports(data);
      document.getElementById("example-title").textContent = data.title;
      document.getElementById("example-subtitle").textContent = data.subtitle;
      document.getElementById("case-note").innerHTML = data.note;
      document.getElementById("example-action").textContent = data.actionLabel;
      document.getElementById("select-ex10").classList.toggle("active", key === "ex10");
      document.getElementById("select-ex11").classList.toggle("active", key === "ex11");
      renderControls(data);
      updateLab();
    }

    document.getElementById("select-ex10").addEventListener("click", () => selectExample("ex10"));
    document.getElementById("select-ex11").addEventListener("click", () => selectExample("ex11"));
    document.getElementById("truth-button").addEventListener("click", () => {
      revealed = truthfulReports(examples[currentExample]);
      renderControls(examples[currentExample]);
      updateLab();
    });
    document.getElementById("example-action").addEventListener("click", () => {
      examples[currentExample].action(revealed);
      renderControls(examples[currentExample]);
      updateLab();
    });

    function renderExperimentChart(rows) {
      const width=720, height=270, left=52, right=18, top=18, bottom=42;
      const plotHeight=height-top-bottom, plotWidth=width-left-right;
      const ticks=[0,.25,.5,.75,1];
      let svg=`<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Strategyproof and Theorem 5.4 rates by attack probability">`;
      ticks.forEach(value=>{
        const y=top+plotHeight*(1-value);
        svg+=`<line class="chart-grid" x1="${left}" y1="${y}" x2="${width-right}" y2="${y}"/><text class="chart-text" x="${left-9}" y="${y+3}" text-anchor="end">${Math.round(value*100)}%</text>`;
      });
      svg+=`<line class="chart-axis" x1="${left}" y1="${top}" x2="${left}" y2="${height-bottom}"/><line class="chart-axis" x1="${left}" y1="${height-bottom}" x2="${width-right}" y2="${height-bottom}"/>`;
      const groupWidth=plotWidth/rows.length, barWidth=Math.min(42,groupWidth*.23);
      rows.forEach((row,index)=>{
        const center=left+groupWidth*(index+.5);
        const values=[{key:"strategyproof_fraction", cls:"bar-sp", offset:-barWidth*.62, ci:row.strategyproof_ci95},{key:"theorem54_condition_fraction", cls:"bar-thm", offset:barWidth*.62}];
        values.forEach(item=>{
          const value=row[item.key], x=center+item.offset-barWidth/2, barHeight=plotHeight*value, y=height-bottom-barHeight;
          svg+=`<rect class="${item.cls}" x="${x}" y="${y}" width="${barWidth}" height="${barHeight}" rx="5" opacity=".92"><title>${item.key === "strategyproof_fraction" ? "Strategyproof" : "Theorem 5.4 condition"}: ${(value*100).toFixed(1)}%</title></rect>`;
          svg+=`<text class="chart-value" x="${x+barWidth/2}" y="${Math.max(top+10,y-6)}" text-anchor="middle">${(value*100).toFixed(0)}%</text>`;
          if(item.ci){
            const lowY=height-bottom-plotHeight*item.ci[0], highY=height-bottom-plotHeight*item.ci[1], cx=x+barWidth/2;
            svg+=`<line class="ci-line" x1="${cx}" y1="${highY}" x2="${cx}" y2="${lowY}"/><line class="ci-line" x1="${cx-5}" y1="${highY}" x2="${cx+5}" y2="${highY}"/><line class="ci-line" x1="${cx-5}" y1="${lowY}" x2="${cx+5}" y2="${lowY}"/>`;
          }
        });
        svg+=`<text class="chart-text" x="${center}" y="${height-14}" text-anchor="middle">p = ${Number(row.p).toFixed(2)}</text>`;
      });
      svg+="</svg>";
      document.getElementById("experiment-chart").innerHTML=svg;
    }

    function loadExperiments() {
      if (!experimentSummary || !Array.isArray(experimentSummary.results)) return;
      const rows=experimentSummary.results;
      const total=experimentSummary.totals.instances;
      const sp=experimentSummary.totals.strategyproof;
      const conditionTrue=rows.reduce((sum,row)=>sum+row.theorem54_condition_count,0);
      const notNecessary=experimentSummary.totals.condition_false_but_strategyproof;
      document.getElementById("metric-instances").textContent=total.toLocaleString();
      document.getElementById("metric-instances-detail").textContent=`Seed ${experimentSummary.seed} · ${experimentSummary.generator.instances_per_probability} per p`;
      document.getElementById("metric-strategyproof").textContent=`${(100*sp/total).toFixed(1)}%`;
      document.getElementById("metric-condition").textContent=`${(100*conditionTrue/total).toFixed(1)}%`;
      document.getElementById("metric-not-necessary").textContent=notNecessary.toLocaleString();
      document.getElementById("seed-caption").textContent=`Seed ${experimentSummary.seed} · ${total.toLocaleString()} exhaustive instances`;
      document.getElementById("experiment-caption").textContent=`${experimentSummary.generator.instances_per_probability} instances at each p · Wilson 95% intervals shown for strategyproofness`;
      document.getElementById("experiment-empty").style.display="none";
      renderExperimentChart(rows);
      document.getElementById("experiment-rows").innerHTML=rows.map(row=>{
        const interval=row.strategyproof_ci95.map(value=>(100*value).toFixed(1)).join("–");
        return `<tr><td>${Number(row.p).toFixed(2)}</td><td>${row.strategyproof_count}/${row.instances}<br><span style="color:#8190aa">${(row.strategyproof_fraction*100).toFixed(1)}% · CI ${interval}%</span></td><td>${row.theorem54_condition_count}/${row.instances}<br><span style="color:#8190aa">${(row.theorem54_condition_fraction*100).toFixed(1)}%</span></td><td>${row.condition_true_but_not_strategyproof}</td><td>${row.condition_false_but_strategyproof}</td></tr>`;
      }).join("");
      const failures=experimentSummary.totals.condition_true_but_not_strategyproof;
      const audit=document.getElementById("theorem-audit");
      if(failures===0){
        audit.className="audit-good";
        audit.textContent=`Sufficiency check passed: ${failures} instances satisfy Theorem 5.4's condition but fail the exhaustive Theorem 5.3 check.`;
      } else {
        audit.className="audit-alert";
        audit.textContent=`Review needed: ${failures} instances satisfy Theorem 5.4's condition but fail the exhaustive Theorem 5.3 check. Inspect interesting_cases.json for witnesses.`;
      }

      const candidates=interestingCases && interestingCases.condition_false_but_strategyproof;
      const finding=document.getElementById("interesting-case");
      if(candidates && candidates.length){
        const sample=candidates[0];
        const witness=sample.theorem54_witness;
        const agentAudit=sample.truthfulness_audit && sample.truthfulness_audit[witness.agent];
        const path=witness.arguments.join(" → ");
        const margin=agentAudit && agentAudit.minimum_truthful_utility_margin;
        finding.className="finding-card";
        finding.innerHTML=`<strong>One condition-fails / strategyproof instance:</strong> ${sample.instance_id} at p=${Number(sample.p).toFixed(2)}. ${witness.agent.toUpperCase()} owns the odd walk ${path} (length ${witness.length}). Exhaustive Theorem 5.3 margin for that agent: ${margin} accepted argument${margin===1?"":"s"} at its tightest profile; ${agentAudit.profiles_with_a_tied_best_withholding_report} opponent profiles tie the best hiding report, and none are profitable.`;
      } else {
        finding.className="";
        finding.innerHTML="<div class=\"empty-state\">No condition-fails / strategyproof random instance was found in this run. Example 5.11 above remains a hand-crafted illustration.</div>";
      }
    }

    selectExample("ex10");
    loadExperiments();
  </script>
</body>
</html>
'''


def build_demo(
    summary_path: Path | str | None = None,
    output_path: Path | str | None = None,
    cases_path: Path | str | None = None,
) -> Path:
    """Create the interactive page, embedding results when a summary exists."""

    project_root = Path(__file__).resolve().parent
    summary_file = (
        Path(summary_path).expanduser().resolve()
        if summary_path is not None
        else project_root / "results" / "experiment_summary.json"
    )
    output_file = (
        Path(output_path).expanduser().resolve()
        if output_path is not None
        else project_root / "results" / "argumentation_demo.html"
    )
    cases_file = (
        Path(cases_path).expanduser().resolve()
        if cases_path is not None
        else project_root / "results" / "interesting_cases.json"
    )

    summary: dict[str, Any] | None = None
    if summary_file.exists():
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
    cases: dict[str, Any] | None = None
    if cases_file.exists():
        cases = json.loads(cases_file.read_text(encoding="utf-8"))

    serialized = json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
    serialized = serialized.replace("</", "<\\/")
    cases_serialized = json.dumps(cases, ensure_ascii=False, separators=(",", ":"))
    cases_serialized = cases_serialized.replace("</", "<\\/")
    page = PAGE.replace("__EXPERIMENT_JSON__", serialized).replace(
        "__INTERESTING_CASES__",
        cases_serialized,
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(page, encoding="utf-8")
    print(f"Interactive demo created: {output_file}")
    if summary is None:
        print(f"No experiment summary found at {summary_file}; the example lab will still work.")
    if cases is None:
        print(f"No interesting-case file found at {cases_file}; no random case spotlight will be shown.")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the offline visual assignment demo.")
    parser.add_argument("--summary", type=Path, default=None, help="experiment_summary.json path")
    parser.add_argument("--cases", type=Path, default=None, help="interesting_cases.json path")
    parser.add_argument("--output", type=Path, default=None, help="HTML output path")
    args = parser.parse_args()
    build_demo(args.summary, args.output, args.cases)


if __name__ == "__main__":
    main()
