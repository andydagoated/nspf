"""
Interim MAP Growth -> Projected NSPF Estimate
==============================================
Lets a school leader upload a per-student NWEA MAP Growth export (CDF or
Combined Report, BOY/MOY) and see a PROJECTED NSPF index/star rating, using
the same unmodified nspf_engine.compute() as the official calculator.

This is a projection, not an official score:
  - Proficiency uses NWEA's linking-study Projected Proficiency (or, as a
    clearly-flagged fallback, a user-set achievement-percentile cut) -- not
    official end-of-year SBAC results.
  - Growth measures use MAP's Conditional Growth Percentile and Met
    Projected Growth -- not the state's official SGP model or AGP targets.
  - Any measure the upload can't support is left unreported. The engine's
    "required for rating" logic then correctly flags the school as Not
    Rated (provisional) rather than faking a complete score.

Data handling:
  - Nothing here is written to disk. The uploaded file is read directly
    into memory (pandas), aggregated into school-level rates, and the
    per-student DataFrame is discarded. Only aggregate rates and the
    resulting score live in st.session_state for this browser session.
  - A "Clear uploaded data" button wipes session state immediately.
"""

from __future__ import annotations
from datetime import datetime
import pandas as pd
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from nspf_engine import LEVELS, compute
from map_ingest import CANONICAL_FIELDS, guess_mapping, apply_mapping, project_rates


