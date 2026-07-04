"""
Streamlit UI for the NSPF Star-Rating Estimator (Elementary / Middle / High).
Implements the 2024-25 NSPF Manual (v8-15-2025). Inputs are labeled and grouped
to match the line items on an official NSPF school rating report.

Run locally:   streamlit run NSPF_Star_Rating_Estimator.py
Deploy:        push to GitHub, then set this file as the main file in Streamlit Community
               Cloud (Manage app -> Settings -> Main file path).
"""

from pathlib import Path
import streamlit as st
from nspf_engine import LEVELS, compute

st.set_page_config(page_title="NSPF Star-Rating Estimator", layout="wide")

st.title("NSPF Star-Rating Estimator")
st.caption("Elementary, Middle & High · implements the 2024-25 NSPF Manual (v8-15-2025)")

st.info(
    "Pick a school level, then enter the rates from a school rating report's front page. "
    "Each field is named as it appears on the report. **Use only aggregate, school-level "
    "numbers** — never individual student data. This is an estimate, not an official NDE rating."
)

METHODOLOGY_URL = "https://github.com/andydagoated/nspf/blob/main/METHODOLOGY.md"  # update to your repo path

st.success(
    "**Fidelity of this algorithm.** It implements the official 2024-25 NSPF Manual "
    "(v8-15-2025) for all three school levels — the same indicator weights, Point Attribution "
    "Tables, truncation rule (§1.3), and star cut scores — and computes the Total Index Score "
    "exactly as the manual defines it (§1.2.2). It reproduces published 2024-25 ratings exactly, "
    "including every component and measure-level point value: Carroll M Johnston STEM Academy "
    "(middle, 51.5 → ★★★) and Amplus Academy–Durango (middle, 88 → ★★★★★, including the chronic-"
    "absenteeism incentive path). This is a transparent calculation — no AI, no hidden logic — "
    "not a prediction, and not an official NDE rating."
)
st.markdown(f"**Methodology:** [open the full methodology document]({METHODOLOGY_URL}) "
            "· or read it on this page below.")
with st.expander("How the rating is calculated — full methodology"):
    try:
        st.markdown((Path(__file__).parent / "METHODOLOGY.md").read_text())
    except Exception:
        st.markdown(f"The full methodology is available here: [{METHODOLOGY_URL}]({METHODOLOGY_URL})")

# ---- Level selector ----
level_key = st.radio("School level", list(LEVELS.keys()), index=1, horizontal=True)
spec = LEVELS[level_key]

# ---- Sidebar: this level's framework reference ----
st.sidebar.header(f"{level_key} school — framework")
st.sidebar.caption("Indicator weights (2024-25 manual):")
for comp in spec.component_order:
    st.sidebar.write(f"- {comp}: **{spec.indicator_weights[comp]:g}** pts")
cuts = " · ".join(f"{s}★ ≥{l:g}" for s, l in spec.star_cuts if s > 1)
st.sidebar.caption("Star cut scores: " + cuts + " · 1★ below the 2★ cut")
st.sidebar.divider()
st.sidebar.caption("Out of scope (need student-level data): n-size pooling, "
                   "CSI/TSI/ATSI designations, participation penalties.")


def indicator(label, default, minv, maxv, step, help, key):
    """Number box + 'Reported' toggle. Returns the value, or None if unreported."""
    col_a, col_b = st.columns([3, 1])
    with col_a:
        val = st.number_input(label, min_value=float(minv), max_value=float(maxv),
                              value=float(default), step=float(step), help=help, key=key)
    with col_b:
        st.write("")
        reported = st.checkbox("Reported", value=True, key=f"rep_{key}")
    return val if reported else None


# ---- Inputs, grouped by indicator, mirroring the report ----
st.subheader(f"Enter the {level_key.lower()} school's reported rates")
st.caption("Uncheck 'Reported' for any measure suppressed by minimum-N rules (shown as '-' on a report).")

values = {}
state = {"prior_ca": None}


def render_measure(md):
    val = indicator(md.label, md.default, md.vmin, md.vmax, md.step,
                    md.help or None, key=f"{level_key}_{md.key}")
    values[md.key] = val
    if md.is_ca:
        on = st.checkbox("I have last year's Chronic Absenteeism rate (enables reduction / incentive)",
                         value=True, key=f"{level_key}_useprior")
        if on:
            state["prior_ca"] = st.number_input(
                "Prior-year Chronic Absenteeism %", min_value=0.0, max_value=100.0,
                value=float(spec.ca_default_prior), step=0.1, key=f"{level_key}_priorca")


def render_component(comp):
    st.markdown(f"### {comp}  ·  /{spec.indicator_weights[comp]:g}")
    for md in spec.measures:
        if md.component == comp:
            render_measure(md)


comps = spec.component_order
split = (len(comps) + 1) // 2
colL, colR = st.columns(2)
with colL:
    for c in comps[:split]:
        render_component(c)
with colR:
    for c in comps[split:]:
        render_component(c)

r = compute(level_key, values, state["prior_ca"])

# ---- Results ----
st.divider()
st.header("Projected result")

if not r.rated:
    st.warning(
        "**Not Rated** under NDE rules — this level requires all of: "
        f"{', '.join(r.missing_required)} (currently missing). The index below is provisional."
    )

m1, m2, m3 = st.columns(3)
m1.metric("Total Index Score", f"{r.index} / 100")
m2.metric("Star rating", "★" * r.stars + "☆" * (5 - r.stars))
if r.next_star is not None:
    m3.metric(f"Index points to {r.next_star}★", r.points_to_next)
else:
    m3.metric("Status", "Top band")

st.subheader("Indicator breakdown")
for comp in spec.component_order:
    if comp in r.by_component:
        c = r.by_component[comp]
        pct = (c["earned"] / c["possible"]) if c["possible"] else 0.0
        st.write(f"**{comp}** — {c['earned']:.1f} / {c['possible']:g}")
        st.progress(max(0.0, min(1.0, pct)))

with st.expander("Measure detail (matches report line items)"):
    for m in r.measures:
        if m.applies:
            note = f"  — _{m.note}_" if m.note and m.note != "rate" else ""
            st.write(f"{m.label}: rate {m.value} → **{m.earned:.1f}** / {m.max_points:g} pts{note}")
        else:
            st.write(f"{m.label}: _not reported_")

st.caption(
    "Index = points earned ÷ points possible × 100 (§1.2.2). Rates are truncated to the tenth "
    "before table lookup (§1.3). Chronic absenteeism takes the higher of the rate path "
    "(+ incentive) or the reduction-rate path when a prior-year rate is supplied."
)
