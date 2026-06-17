"""
Streamlit UI for the NSPF Middle School star-rating estimator.

Run locally:   streamlit run app.py
Deploy:        push this repo to GitHub, then deploy on Streamlit Community Cloud.

All scoring numbers are editable in the sidebar and default to PLACEHOLDERS.
Replace them with official NDE NSPF technical-guide values for your target year.
"""

import streamlit as st
from nspf_middle_school import compute, MiddleSchoolInputs, NSPFConfig

st.set_page_config(page_title="NSPF Middle School Estimator", layout="wide")

st.title("NSPF Middle School Star-Rating Estimator")
st.caption("Nevada School Performance Framework — deterministic scoring engine")

st.warning(
    "**These numbers are placeholders.** Every weight, scoring rule, and star "
    "cut score is illustrative. Replace them with the official NDE NSPF technical "
    "guide values for your target year (sidebar) before relying on any result.\n\n"
    "**Enter only aggregate, school-level numbers** — never individual student data."
)

# Defaults pulled from the engine's placeholder config.
D = NSPFConfig()

# ----------------------------------------------------------------------
# Sidebar: editable scoring configuration
# ----------------------------------------------------------------------
st.sidebar.header("Scoring configuration")
st.sidebar.caption("Replace with official NDE values for your year.")

st.sidebar.subheader("Component max points")
w = {}
w["ela_prof"]  = st.sidebar.number_input("ELA proficiency",     value=D.pts_ela_proficiency,     step=0.5)
w["math_prof"] = st.sidebar.number_input("Math proficiency",    value=D.pts_math_proficiency,    step=0.5)
w["sci_prof"]  = st.sidebar.number_input("Science proficiency", value=D.pts_science_proficiency, step=0.5)
w["ela_mgp"]   = st.sidebar.number_input("ELA MGP",             value=D.pts_ela_mgp,             step=0.5)
w["math_mgp"]  = st.sidebar.number_input("Math MGP",            value=D.pts_math_mgp,            step=0.5)
w["ela_agp"]   = st.sidebar.number_input("ELA adequate growth", value=D.pts_ela_agp,            step=0.5)
w["math_agp"]  = st.sidebar.number_input("Math adequate growth",value=D.pts_math_agp,           step=0.5)
w["el"]        = st.sidebar.number_input("EL progress",         value=D.pts_el_progress,         step=0.5)
w["gap"]       = st.sidebar.number_input("Closing opportunity gaps", value=D.pts_opportunity_gap, step=0.5)
w["absent"]    = st.sidebar.number_input("Chronic absenteeism", value=D.pts_chronic_absenteeism, step=0.5)
w["climate"]   = st.sidebar.number_input("Climate survey",      value=D.pts_climate_survey,      step=0.5)

total_pts = sum(w.values())
st.sidebar.caption(f"Total points configured: **{total_pts:.1f}**")

st.sidebar.subheader("Star cut scores (index lower bound)")
cut5 = st.sidebar.number_input("5 stars  (index ≥)", value=82.0, step=1.0)
cut4 = st.sidebar.number_input("4 stars  (index ≥)", value=65.0, step=1.0)
cut3 = st.sidebar.number_input("3 stars  (index ≥)", value=50.0, step=1.0)
cut2 = st.sidebar.number_input("2 stars  (index ≥)", value=27.0, step=1.0)

cfg = NSPFConfig(
    pts_ela_proficiency=w["ela_prof"],
    pts_math_proficiency=w["math_prof"],
    pts_science_proficiency=w["sci_prof"],
    pts_ela_mgp=w["ela_mgp"],
    pts_math_mgp=w["math_mgp"],
    pts_ela_agp=w["ela_agp"],
    pts_math_agp=w["math_agp"],
    pts_el_progress=w["el"],
    pts_opportunity_gap=w["gap"],
    pts_chronic_absenteeism=w["absent"],
    pts_climate_survey=w["climate"],
    star_cuts=[(5, cut5), (4, cut4), (3, cut3), (2, cut2), (1, 0.0)],
)

# ----------------------------------------------------------------------
# Helper: indicator input with a "reported" toggle (for min-N suppression)
# ----------------------------------------------------------------------
def indicator(label, default, minv=0.0, maxv=100.0, step=1.0, help=None):
    col_a, col_b = st.columns([3, 1])
    with col_a:
        val = st.number_input(label, min_value=float(minv), max_value=float(maxv),
                              value=float(default), step=float(step), help=help)
    with col_b:
        st.write("")  # vertical nudge
        reported = st.checkbox("Reported", value=True, key=f"rep_{label}")
    return val if reported else None

# ----------------------------------------------------------------------
# Main: indicator inputs (seeded with an example school)
# ----------------------------------------------------------------------
st.subheader("Enter this school's indicator values")
st.caption("Uncheck 'Reported' for any indicator suppressed by minimum-N rules.")

left, right = st.columns(2)

with left:
    st.markdown("**Academic Achievement** (% proficient)")
    ela_prof  = indicator("ELA proficiency", 48)
    math_prof = indicator("Math proficiency", 35)
    sci_prof  = indicator("Science proficiency", 40)

    st.markdown("**Student Growth**")
    ela_mgp  = indicator("ELA median growth percentile", 52, minv=1, maxv=99)
    math_mgp = indicator("Math median growth percentile", 47, minv=1, maxv=99)
    ela_agp  = indicator("ELA % meeting adequate growth", 44)
    math_agp = indicator("Math % meeting adequate growth", 38)

with right:
    st.markdown("**English Learner Progress**")
    el = indicator("% making progress to proficiency", 55,
                  help="Uncheck Reported if too few ELs to report.")

    st.markdown("**Closing Opportunity Gaps**")
    gap = indicator("Opportunity-gap measure", 46,
                   help="Confirm the official definition for your year.")

    st.markdown("**Student Engagement**")
    absent  = indicator("Chronic absenteeism % (lower is better)", 18)
    climate = indicator("Climate survey score", 70)

inp = MiddleSchoolInputs(
    ela_proficiency=ela_prof,
    math_proficiency=math_prof,
    science_proficiency=sci_prof,
    ela_mgp=ela_mgp,
    math_mgp=math_mgp,
    ela_agp_pct=ela_agp,
    math_agp_pct=math_agp,
    el_progress=el,
    opportunity_gap_index=gap,
    chronic_absenteeism=absent,
    climate_survey=climate,
)

r = compute(inp, cfg)

# ----------------------------------------------------------------------
# Results
# ----------------------------------------------------------------------
st.divider()
st.header("Projected result")

m1, m2, m3 = st.columns(3)
m1.metric("Index", f"{r.index} / 100")
m2.metric("Star rating", "★" * r.stars + "☆" * (5 - r.stars))
if r.next_star is not None:
    m3.metric(f"Index points to {r.next_star}★", r.points_to_next_star)
else:
    m3.metric("Status", "Top band")

st.subheader("Component breakdown")
for name, c in r.by_component.items():
    pct = (c["earned"] / c["possible"]) if c["possible"] else 0.0
    st.write(f"**{name}** — {c['earned']:.1f} / {c['possible']:.1f}  ({pct * 100:.0f}%)")
    st.progress(max(0.0, min(1.0, pct)))

with st.expander("Indicator detail"):
    for i in r.by_indicator:
        if i.applies:
            st.write(f"{i.name}: {i.earned:.2f} / {i.max_points:.1f}")
        else:
            st.write(f"{i.name}: _not reported_")

st.caption(
    "Index = points earned ÷ points possible × 100, so unreported indicators drop "
    "out of both. Confirm this matches the official min-N / reweighting rules."
)