def _pdf_safe(text: str) -> str:
    """Make text safe for fpdf2's built-in Latin-1 fonts."""
    replacements = {
        "\u2014": "-", "\u2013": "-",
        "\u2192": "->", "\u2190": "<-",
        "\u2265": ">=", "\u2264": "<=",
        "\u00d7": "x", "\u2248": "~=",
        "\u2605": "*", "\u2606": "-",
        "\u00b7": "|", "\u2022": "-",
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


def _line(pdf, text, h=5):
    pdf.multi_cell(0, h, _pdf_safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def build_pdf(level_key: str, r, projection, values: dict, engagement_measures: list) -> bytes:
    """One-page PDF summary. Aggregate school-level numbers only -- no
    student names, IDs, or row-level data."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    _line(pdf, "Interim MAP Growth -> Projected NSPF Estimate", h=8)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(180, 60, 0)
    _line(
        pdf,
        "PROJECTED / INTERIM -- NOT AN OFFICIAL NDE RATING. Based on an interim MAP Growth "
        "assessment, not official end-of-year SBAC results. Proficiency uses NWEA's "
        "linking-study projection (or a percentile-cut estimate where flagged); growth "
        "measures use MAP's Conditional Growth Percentile and Met Projected Growth, not "
        "the state's official growth model or AGP targets. Not suitable for public, "
        "board, or funder-facing reporting.",
        h=6,
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    _line(pdf, "Getting the most from these numbers", h=6)
    pdf.set_font("Helvetica", "I", 9)
    _line(
        pdf,
        "If you're pasting this into an AI assistant for analysis, these prompts are built to "
        "respect the confidence tags above and avoid over-trusting a projection:",
        h=4,
    )
    pdf.set_font("Helvetica", "", 9)
    _line(
        pdf,
        '1. "Given the confidence levels noted (high/medium/low), which 1-2 measures are most '
        'likely driving this result, and which should I treat cautiously since they\'re '
        'projections?"',
        h=4,
    )
    _line(
        pdf,
        '2. "Where\'s the biggest gap between subjects or grades in these numbers that\'s worth '
        'investigating with my team this week?"',
        h=4,
    )
    _line(
        pdf,
        '3. "This is a mid-year projection from MAP, not an official score. What would need to '
        'be true about my school\'s real (non-MAP) data for this projection to be misleading?"',
        h=4,
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    _line(pdf, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    _line(pdf, f"School level: {level_key}")
    term_bit = f"  |  Term: {projection.term_used}" if projection.term_used else ""
    _line(
        pdf,
        f"Students: {projection.n_students}  |  ELA rows: {projection.n_ela_rows}  |  "
        f"Math rows: {projection.n_math_rows}{term_bit}",
    )
    if projection.n_dropped_other:
        _line(
            pdf,
            f"Rows excluded (Language Usage / Science / other non-ELA/Math courses): "
            f"{projection.n_dropped_other}",
        )
    if projection.term_note:
        _line(pdf, projection.term_note)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 13)
    _line(pdf, f"Projected Index: {r.index} / 100    Stars: {'*' * r.stars}{'-' * (5 - r.stars)}", h=7)
    if r.next_star is not None:
        pdf.set_font("Helvetica", "", 10)
        _line(pdf, f"Points to {r.next_star}-star band: {r.points_to_next}")
    if not r.rated:
        pdf.set_font("Helvetica", "I", 10)
        _line(pdf, f"Not Rated (provisional) -- missing required measure(s): {', '.join(r.missing_required)}.")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    _line(pdf, "Measures included in this projection", h=6)
    pdf.set_font("Helvetica", "", 10)
    for d in projection.detail:
        val_str = f"{d.value:g}%" if d.value is not None else "not available"
        included = "included" if values.get(d.key) is not None else "excluded"
        _line(pdf, f"- {d.label}: {val_str}  [{d.confidence} confidence, {included}]  ({d.note})")

    if engagement_measures:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        _line(pdf, "Student Engagement (entered manually, not derived from MAP)", h=5)
        pdf.set_font("Helvetica", "", 10)
        for md in engagement_measures:
            v = values.get(md.key)
            status = f"{v:g}%  [included]" if v is not None else "not reported  [excluded]"
            _line(pdf, f"- {md.label}: {status}")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 12)
    _line(pdf, "Indicator breakdown (measures included only)", h=6)
    pdf.set_font("Helvetica", "", 10)
    for comp, c in r.by_component.items():
        _line(pdf, f"- {comp}: {c['earned']:.1f} / {c['possible']:g}")

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 9)
    _line(
        pdf,
        "This document contains only aggregate, school-level statistics -- no individual "
        "student data. Safe to share, print, or paste into other tools for further analysis.",
    )
    return bytes(pdf.output())


st.set_page_config(page_title="Interim MAP Growth -> NSPF Projection", layout="wide")

st.title("Interim MAP Growth \u2192 Projected NSPF Estimate")

st.warning(
    "**This is a projection, not an official NSPF score.** It's built from an interim MAP "
    "Growth assessment (BOY/MOY), not official end-of-year SBAC results. Proficiency comes "
    "from NWEA's linking-study *Projected Proficiency* where available; growth-based measures "
    "use MAP's *Conditional Growth Percentile* and *Met Projected Growth*, which are not the "
    "state's official growth model or AGP targets. Use this for a mid-year directional "
    "check-in \u2014 not for public, board, or funder-facing reporting."
)

st.caption(
    "For the official calculator (type in numbers from a published NSPF rating report), "
    "use the main **NSPF Star-Rating Estimator** page in the sidebar."
)

st.divider()

# ---------------------------------------------------------------------
# 1. Upload
# ---------------------------------------------------------------------
st.subheader("1. Upload your MAP Growth export")
st.caption(
    "A Comprehensive Data File (CDF) or Combined Report works best \u2014 one file with a "
    "Course column, or upload Reading and Math separately below. Nothing is saved \u2014 "
    "this file is processed in memory for this browser session only."
)

col_a, col_b = st.columns(2)
with col_a:
    combined_file = st.file_uploader("Combined export (has a Course/Subject column)",
                                     type=["csv", "xlsx"], key="map_combined")
with col_b:
    st.caption("— or, if Reading and Math are separate exports —")
    ela_file = st.file_uploader("Reading export", type=["csv", "xlsx"], key="map_ela")
    math_file = st.file_uploader("Math export", type=["csv", "xlsx"], key="map_math")


def _read_any(f):
    if f.name.lower().endswith(".csv"):
        return pd.read_csv(f)
    return pd.read_excel(f)


raw_df = None
if combined_file is not None:
    raw_df = _read_any(combined_file)
elif ela_file is not None or math_file is not None:
    frames = []
    if ela_file is not None:
        d = _read_any(ela_file)
        d["__subject_override"] = "ELA"
        frames.append(d)
    if math_file is not None:
        d = _read_any(math_file)
        d["__subject_override"] = "MATH"
        frames.append(d)
    raw_df = pd.concat(frames, ignore_index=True) if frames else None

if raw_df is None:
    st.info("Upload a file above to continue.")
    st.stop()

st.success(f"Loaded {len(raw_df):,} rows. Nothing has been saved to disk.")
with st.expander("Preview first 5 rows (shown only in your browser, not stored)"):
    st.dataframe(raw_df.head(5), use_container_width=True)

# ---------------------------------------------------------------------
# 2. Column mapping
# ---------------------------------------------------------------------
st.divider()
st.subheader("2. Map your columns")
st.caption(
    "Confirm or correct the auto-detected mapping. Leave optional fields as 'None' if you "
    "don't have that data. Tip: 'Prior-year State Achievement Level' usually comes from a "
    "column your data team merged in \u2014 MAP exports don't include state results natively."
)

columns = ["None"] + list(raw_df.columns)
auto_mapping = guess_mapping(list(raw_df.columns))

mapping = {}
map_cols = st.columns(2)
for i, (field_key, meta) in enumerate(CANONICAL_FIELDS.items()):
    with map_cols[i % 2]:
        guess = auto_mapping.get(field_key)
        default_idx = columns.index(guess) if guess in columns else 0
        label = meta["label"] + (" *required*" if meta["required"] else " (optional)")
        chosen = st.selectbox(label, columns, index=default_idx, key=f"map_{field_key}")
        mapping[field_key] = None if chosen == "None" else chosen

if "__subject_override" in raw_df.columns and mapping.get("subject") is None:
    raw_df["__subject_for_mapping"] = raw_df["__subject_override"]
    mapping["subject"] = "__subject_for_mapping"

missing_required = [k for k, m in CANONICAL_FIELDS.items() if m["required"] and mapping.get(k) is None]
if missing_required:
    st.error(f"Please map required field(s): {', '.join(missing_required)}")
    st.stop()

# ---------------------------------------------------------------------
# 2b. Proficiency fallback (only when no linking-study column is mapped)
# ---------------------------------------------------------------------
percentile_cut = None
if mapping.get("projected_prof") is None and mapping.get("percentile") is not None:
    st.info(
        "No **Projected Proficiency** column mapped. You can estimate proficiency from the "
        "achievement percentile instead \u2014 this is a rough, LOW-confidence stand-in for "
        "the linking study, and the projection will say so everywhere it appears."
    )
    use_cut = st.checkbox("Estimate proficiency from a percentile cut", value=False, key="map_use_cut")
    if use_cut:
        percentile_cut = st.number_input(
            "Achievement percentile at/above which a student counts as projected-proficient",
            min_value=1.0, max_value=99.0, value=60.0, step=1.0, key="map_cut",
            help="There is no official cut. Ask your assessment coordinator what percentile "
                 "has historically corresponded to SBAC Level 3 for your grades.",
        )

# ---------------------------------------------------------------------
# 3. Aggregate (student-level data discarded immediately after this)
# ---------------------------------------------------------------------
canonical_df = apply_mapping(raw_df, mapping)
projection = project_rates(canonical_df, percentile_cut=percentile_cut)
del canonical_df, raw_df  # done with per-student data for this run

st.divider()
st.subheader("3. Projected rates")
term_bit = f" \u00b7 term: {projection.term_used}" if projection.term_used else ""
st.caption(
    f"{projection.n_students:,} unique students \u00b7 {projection.n_ela_rows:,} ELA rows \u00b7 "
    f"{projection.n_math_rows:,} Math rows{term_bit}"
)
if projection.term_note:
    st.info(projection.term_note)
if projection.n_dropped_other:
    st.caption(
        f"{projection.n_dropped_other:,} rows in other courses (Language Usage, Science, ...) "
        "were excluded \u2014 NSPF's ELA measures are anchored to the Reading assessment."
    )

CONF_BADGE = {"high": "\U0001F7E2 High confidence", "medium": "\U0001F7E1 Medium confidence",
              "low": "\U0001F534 Low confidence (not the state's official model)"}

values = {}
for d in projection.detail:
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        st.write(f"**{d.label}**")
        st.caption(CONF_BADGE[d.confidence])
    with c2:
        if d.value is None:
            st.write("_Not available from this upload_")
            reported = False
        else:
            reported = st.checkbox("Include in projection", value=(d.n >= 1), key=f"rep_{d.key}")
    with c3:
        if d.value is not None:
            st.metric("Rate", f"{d.value:g}%", help=d.note)
    values[d.key] = d.value if (d.value is not None and reported) else None

# ---------------------------------------------------------------------
# 4. Run the SAME unmodified NSPF engine
# ---------------------------------------------------------------------
st.divider()
st.subheader("4. Projected NSPF result")

level_key = st.radio("School level", list(LEVELS.keys()), index=1, horizontal=True, key="level_proj_map")
spec = LEVELS[level_key]

st.markdown("**Student Engagement \u2014 enter these directly (not derived from MAP)**")
st.caption(
    "These measures need attendance/enrollment data this tool doesn't take. Pull them from "
    "your SIS if you have them, or leave 'Reported' unchecked to exclude a measure."
)

engagement_measures = [m for m in spec.measures if m.component == "Student Engagement"]
prior_ca_value = None

for md in engagement_measures:
    e1, e2 = st.columns([3, 1])
    with e1:
        val = st.number_input(
            md.label, min_value=float(md.vmin), max_value=float(md.vmax),
            value=float(md.default), step=float(md.step), help=md.help or None,
            key=f"eng_map_{level_key}_{md.key}",
        )
    with e2:
        st.write("")
        reported = st.checkbox("Reported", value=False, key=f"eng_rep_map_{level_key}_{md.key}")
    values[md.key] = val if reported else None

    if md.is_ca and reported:
        use_prior = st.checkbox(
            "I have last year's Chronic Absenteeism rate (enables reduction/incentive)",
            value=False, key=f"eng_useprior_map_{level_key}",
        )
        if use_prior:
            prior_ca_value = st.number_input(
                "Prior-year Chronic Absenteeism %", min_value=0.0, max_value=100.0,
                value=float(spec.ca_default_prior), step=0.1, key=f"eng_priorca_map_{level_key}",
            )

r = compute(level_key, values, prior_ca=prior_ca_value)

st.error(
    "PROJECTED / INTERIM \u2014 not an official NDE rating, not suitable for public reporting."
)

if not r.rated:
    st.warning(
        "**Not Rated (provisional)** \u2014 this projection is missing required measure(s): "
        f"{', '.join(r.missing_required)}. That's expected if your MAP export doesn't include "
        "growth columns or a Projected Proficiency linking study. The index below only reflects "
        "the measures that were available."
    )

m1, m2, m3 = st.columns(3)
m1.metric("Projected Index", f"{r.index} / 100")
m2.metric("Projected stars", "\u2605" * r.stars + "\u2606" * (5 - r.stars))
if r.next_star is not None:
    m3.metric(f"Index points to {r.next_star}\u2605", r.points_to_next)
else:
    m3.metric("Status", "Top band")

st.subheader("Indicator breakdown (measures included in this projection only)")
for comp, c in r.by_component.items():
    pct = (c["earned"] / c["possible"]) if c["possible"] else 0.0
    st.write(f"**{comp}** \u2014 {c['earned']:.1f} / {c['possible']:g}")
    st.progress(max(0.0, min(1.0, pct)))

st.caption(
    "Student Engagement measures above were entered manually, not derived from MAP \u2014 "
    "double-check they're accurate before trusting the result."
)

st.divider()
st.subheader("5. Export")
pdf_bytes = build_pdf(level_key, r, projection, values, engagement_measures)
st.download_button(
    "\U0001F4C4 Download results as PDF",
    data=pdf_bytes,
    file_name=f"interim_map_nspf_projection_{level_key.lower()}.pdf",
    mime="application/pdf",
)
st.caption(
    "This PDF contains only aggregate, school-level numbers \u2014 no student names, IDs, or "
    "row-level data \u2014 so it's safe to share, print, or paste into another tool (including "
    "an AI assistant) for further analysis. The PROJECTED/INTERIM disclaimer travels with the "
    "document."
)

st.divider()
if st.button("Clear uploaded data now"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.caption(
    "Nothing from this page is written to a database or disk. Uploaded data exists only in this "
    "browser session's memory and is cleared when you close the tab, refresh, or click Clear above."
)
