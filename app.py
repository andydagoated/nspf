"""
Streamlit UI for the NSPF Middle School estimator.
Implements the 2024-25 NSPF Manual (v8-15-2025). Inputs are labeled and grouped
to match the line items on an official NSPF school rating report, so values read
off a report map directly onto this tool.

Run locally:   streamlit run app.py
Deploy:        push to GitHub, then deploy on Streamlit Community Cloud (main file: app.py)
"""

import streamlit as st
from nspf_middle_school import (
    MiddleSchoolInputs, compute, INDICATOR_WEIGHTS, COMPONENT_ORDER, REQUIRED_FOR_RATING,
)

st.set_page_config(page_title="NSPF Middle School Estimator", layout="wide")

st.title("NSPF Middle School Star-Rating Estimator")
st.caption("Implements the 2024-25 NSPF Manual (v8-15-2025). Labels match the school rating report.")

st.info(
    "Enter the rates from a school rating report's front page. Each field below is named "
    "exactly as it appears on the report. **Use only aggregate, school-level numbers** — "
    "never individual student data. This is an estimate, not an official NDE rating."
)

# ---- Sidebar: framework reference ----
st.sidebar.header("Framework reference")
st.sidebar.caption("2024-25 indicator weights (Table 10):")
for comp in COMPONENT_ORDER:
    st.sidebar.write(f"- {comp}: **{INDICATOR_WEIGHTS[comp]}** pts")
st.sidebar.caption("Star cuts (Table 2): 5★ ≥80 · 4★ 70–79 · 3★ 50–69 · 2★ 29–49 · 1★ <29")
st.sidebar.divider()
st.sidebar.caption(
    "Out of scope (need student-level data): n-size pooling, CSI/TSI/ATSI designations, "
    "and assessment participation penalties."
)


def indicator(label, default, minv=0.0, maxv=100.0, step=1.0, help=None, key=None):
    """Number box + a 'Reported' toggle. Returns the value, or None if unreported."""
    col_a, col_b = st.columns([3, 1])
    with col_a:
        val = st.number_input(label, min_value=float(minv), max_value=float(maxv),
                              value=float(default), step=float(step), help=help, key=key)
    with col_b:
        st.write("")
        reported = st.checkbox("Reported", value=True, key=f"rep_{key or label}")
    return val if reported else None


st.subheader("Enter the school's reported rates")
st.caption("Uncheck 'Reported' for any measure suppressed by minimum-N rules (shown as '-' on a report).")

left, right = st.columns(2)

with left:
    st.markdown("### Academic Achievement  ·  /25")
    mode = st.radio("Pooled proficiency", ["Enter rate directly", "Compute from counts"],
                    horizontal=True, label_visibility="collapsed")
    if mode == "Compute from counts":
        st.caption("Pooled = (Math + ELA + Science proficient) ÷ (assessed) × 100")
        c1, c2 = st.columns(2)
        with c1:
            mp = st.number_input("Math proficient", min_value=0, value=0, step=1)
            ep = st.number_input("ELA proficient", min_value=0, value=0, step=1)
            sp = st.number_input("Science proficient", min_value=0, value=0, step=1)
        with c2:
            ma = st.number_input("Math assessed", min_value=0, value=0, step=1)
            ea = st.number_input("ELA assessed", min_value=0, value=0, step=1)
            sa = st.number_input("Science assessed", min_value=0, value=0, step=1)
        denom = ma + ea + sa
        pooled = round((mp + ep + sp) / denom * 100, 1) if denom else 0.0
        st.metric("Pooled Proficiency", f"{pooled}%")
        rep = st.checkbox("Reported", value=denom > 0, key="rep_pooled_counts")
        pooled_proficiency = pooled if rep else None
    else:
        pooled_proficiency = indicator("Pooled Proficiency", 26.2, step=0.1, key="pooled")

    st.markdown("### Student Growth  ·  /30")
    math_mgp = indicator("Math MGP (school median)", 56, minv=1, maxv=99, key="mmgp")
    ela_mgp = indicator("ELA MGP (school median)", 51, minv=1, maxv=99, key="emgp")
    math_agp = indicator("Met Math AGP Target %", 21, step=0.1, key="magp")
    ela_agp = indicator("Met ELA AGP Target %", 39.9, step=0.1, key="eagp")

    st.markdown("### English Language Proficiency  ·  /10")
    wida = indicator("Met EL AGP Target %", 37.5, step=0.1,
                    help="Uncheck Reported if too few ELs to report.", key="wida")

