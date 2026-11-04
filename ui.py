"""Presentation helpers for ``app.py``: theme CSS, the animated graph and HTML widgets."""

from __future__ import annotations

import html
import json
import math
import re

import streamlit as st

AGENT_COLOURS = {"x": "#60a5fa", "y": "#c084fc", "z": "#fb923c"}
LABEL_COLOURS = {"in": "#4ade80", "out": "#f87171", "undec": "#facc15", None: "#cbd5e1"}
LABEL_NAMES = {"in": "in", "out": "out", "undec": "undecided", None: "unlabelled"}

NODE_RADIUS = 23
ARROW_LENGTH = 11
ARROW_WIDTH = 5.5


def esc(value) -> str:
    return html.escape(str(value))


def sort_key(argument):
    return (len(str(argument)), str(argument))


def arg_html(argument) -> str:
    match = re.fullmatch(r"([A-Za-z]+)(\d+)", str(argument))
    if match:
        return f"{esc(match.group(1))}<sub>{esc(match.group(2))}</sub>"
    return esc(argument)


# --------------------------------------------------------------------------- global styling

CSS = """
<style>
:root {
  --ease-out: cubic-bezier(.23, 1, .32, 1);
  --ease-io: cubic-bezier(.77, 0, .175, 1);
  --card: rgba(18, 26, 46, .78);
  --line: #22304d;
  --muted: #8d9cb9;
  --text: #e6edf7;
  --in: #4ade80; --out: #f87171; --undec: #facc15;
  --accent: #818cf8; --accent-2: #22d3ee;
  --mono: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace;
}
@property --n { syntax: '\\3C integer\\3E '; initial-value: 0; inherits: false; }

.stApp {
  background:
    radial-gradient(1100px 520px at 8% -12%, rgba(99, 102, 241, .16), transparent 62%),
    radial-gradient(900px 480px at 100% -5%, rgba(34, 211, 238, .08), transparent 60%),
    #0b1020;
}
[data-testid="stMainBlockContainer"], .block-container { padding-top: 2rem; max-width: 1440px; }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stCaptionContainer"], .stCaption { color: var(--muted); font-size: .84rem; }
[data-testid="stMarkdownContainer"] p { line-height: 1.6; }

/* sidebar */
[data-testid="stSidebar"] { border-right: 1px solid var(--line); }
.brand { display: flex; gap: .75rem; align-items: center; margin: .2rem 0 1.1rem; }
.brand-mark {
  width: 42px; height: 42px; border-radius: 12px; display: grid; place-items: center;
  font-size: 1.35rem; background: linear-gradient(135deg, #6366f1, #22d3ee);
  box-shadow: 0 8px 24px -10px rgba(99, 102, 241, .9);
}
.brand-name { font-family: 'Space Grotesk', sans-serif; font-weight: 700; font-size: 1.15rem; line-height: 1.1; }
.brand-sub { color: var(--muted); font-size: .76rem; margin-top: .15rem; }
.side-note {
  border: 1px solid var(--line); background: rgba(22, 32, 58, .6); border-radius: 12px;
  padding: .8rem .9rem; font-size: .86rem; line-height: 1.55; color: #cdd6e6;
  animation: fadeUp 420ms var(--ease-out) both;
}
.side-stats { display: flex; gap: .4rem; margin-top: .6rem; flex-wrap: wrap; }

/* hero */
.hero { margin: .2rem 0 1.3rem; animation: fadeUp 560ms var(--ease-out) both; }
.kicker {
  font-size: .72rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase;
  color: var(--accent);
}
.hero-title {
  font-family: 'Space Grotesk', sans-serif; font-size: 2.35rem; font-weight: 700;
  letter-spacing: -.02em; line-height: 1.15; margin: .3rem 0 .45rem;
}
.hero-title span {
  background: linear-gradient(90deg, #a5b4fc, #67e8f9 55%, #86efac);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub { color: var(--muted); font-size: .98rem; max-width: 760px; margin: 0; }
.hero-meta { display: flex; gap: .45rem; flex-wrap: wrap; margin-top: .9rem; }

/* tabs as a segmented pill bar */
[role="tablist"] {
  gap: .3rem; padding: .32rem; width: fit-content; border-radius: 14px;
  background: rgba(17, 25, 44, .85); border: 1px solid var(--line) !important; box-shadow: none !important;
}
[role="tablist"]::before, [role="tablist"]::after { display: none !important; }
[data-testid="stTab"] {
  height: auto; padding: .5rem 1.1rem !important; margin: 0 !important; border-radius: 10px; border: 0 !important;
  color: var(--muted); transition: background-color 200ms ease, color 200ms ease;
}
[data-testid="stTab"]::before, [data-testid="stTab"]::after { display: none !important; }
[data-testid="stTab"] p { font-size: .93rem; font-weight: 600; }
@media (hover: hover) and (pointer: fine) { [data-testid="stTab"]:hover { color: var(--text); background: rgba(148, 163, 184, .08); } }
[data-testid="stTab"][aria-selected="true"] {
  background: linear-gradient(135deg, rgba(99, 102, 241, .38), rgba(34, 211, 238, .16));
  color: #fff; box-shadow: inset 0 0 0 1px rgba(129, 140, 248, .35);
}
[data-testid="stTabPanel"] { padding-top: 1.1rem; animation: fadeUp 380ms var(--ease-out) both; }

/* cards: st.container(border=True, key="card-...") */
[class*="st-key-card"] {
  background: var(--card); border: 1px solid var(--line) !important; border-radius: 18px !important;
  box-shadow: 0 18px 40px -28px rgba(0, 0, 0, .9), inset 0 1px 0 rgba(255, 255, 255, .03);
  animation: fadeUp 460ms var(--ease-out) both;
  transition: border-color 220ms ease;
}
[class*="st-key-card"]:hover { border-color: #2f4068 !important; }
@media (max-width: 1200px) {
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [class*="st-key-card"]) { flex-direction: column; }
  [data-testid="stHorizontalBlock"]:has(> [data-testid="stColumn"] [class*="st-key-card"]) > [data-testid="stColumn"] {
    width: 100% !important; flex: 1 1 auto !important;
  }
}

/* buttons */
.stButton button { transition: transform 140ms var(--ease-out), box-shadow 220ms ease, filter 200ms ease; font-weight: 600; }
.stButton button:active { transform: scale(.97); }
.stButton button[kind="primary"], [data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #6366f1, #8b5cf6); border: 0;
  box-shadow: 0 8px 22px -12px rgba(129, 140, 248, .95);
}
@media (hover: hover) and (pointer: fine) {
  .stButton button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover { filter: brightness(1.12); }
}

/* section headings */
.sec { margin: .1rem 0 .55rem; }
.sec-k { font-size: .68rem; font-weight: 600; letter-spacing: .12em; text-transform: uppercase; color: var(--accent); }
.sec-t { font-family: 'Space Grotesk', sans-serif; font-size: 1.12rem; font-weight: 600; margin-top: .1rem; }
.sec-c { color: var(--muted); font-size: .84rem; margin-top: .2rem; line-height: 1.5; }

/* chips and sets */
.chip {
  display: inline-flex; align-items: center; gap: .35rem; padding: .2rem .62rem; border-radius: 999px;
  font-size: .78rem; font-weight: 600; border: 1px solid transparent; white-space: nowrap;
  animation: pop 360ms var(--ease-out) both;
}
.chip .dot { width: .5rem; height: .5rem; border-radius: 50%; background: currentColor; }
.chip.good { color: #86efac; background: rgba(74, 222, 128, .1); border-color: rgba(74, 222, 128, .3); }
.chip.bad { color: #fca5a5; background: rgba(248, 113, 113, .1); border-color: rgba(248, 113, 113, .3); }
.chip.warn { color: #fde047; background: rgba(250, 204, 21, .1); border-color: rgba(250, 204, 21, .3); }
.chip.info { color: #a5b4fc; background: rgba(129, 140, 248, .12); border-color: rgba(129, 140, 248, .32); }
.chip.muted { color: #b6c2d9; background: rgba(148, 163, 184, .08); border-color: rgba(148, 163, 184, .2); }
.chips { display: flex; gap: .45rem; flex-wrap: wrap; align-items: center; }

.set { font-family: var(--mono); font-size: .82rem; color: #64748b; line-height: 1.9; }
.set .brace { color: #64748b; }
.set .arg {
  display: inline-block; padding: 0 .3rem; margin: 0 .02rem; border-radius: 5px; white-space: nowrap;
  background: rgba(148, 163, 184, .12); color: #e2e8f0; line-height: 1.5;
}
.set .arg.new { background: rgba(74, 222, 128, .2); color: #bbf7d0; box-shadow: 0 0 0 1px rgba(74, 222, 128, .45); }
.set .arg.in { background: rgba(74, 222, 128, .16); color: #bbf7d0; }
.set.empty { color: #64748b; }
sub { font-size: .72em; }

/* tables */
.tbl-wrap { overflow: auto; border-radius: 12px; border: 1px solid var(--line); }
table.tbl { width: 100%; border-collapse: collapse; font-size: .88rem; }
.tbl th {
  position: sticky; top: 0; background: #131c33; text-align: left; font-size: .68rem; font-weight: 600;
  letter-spacing: .08em; text-transform: uppercase; color: var(--muted); padding: .55rem .75rem;
  border-bottom: 1px solid var(--line);
}
.tbl td { padding: .5rem .75rem; border-bottom: 1px solid rgba(34, 48, 77, .6); vertical-align: middle; }
.tbl tr:last-child td { border-bottom: 0; }
.tbl tbody tr { animation: fadeUp 360ms var(--ease-out) both; animation-delay: calc(var(--r, 0) * 32ms); }
@media (hover: hover) and (pointer: fine) { .tbl tbody tr:hover td { background: rgba(129, 140, 248, .06); } }
.tbl tr.hl td { background: rgba(129, 140, 248, .1); }
.tbl tr.hl td:first-child { box-shadow: inset 3px 0 0 var(--accent); }
.tbl .num { font-variant-numeric: tabular-nums; font-weight: 600; }
.lab { display: inline-block; min-width: 3.1rem; text-align: center; padding: .12rem .45rem; border-radius: 6px; font-size: .76rem; font-weight: 600; }
.lab.in { background: rgba(74, 222, 128, .16); color: #86efac; }
.lab.out { background: rgba(248, 113, 113, .14); color: #fca5a5; }
.lab.undec { background: rgba(250, 204, 21, .14); color: #fde047; }
.delta { font-weight: 700; font-variant-numeric: tabular-nums; }
.delta.up { color: #86efac; } .delta.down { color: #fca5a5; } .delta.zero { color: #64748b; }

/* step-by-step fixed point */
.steps { display: flex; flex-direction: column; gap: .45rem; }
.step {
  display: flex; flex-wrap: wrap; align-items: center; gap: .4rem .8rem; padding: .55rem .75rem; border-radius: 12px;
  background: rgba(15, 23, 42, .55); border: 1px solid var(--line);
  animation: fadeUp 420ms var(--ease-out) both; animation-delay: calc(var(--r) * 110ms);
}
.step .k { font-family: 'Space Grotesk', sans-serif; font-weight: 600; font-size: .9rem; color: var(--accent); min-width: 3.4rem; }
.step.fixed { border-color: rgba(74, 222, 128, .45); background: rgba(74, 222, 128, .07); }
.step .tag { margin-left: auto; }

/* callouts */
.callout {
  display: flex; gap: .8rem; padding: .85rem 1rem; border-radius: 14px; border: 1px solid;
  font-size: .9rem; line-height: 1.55; animation: fadeUp 420ms var(--ease-out) both;
}
.callout .ico { font-size: 1.1rem; line-height: 1.4; }
.callout b { font-weight: 650; }
.callout.good { background: rgba(74, 222, 128, .07); border-color: rgba(74, 222, 128, .3); }
.callout.bad { background: rgba(248, 113, 113, .08); border-color: rgba(248, 113, 113, .35); }
.callout.info { background: rgba(129, 140, 248, .08); border-color: rgba(129, 140, 248, .3); }
.callout.warn { background: rgba(250, 204, 21, .07); border-color: rgba(250, 204, 21, .3); }

/* verdict tiles */
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .55rem; }
.tile {
  padding: .7rem .85rem; border-radius: 14px; border: 1px solid var(--line); background: rgba(15, 23, 42, .55);
  animation: fadeUp 420ms var(--ease-out) both; animation-delay: calc(var(--r, 0) * 60ms);
}
.tile .t-l { font-size: .72rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; font-weight: 600; }
.tile .t-v { font-family: 'Space Grotesk', sans-serif; font-size: 1.35rem; font-weight: 700; margin-top: .15rem; }
.tile .t-s { font-size: .78rem; color: var(--muted); margin-top: .1rem; }
.tile.good { border-color: rgba(74, 222, 128, .35); } .tile.good .t-v { color: #86efac; }
.tile.bad { border-color: rgba(248, 113, 113, .35); } .tile.bad .t-v { color: #fca5a5; }
.tile.info .t-v { color: #a5b4fc; }
.count { animation: count 1300ms var(--ease-out) both; counter-reset: n var(--n); }
.count::after { content: counter(n); }

/* charts */
.q1 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; }
.q1-panel { padding: .9rem 1rem .6rem; border-radius: 14px; border: 1px solid var(--line); background: rgba(15, 23, 42, .5); }
.q1-title { font-weight: 600; font-size: .9rem; margin-bottom: .6rem; }
.q1-plot { position: relative; height: 210px; display: flex; justify-content: space-around; align-items: stretch; margin: 1.4rem 0 2rem 2.2rem; }
.q1-grid { position: absolute; inset: 0; pointer-events: none; }
.q1-grid div { position: absolute; left: 0; right: 0; border-top: 1px dashed rgba(148, 163, 184, .14); }
.q1-grid span { position: absolute; left: -2.3rem; top: -.55rem; font-size: .68rem; color: #64748b; width: 2rem; text-align: right; }
.q1-group { position: relative; display: flex; flex-direction: column; align-items: center; }
.q1-bars { flex: 1; display: flex; gap: .45rem; align-items: stretch; }
.q1-col { position: relative; width: 38px; }
.q1-bar {
  position: absolute; left: 0; right: 0; bottom: 0; height: calc(var(--h) * 100%); border-radius: 8px 8px 3px 3px;
  transform-origin: bottom; animation: growY 900ms var(--ease-out) both; animation-delay: calc(var(--i) * 80ms);
}
.q1-bar.sp { background: linear-gradient(180deg, #34d399, #059669); box-shadow: 0 0 18px -6px rgba(52, 211, 153, .7); }
.q1-bar.cond { background: linear-gradient(180deg, #a5b4fc, #6366f1); box-shadow: 0 0 18px -6px rgba(129, 140, 248, .7); }
.q1-val {
  position: absolute; left: 50%; bottom: calc(var(--h) * 100% + 6px); transform: translateX(-50%);
  font-size: .72rem; font-weight: 600; color: #cbd5e1; white-space: nowrap;
  animation: fadeIn 500ms ease both; animation-delay: calc(500ms + var(--i) * 80ms);
}
.q1-ci {
  position: absolute; left: 50%; width: 2px; margin-left: -1px; background: #fbbf24;
  bottom: calc(var(--lo) * 100%); height: calc((var(--hi) - var(--lo)) * 100%);
  animation: fadeIn 400ms ease both; animation-delay: calc(800ms + var(--i) * 80ms);
}
.q1-ci::before, .q1-ci::after { content: ""; position: absolute; left: -5px; width: 12px; height: 2px; background: #fbbf24; }
.q1-ci::before { top: 0; } .q1-ci::after { bottom: 0; }
.q1-x { position: absolute; top: calc(100% + .5rem); white-space: nowrap; font-size: .78rem; color: var(--muted); font-family: var(--mono); }
.legend-row { display: flex; gap: 1rem; flex-wrap: wrap; font-size: .78rem; color: var(--muted); margin-top: .7rem; }
.legend-row i { display: inline-block; width: .7rem; height: .7rem; border-radius: 3px; margin-right: .35rem; vertical-align: -1px; }

.hbars { display: flex; flex-direction: column; gap: .6rem; }
.hbar { display: grid; grid-template-columns: minmax(180px, 1.1fr) 3fr 3.2rem; gap: .8rem; align-items: center; font-size: .86rem; }
.hbar-track { height: 12px; border-radius: 999px; background: rgba(148, 163, 184, .1); overflow: hidden; }
.hbar-fill {
  height: 100%; width: calc(var(--w) * 100%); border-radius: 999px;
  background: linear-gradient(90deg, #6366f1, #22d3ee); transform-origin: left;
  animation: growX 900ms var(--ease-out) both; animation-delay: calc(var(--i) * 90ms);
}
.hbar-n { text-align: right; font-weight: 700; font-variant-numeric: tabular-nums; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes pop { from { opacity: 0; transform: scale(.92); } to { opacity: 1; transform: none; } }
@keyframes growY { from { transform: scaleY(0); } to { transform: scaleY(1); } }
@keyframes growX { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes count { from { --n: 0; } to { --n: var(--target); } }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 1ms !important; animation-delay: 0ms !important; transition-duration: 1ms !important; }
}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


# --------------------------------------------------------------------------- small widgets

def render(markup: str) -> None:
    st.html(markup)


def chip(text, tone: str = "muted", dot: bool = False) -> str:
    return f'<span class="chip {tone}">{"<span class=dot></span>" if dot else ""}{text}</span>'


def agent_chip(agent, short: bool = False) -> str:
    colour = AGENT_COLOURS.get(agent, "#94a3b8")
    text = esc(agent) if short else f"agent {esc(agent)}"
    return (f'<span class="chip agent" style="color:{colour};border-color:{colour}55;'
            f'background:{colour}1a"><span class="dot"></span>{text}</span>')


def set_html(arguments, highlight=(), tone: str = "new") -> str:
    items = sorted(arguments, key=sort_key)
    if not items:
        return '<span class="set empty">∅</span>'
    marked = set(highlight)
    body = ",".join(
        f'<span class="arg{" " + tone if a in marked else ""}">{arg_html(a)}</span>' for a in items
    )
    return f'<span class="set"><span class="brace">{{</span>{body}<span class="brace">}}</span></span>'


def label_html(label) -> str:
    return f'<span class="lab {esc(label)}">{esc(label)}</span>'


def delta_html(value: int) -> str:
    tone = "up" if value > 0 else "down" if value < 0 else "zero"
    return f'<span class="delta {tone}">{value:+d}</span>'


def section(title: str, kicker: str | None = None, caption: str | None = None) -> None:
    parts = ['<div class="sec">']
    if kicker:
        parts.append(f'<div class="sec-k">{esc(kicker)}</div>')
    parts.append(f'<div class="sec-t">{title}</div>')
    if caption:
        parts.append(f'<div class="sec-c">{caption}</div>')
    parts.append("</div>")
    render("".join(parts))


def callout(tone: str, body: str) -> None:
    icons = {"good": "✓", "bad": "⚠", "info": "ℹ", "warn": "◆"}
    render(f'<div class="callout {tone}"><span class="ico">{icons[tone]}</span><div>{body}</div></div>')


def table(columns, rows, *, highlight=(), max_height: int | None = None) -> None:
    head = "".join(f"<th>{esc(c)}</th>" for c in columns)
    body = []
    for index, row in enumerate(rows):
        cls = ' class="hl"' if index in highlight else ""
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body.append(f'<tr{cls} style="--r:{min(index, 14)}">{cells}</tr>')
    style = f' style="max-height:{max_height}px"' if max_height else ""
    render(
        f'<div class="tbl-wrap"{style}><table class="tbl"><thead><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}</tbody></table></div>'
    )


def tiles(items) -> None:
    """``items``: (label, value, sub, tone). Integer values count up."""
    cells = []
    for index, (label, value, sub, tone) in enumerate(items):
        if isinstance(value, int):
            shown = f'<span class="count" style="--target:{value}"></span>'
        else:
            shown = esc(value)
        cells.append(
            f'<div class="tile {tone}" style="--r:{index}"><div class="t-l">{esc(label)}</div>'
            f'<div class="t-v">{shown}</div><div class="t-s">{sub}</div></div>'
        )
    render(f'<div class="tiles">{"".join(cells)}</div>')


def hero(source: str, n_arguments: int, n_attacks: int, agents) -> None:
    meta = [chip(esc(source), "info")]
    if n_arguments:
        meta.append(chip(f"{n_arguments} arguments", "muted"))
        meta.append(chip(f"{n_attacks} attacks", "muted"))
    if agents:
        meta.append(chip(f"agents {' · '.join(agents)}", "muted"))
    render(
        '<div class="hero"><div class="kicker">CSL7650 Autonomous Systems · Assignment 3</div>'
        '<div class="hero-title">Argumentation <span>among agents</span></div>'
        '<p class="hero-sub">Dung semantics, the grounded direct argumentation mechanism and '
        'Theorems 5.3 &amp; 5.4 — Weiss, <em>Multiagent Systems</em>, Chapter 5.</p>'
        f'<div class="hero-meta">{"".join(meta)}</div></div>'
    )


def brand() -> None:
    st.sidebar.html(
        '<div class="brand"><div class="brand-mark">⚖</div><div>'
        '<div class="brand-name">Argumentation Lab</div>'
        '<div class="brand-sub">CSL7650 · Assignment 3</div></div></div>'
    )


def side_note(note: str, n_arguments: int, n_attacks: int) -> None:
    stats = ""
    if n_arguments:
        stats = (f'<div class="side-stats">{chip(f"{n_arguments} arguments")}'
                 f'{chip(f"{n_attacks} attacks")}</div>')
    st.sidebar.html(f'<div class="side-note">{esc(note)}{stats}</div>')


def q1_chart(panels) -> None:
    """``panels``: list of (title, rows) with rows (p, sp, lo, hi, cond)."""
    grid = "".join(
        f'<div style="top:{100 - v}%"><span>{v}%</span></div>' for v in (0, 25, 50, 75, 100)
    )
    out = []
    index = 0
    for title, rows in panels:
        groups = []
        for p, sp, lo, hi, cond in rows:
            groups.append(
                '<div class="q1-group"><div class="q1-bars">'
                f'<div class="q1-col" style="--h:{sp:.4f};--lo:{lo:.4f};--hi:{hi:.4f};--i:{index}" '
                f'title="strategyproof {sp:.1%} (95% CI {lo:.1%}–{hi:.1%})">'
                f'<div class="q1-bar sp"></div><div class="q1-ci"></div>'
                f'<div class="q1-val">{sp:.1%}</div></div>'
                f'<div class="q1-col" style="--h:{cond:.4f};--i:{index + 1}" '
                f'title="Theorem 5.4 condition holds {cond:.1%}">'
                f'<div class="q1-bar cond"></div><div class="q1-val">{cond:.1%}</div></div>'
                f'</div><div class="q1-x">p = {p:.2f}</div></div>'
            )
            index += 2
        out.append(
            f'<div class="q1-panel"><div class="q1-title">{esc(title)}</div>'
            f'<div class="q1-plot"><div class="q1-grid">{grid}</div>{"".join(groups)}</div></div>'
        )
    legend_row = (
        '<div class="legend-row"><span><i style="background:#10b981"></i>strategyproof</span>'
        '<span><i style="background:#6366f1"></i>Theorem 5.4 condition holds</span>'
        '<span><i style="background:#fbbf24;width:2px;height:.8rem"></i>95 % Wilson interval</span></div>'
    )
    render(f'<div class="q1">{"".join(out)}</div>{legend_row}')


def hbars(rows) -> None:
    """``rows``: (label, value)."""
    top = max((v for _, v in rows), default=1) or 1
    cells = "".join(
        f'<div class="hbar"><div>{esc(label)}</div><div class="hbar-track">'
        f'<div class="hbar-fill" style="--w:{value / top:.4f};--i:{i}"></div></div>'
        f'<div class="hbar-n">{value}</div></div>'
        for i, (label, value) in enumerate(rows)
    )
    render(f'<div class="hbars">{cells}</div>')


# --------------------------------------------------------------------------- graph layout

def _layout(nodes, attacks):
    """Layered left-to-right layout for sparse graphs, a circle for dense or cyclic ones."""
    edges = sorted({(s, t) for s, t in attacks if s != t})
    succ = {n: [] for n in nodes}
    indegree = {n: 0 for n in nodes}
    for s, t in edges:
        succ[s].append(t)
        indegree[t] += 1

    state, back = {}, set()

    def visit(node):
        state[node] = 1
        for target in succ[node]:
            if state.get(target) == 1:
                back.add((node, target))
            elif target not in state:
                visit(target)
        state[node] = 2

    for node in sorted(nodes, key=lambda n: (indegree[n] > 0, sort_key(n))):
        if node not in state:
            visit(node)

    layered = len(back) <= 2 and len(edges) <= 1.5 * max(len(nodes), 1)
    if layered:
        dag = [e for e in edges if e not in back]
        rank = {n: 0 for n in nodes}
        for _ in nodes:
            changed = False
            for s, t in dag:
                if rank[t] < rank[s] + 1:
                    rank[t] = rank[s] + 1
                    changed = True
            if not changed:
                break
        layers = {}
        for node in nodes:
            layers.setdefault(rank[node], []).append(node)
        neighbours = {n: set() for n in nodes}
        for s, t in dag:
            neighbours[s].add(t)
            neighbours[t].add(s)
        order = {n: i for layer in layers.values() for i, n in enumerate(layer)}
        ranks = sorted(layers)
        for sweep in range(4):
            sequence = ranks[1:] if sweep % 2 == 0 else list(reversed(ranks[:-1]))
            for r in sequence:
                adjacent = r - 1 if sweep % 2 == 0 else r + 1

                def barycentre(node):
                    linked = [order[m] for m in neighbours[node] if rank[m] == adjacent]
                    return sum(linked) / len(linked) if linked else order[node]

                layers[r].sort(key=barycentre)
                for i, node in enumerate(layers[r]):
                    order[node] = i
        positions, outward = {}, {}
        for r, layer in layers.items():
            for i, node in enumerate(layer):
                positions[node] = (r * 132.0, (i - (len(layer) - 1) / 2) * 92.0)
                outward[node] = (0.0, -1.0)
        return positions, outward, rank

    count = len(nodes)
    radius = max(95.0, 118.0 / (2 * math.sin(math.pi / count))) if count > 1 else 0.0
    positions, outward = {}, {}
    for i, node in enumerate(nodes):
        angle = -math.pi / 2 + 2 * math.pi * i / count
        positions[node] = (radius * math.cos(angle), radius * math.sin(angle))
        outward[node] = (math.cos(angle), math.sin(angle)) if count > 1 else (0.0, -1.0)
    return positions, outward, None


def _towards(origin, target, distance):
    dx, dy = target[0] - origin[0], target[1] - origin[1]
    length = math.hypot(dx, dy) or 1.0
    return origin[0] + dx / length * distance, origin[1] + dy / length * distance


def _arrow(tip, direction_from):
    dx, dy = tip[0] - direction_from[0], tip[1] - direction_from[1]
    length = math.hypot(dx, dy) or 1.0
    ux, uy = dx / length, dy / length
    bx, by = tip[0] - ux * ARROW_LENGTH, tip[1] - uy * ARROW_LENGTH
    px, py = -uy * ARROW_WIDTH, ux * ARROW_WIDTH
    points = f"{tip[0]:.1f},{tip[1]:.1f} {bx + px:.1f},{by + py:.1f} {bx - px:.1f},{by - py:.1f}"
    return points, (bx, by)


def _edge_shapes(source, target, positions, outward, rank, edge_set):
    r = NODE_RADIUS
    if source == target:
        x, y = positions[source]
        ux, uy = outward[source]
        vx, vy = -uy, ux

        def around(angle, distance):
            c, s = math.cos(angle), math.sin(angle)
            return x + distance * (ux * c + vx * s), y + distance * (uy * c + vy * s)

        start, tip = around(-0.62, r + 2), around(0.62, r + 2)
        c1 = (x + ux * (r + 46) - vx * 30, y + uy * (r + 46) - vy * 30)
        c2 = (x + ux * (r + 46) + vx * 30, y + uy * (r + 46) + vy * 30)
        points, base = _arrow(tip, c2)
        d = (f"M{start[0]:.1f},{start[1]:.1f} C{c1[0]:.1f},{c1[1]:.1f} "
             f"{c2[0]:.1f},{c2[1]:.1f} {base[0]:.1f},{base[1]:.1f}")
        return d, points

    p, q = positions[source], positions[target]
    curvature = 0.0
    if (target, source) in edge_set:
        curvature = 0.17
    elif rank is not None and (rank[target] <= rank[source] or rank[target] - rank[source] > 1):
        curvature = 0.3
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    control = ((p[0] + q[0]) / 2 + nx * curvature * length, (p[1] + q[1]) / 2 + ny * curvature * length)
    start = _towards(p, control, r + 2)
    tip = _towards(q, control, r + 3)
    points, base = _arrow(tip, control)
    d = (f"M{start[0]:.1f},{start[1]:.1f} Q{control[0]:.1f},{control[1]:.1f} "
         f"{base[0]:.1f},{base[1]:.1f}")
    return d, points


# --------------------------------------------------------------------------- graph component

GRAPH_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap" rel="stylesheet">
<style>
:root { --eo: cubic-bezier(.23,1,.32,1); --eio: cubic-bezier(.77,0,.175,1); }
html, body { margin: 0; background: transparent; font-family: Inter, ui-sans-serif, system-ui, sans-serif; color: #e6edf7; overflow: hidden; }
.wrap { position: relative; }
svg { display: block; width: 100%; height: auto; margin: 0 auto; overflow: visible; }
.edge { fill: none; stroke: #64748b; stroke-width: 2.2; stroke-linecap: round; transition: opacity 260ms ease, stroke 260ms ease; }
.head { fill: #64748b; transition: opacity 260ms ease, fill 260ms ease; }
.edge.dim { stroke: #3b4a66; stroke-dasharray: .02 .035; }
.head.dim { fill: #334155; }
.edge.hot { stroke: #fb7185; stroke-width: 3.6; filter: drop-shadow(0 0 6px rgba(251,113,133,.55)); }
.head.hot { fill: #fb7185; }
.flow { fill: none; stroke: #fff1f2; stroke-width: 2; stroke-linecap: round; stroke-dasharray: .035 .085; opacity: .85; animation: flow 1.1s linear infinite; pointer-events: none; }
@keyframes flow { to { stroke-dashoffset: -.12; } }
.node { cursor: default; transition: opacity 320ms ease; }
.node .body { transform-box: fill-box; transform-origin: center; }
.disc { stroke-width: 3; transition: fill 560ms var(--eio), stroke 300ms ease; }
.node.hidden .disc { fill: #0f172a !important; stroke-dasharray: 5 4; }
.node.hidden .lbl { fill: #94a3b8; }
.node.hidden { opacity: .55; }
.lbl { font-size: 17px; font-weight: 700; fill: #0b1020; text-anchor: middle; dominant-baseline: central; pointer-events: none; letter-spacing: -.01em; }
.lbl tspan.sub { font-size: 11.5px; font-weight: 700; }
.badge circle { stroke: #0b1020; stroke-width: 2.5; }
.badge text { font-size: 10.5px; font-weight: 700; fill: #0b1020; text-anchor: middle; dominant-baseline: central; }
.halo { fill: none; stroke: #e0e7ff; stroke-width: 2; stroke-dasharray: 4 4; opacity: .9; }
.glow { opacity: .0; transition: opacity 400ms ease; }
.node.in .glow { opacity: .55; }
.ripple { fill: none; stroke-width: 2.5; opacity: 0; transform-box: fill-box; transform-origin: center; }

.enter .node .body { animation: nodeIn 560ms var(--eo) both; animation-delay: calc(var(--i) * 60ms); }
.enter .edge:not(.dim) { stroke-dasharray: 1; animation: draw 620ms var(--eio) both; animation-delay: calc(240ms + var(--i) * 45ms); }
.enter .edge.dim, .enter .flow { animation: fadeIn 400ms ease both; animation-delay: calc(500ms + var(--i) * 45ms); }
.enter .head { animation: fadeIn 260ms ease both; animation-delay: calc(760ms + var(--i) * 45ms); }
.node.changed .body { animation: bump 560ms var(--eo) 80ms both; }
.node.changed .ripple { animation: ripple 760ms var(--eo) 80ms both; }
.halo.new { animation: haloIn 360ms var(--eo) both; transform-box: fill-box; transform-origin: center; }
.edge.fresh, .head.fresh { animation: fadeIn 380ms ease both; }
@keyframes nodeIn { from { opacity: 0; transform: scale(.82); } to { opacity: 1; transform: none; } }
@keyframes draw { from { stroke-dashoffset: 1; } to { stroke-dashoffset: 0; } }
@keyframes fadeIn { from { opacity: 0; } }
@keyframes bump { 0% { transform: scale(1); } 40% { transform: scale(1.13); } 100% { transform: scale(1); } }
@keyframes ripple { from { opacity: .7; transform: scale(1); } to { opacity: 0; transform: scale(1.75); } }
@keyframes haloIn { from { opacity: 0; transform: scale(.85); } }

.focus .node:not(.lit) { opacity: .28; }
.focus .edge:not(.lit), .focus .head:not(.lit), .focus .flow:not(.lit) { opacity: .1; }
.edge.lit.from { stroke: #fbbf24; } .head.lit.from { fill: #fbbf24; }
.edge.lit.to { stroke: #e2e8f0; } .head.lit.to { fill: #e2e8f0; }

.legend { display: flex; justify-content: center; flex-wrap: wrap; gap: 14px; font-size: 12.5px; color: #93a3bf; padding: 6px 0 2px; }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.sw { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
.sw.ring { background: transparent; border: 2.5px solid; width: 8px; height: 8px; }
.sw.line { width: 18px; height: 3px; border-radius: 2px; }
.tip {
  position: absolute; pointer-events: none; background: rgba(15,23,42,.96); border: 1px solid #2b3a5c;
  border-radius: 10px; padding: 8px 10px; font-size: 12px; line-height: 1.5; color: #dbe4f3; white-space: nowrap;
  opacity: 0; transform: translate(-50%, calc(-100% - 6px)) scale(.97); transform-origin: bottom center;
  transition: opacity 140ms ease, transform 160ms var(--eo); box-shadow: 0 12px 28px -12px rgba(0,0,0,.9);
}
.tip.on { opacity: 1; transform: translate(-50%, calc(-100% - 10px)); }
.tip.below { transform: translate(-50%, 6px) scale(.97); transform-origin: top center; }
.tip.below.on { transform: translate(-50%, 10px); }
.tip b { color: #fff; }
@media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
</style></head><body>
<div class="wrap"><svg id="g" viewBox="__VIEWBOX__" style="max-width:__MAXW__px" preserveAspectRatio="xMidYMid meet">
<defs>
  <radialGradient id="shine" cx="35%" cy="28%" r="75%">
    <stop offset="0%" stop-color="#fff" stop-opacity=".55"/><stop offset="55%" stop-color="#fff" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="7"/></filter>
</defs>
__EDGES__
__NODES__
</svg><div class="tip" id="tip"></div></div>
<div class="legend">__LEGEND__</div>
<script>
const DATA = __DATA__;
const svg = document.getElementById("g");
const store = (() => { try { return (window.parent.__afGraphs = window.parent.__afGraphs || {}); } catch (e) { return {}; } })();
const prev = store[DATA.key];
if (prev && prev.sig === DATA.sig) {
  document.body.classList.add("still");
  const discs = [];
  for (const g of svg.querySelectorAll(".node")) {
    const id = g.dataset.id, now = DATA.nodes[id], was = prev.nodes[id];
    const disc = g.querySelector(".disc");
    if (was && (was.fill !== now.fill || was.hidden !== now.hidden)) {
      disc.style.transition = "none";
      disc.style.fill = was.fill;
      discs.push([disc, now.fill]);
      g.classList.add("changed");
    }
    const halo = g.querySelector(".halo");
    if (halo && !(was && was.selected)) halo.classList.add("new");
  }
  for (const e of svg.querySelectorAll(".edge, .head")) {
    if (prev.edges[e.dataset.e] !== DATA.edges[e.dataset.e]) e.classList.add("fresh");
  }
  svg.getBoundingClientRect();
  requestAnimationFrame(() => requestAnimationFrame(() => {
    for (const [disc, fill] of discs) { disc.style.transition = ""; disc.style.fill = fill; }
  }));
} else {
  svg.classList.add("enter");
}
store[DATA.key] = { sig: DATA.sig, nodes: DATA.nodes, edges: DATA.edges };

const tip = document.getElementById("tip");
const wrap = document.querySelector(".wrap");
if (matchMedia("(hover: hover)").matches) {
  for (const g of svg.querySelectorAll(".node")) {
    g.addEventListener("mouseenter", () => {
      const id = g.dataset.id, info = DATA.nodes[id];
      svg.classList.add("focus");
      g.classList.add("lit");
      for (const e of svg.querySelectorAll("[data-e]")) {
        const [s, t] = JSON.parse(e.dataset.e);
        if (s === id || t === id) {
          e.classList.add("lit", s === id ? "from" : "to");
          const other = svg.querySelector(`.node[data-id="${CSS.escape(s === id ? t : s)}"]`);
          if (other) other.classList.add("lit");
        }
      }
      tip.innerHTML = info.tip;
      const box = g.querySelector(".disc").getBoundingClientRect(), outer = wrap.getBoundingClientRect();
      const below = box.top - outer.top < 96;
      tip.classList.toggle("below", below);
      tip.style.left = Math.min(Math.max(box.left + box.width / 2 - outer.left, 110), outer.width - 110) + "px";
      tip.style.top = (below ? box.bottom - outer.top : box.top - outer.top) + "px";
      tip.classList.add("on");
    });
    g.addEventListener("mouseleave", () => {
      svg.classList.remove("focus");
      for (const el of svg.querySelectorAll(".lit")) el.classList.remove("lit", "from", "to");
      tip.classList.remove("on");
    });
  }
}
</script></body></html>"""


def graph(
    key: str,
    arguments,
    attacks,
    *,
    owners=None,
    labels=None,
    hidden=(),
    path=(),
    selected=(),
) -> None:
    """Animated SVG argument graph. ``path`` edges glow red; labelling changes morph in place."""
    nodes = sorted(arguments, key=sort_key)
    if not nodes:
        return
    owners = owners or {}
    labels = labels or {}
    hidden, selected = set(hidden), set(selected)
    attacks = sorted(set(attacks), key=lambda e: (sort_key(e[0]), sort_key(e[1])))
    edge_set = set(attacks)
    path_edges = set(zip(path, path[1:]))
    positions, outward, rank = _layout(nodes, attacks)

    r = NODE_RADIUS
    xs, ys = [], []
    for node, (x, y) in positions.items():
        ux, uy = outward[node]
        loop = (r + 40) if (node, node) in edge_set else r + 6
        xs += [x - r - 8, x + r + 8, x + ux * loop]
        ys += [y - r - 8, y + r + 8, y + uy * loop]
    pad = 18
    min_x, max_x = min(xs) - pad, max(xs) + pad
    min_y, max_y = min(ys) - pad, max(ys) + pad
    width, height = max_x - min_x, max_y - min_y

    order = {n: i for i, n in enumerate(sorted(nodes, key=lambda n: (positions[n][0], positions[n][1])))}

    edge_parts, edge_state = [], {}
    for index, (source, target) in enumerate(attacks):
        d, points = _edge_shapes(source, target, positions, outward, rank, edge_set)
        classes = []
        if (source, target) in path_edges:
            classes.append("hot")
        if source in hidden or target in hidden:
            classes.append("dim")
        cls = " ".join(classes)
        ident = esc(json.dumps([str(source), str(target)]))
        edge_state[json.dumps([str(source), str(target)])] = cls
        edge_parts.append(
            f'<path class="edge {cls}" data-e="{ident}" d="{d}" pathLength="1" style="--i:{index}"/>'
        )
        if "hot" in classes:
            edge_parts.append(f'<path class="flow" data-e="{ident}" d="{d}" pathLength="1"/>')
        edge_parts.append(f'<polygon class="head {cls}" data-e="{ident}" points="{points}" style="--i:{index}"/>')

    attackers = {n: sorted((s for s, t in attacks if t == n), key=sort_key) for n in nodes}
    targets = {n: sorted((t for s, t in attacks if s == n), key=sort_key) for n in nodes}

    node_parts, node_state = [], {}
    for node in nodes:
        x, y = positions[node]
        label = labels.get(node)
        fill = LABEL_COLOURS.get(label, LABEL_COLOURS[None])
        owner = owners.get(node)
        stroke = AGENT_COLOURS.get(owner, "#94a3b8") if owner else "rgba(15,23,42,.65)"
        is_hidden = node in hidden
        classes = ["node", label or "none"] + (["hidden"] if is_hidden else [])
        match = re.fullmatch(r"([A-Za-z]+)(\d+)", str(node))
        if match:
            text = f'{esc(match.group(1))}<tspan class="sub" dy="4">{esc(match.group(2))}</tspan>'
        else:
            text = esc(node)
        badge = ""
        if owner:
            bx, by = r * 0.74, -r * 0.74
            badge = (f'<g class="badge" transform="translate({bx:.1f},{by:.1f})">'
                     f'<circle r="9" fill="{stroke}"/><text y="0.5">{esc(owner)}</text></g>')
        halo = f'<circle class="halo" r="{r + 7}"/>' if node in selected else ""
        tip_lines = [f"<b>{esc(node)}</b> · {LABEL_NAMES.get(label, 'unlabelled')}"]
        if owner:
            tip_lines.append(f"owned by agent <b>{esc(owner)}</b>")
        if is_hidden:
            tip_lines.append("withheld by its owner")
        tip_lines.append("attacks " + (", ".join(map(esc, targets[node])) or "nothing"))
        tip_lines.append("attacked by " + (", ".join(map(esc, attackers[node])) or "nobody"))
        node_state[str(node)] = {
            "fill": fill, "hidden": is_hidden, "selected": node in selected,
            "tip": "<br>".join(tip_lines),
        }
        node_parts.append(
            f'<g class="{" ".join(classes)}" data-id="{esc(node)}" transform="translate({x:.1f},{y:.1f})" '
            f'style="--i:{order[node]}"><g class="body">'
            f'<circle class="glow" r="{r}" fill="{fill}" filter="url(#soft)"/>'
            f'<circle class="ripple" r="{r}" stroke="{fill}"/>{halo}'
            f'<circle class="disc" r="{r}" style="fill:{fill}" stroke="{stroke}"/>'
            f'<circle r="{r - 1.5}" fill="url(#shine)" pointer-events="none"/>'
            f'<text class="lbl">{text}</text>{badge}</g></g>'
        )

    present = {labels.get(n) for n in nodes}
    legend_items = [
        f'<span><i class="sw" style="background:{LABEL_COLOURS[k]}"></i>{LABEL_NAMES[k]}</span>'
        for k in ("in", "out", "undec") if k in present
    ]
    if hidden:
        legend_items.append('<span><i class="sw ring" style="border-color:#64748b;border-style:dashed"></i>withheld</span>')
    if selected:
        legend_items.append('<span><i class="sw ring" style="border-color:#e0e7ff;border-style:dashed"></i>set S</span>')
    for agent in sorted({o for o in owners.values() if o}):
        legend_items.append(
            f'<span><i class="sw" style="background:{AGENT_COLOURS.get(agent, "#94a3b8")}"></i>agent {esc(agent)}</span>'
        )
    if path_edges:
        legend_items.append('<span><i class="sw line" style="background:#fb7185"></i>odd path</span>')

    signature = json.dumps([[str(n) for n in nodes], [[str(s), str(t)] for s, t in attacks],
                            {str(k): v for k, v in owners.items()}])
    data = {"key": key, "sig": signature, "nodes": node_state, "edges": edge_state}
    document = (
        GRAPH_TEMPLATE
        .replace("__VIEWBOX__", f"{min_x:.1f} {min_y:.1f} {width:.1f} {height:.1f}")
        .replace("__MAXW__", f"{width * 1.25:.0f}")
        .replace("__EDGES__", "\n".join(edge_parts))
        .replace("__NODES__", "\n".join(node_parts))
        .replace("__LEGEND__", "".join(legend_items))
        .replace("__DATA__", json.dumps(data).replace("</", "<\\/"))
    )
    st.iframe(document, height="content")