with right:
    st.markdown("### Closing Opportunity Gaps  ·  /20")
    math_gap = indicator("Prior Non-Proficient Met Math AGP Target %", 11.7, step=0.1, key="mgap")
    ela_gap = indicator("Prior Non-Proficient Met ELA AGP Target %", 26.6, step=0.1, key="egap")

    st.markdown("### Student Engagement  ·  /15")
    absent = indicator("Chronic Absenteeism %  (lower is better)", 28.5, step=0.1, key="ca")
    use_prior = st.checkbox("I have last year's Chronic Absenteeism rate "
                            "(enables the reduction / incentive paths)", value=True, key="useprior")
    prior_absent = None
    if use_prior:
        prior_absent = st.number_input("Prior-year Chronic Absenteeism %", min_value=0.0,
                                       max_value=100.0, value=42.5, step=0.1, key="prior_ca")
    alp = indicator("Academic Learning Plans %", 95, step=0.1,
                   help="Reports often show '>95' — enter 95 (anything ≥95 earns full points).", key="alp")
    credit8 = indicator("8th Grade Credit Requirements %", 81.8, step=0.1, key="cr8")

inp = MiddleSchoolInputs(
    pooled_proficiency=pooled_proficiency,
    math_mgp=math_mgp, ela_mgp=ela_mgp,
    math_agp_pct=math_agp, ela_agp_pct=ela_agp,
    wida_agp_pct=wida,
    math_gap_pct=math_gap, ela_gap_pct=ela_gap,
    chronic_absenteeism=absent, prior_chronic_absenteeism=prior_absent,
    alp_pct=alp, credit8_pct=credit8,
)

r = compute(inp)

# ---- Results (mirrors the report's front page) ----
st.divider()
st.header("Projected result")

if not r.rated:
    pretty = ", ".join(REQUIRED_FOR_RATING)
    st.warning(
        "**Not Rated** under NDE rules — a middle school must have all five rating-required "
        f"measures ({pretty}). The index below is provisional, based only on what was entered."
    )

m1, m2, m3 = st.columns(3)
m1.metric("Total Index Score", f"{r.index} / 100")
m2.metric("Star rating", "★" * r.stars + "☆" * (5 - r.stars))
if r.next_star is not None:
    m3.metric(f"Index points to {r.next_star}★", r.points_to_next)
else:
    m3.metric("Status", "Top band")

st.subheader("Indicator breakdown")
for comp in COMPONENT_ORDER:
    if comp in r.by_component:
        c = r.by_component[comp]
        pct = (c["earned"] / c["possible"]) if c["possible"] else 0.0
        st.write(f"**{comp}** — {c['earned']:.1f} / {c['possible']:.0f}")
        st.progress(max(0.0, min(1.0, pct)))

with st.expander("Measure detail (matches report line items)"):
    for m in r.measures:
        if m.applies:
            note = f"  — _{m.note}_" if m.note and m.note != "rate" else ""
            st.write(f"{m.label}: rate {m.value} → **{m.earned:.1f}** / {m.max_points:.0f} pts{note}")
        else:
            st.write(f"{m.label}: _not reported_")

st.caption(
    "Index = points earned ÷ points possible × 100 (manual §1.2.2). Rates are truncated to the "
    "tenth before table lookup (§1.3). Chronic absenteeism takes the higher of the rate path "
    "(+ incentive) or the reduction-rate path when a prior-year rate is supplied."
)
