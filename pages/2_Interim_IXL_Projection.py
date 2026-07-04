"""
Interim IXL -> Projected NSPF Estimate
=======================================
Lets a school leader upload a per-student IXL Real-Time Diagnostic export
and see a PROJECTED NSPF index/star rating, using the same unmodified
nspf_engine.compute() as the official calculator.

This is a projection built on EXPLICIT LINKING ASSUMPTIONS, not vendor
proficiency projections:
  - IXL has no "Probable SBAC Level" (unlike iReady) and no published
    IXL -> SBAC concordance for Nevada. Proficiency here means
    "diagnostic level at/above grade level (x100), plus an adjustable
    offset" -- a heuristic the school can calibrate, shown on-screen at
    all times.
  - IXL has no peer-normed growth percentile, so MGP is reported as NOT
    DERIVABLE rather than faked. The engine's existing "required for
    rating" logic then correctly flags the result as provisional.
  - Growth-target measures use a catch-up proxy (see ixl_ingest.py),
    which is an analog of the state's 3-year AGP concept -- not the
    state's actual AGP determination.

Data handling (same guarantees as the iReady page):
  - Nothing here is written to disk. The uploaded file is read directly
    into memory (pandas), aggregated into school-level rates, and the
    per-student DataFrame is discarded. Only the aggregate rates and the
    resulting score live in st.session_state for the browser session.
  - A "Clear uploaded data" button wipes session state immediately.
"""

from __future__ import annotations
from datetime import datetime
import pandas as pd
import streamlit as st
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from nspf_engine import LEVELS, compute
from ixl_ingest import (
    CANONICAL_FIELDS, LinkingSettings, guess_mapping, apply_mapping, project_rates,
)


def _pdf_safe(text: str) -> str:
    """Make text safe for fpdf2's built-in Latin-1 fonts.

    Replaces the Unicode punctuation used elsewhere in the app (em dashes,
    arrows, math symbols) with ASCII equivalents, then hard-fails nothing:
    any remaining unsupported character becomes '?' instead of crashing
    PDF generation.
    """
    replacements = {
        "\u2014": "-", "\u2013": "-",      # em/en dash
        "\u2192": "->", "\u2190": "<-",    # arrows
        "\u2265": ">=", "\u2264": "<=",
        "\u00d7": "x", "\u2248": "~=",
        "\u2605": "*", "\u2606": "-",      # filled/empty stars
        "\u00b7": "|", "\u2022": "-",      # middle dot, bullet
        "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "replace").decode("latin-1")


def _line(pdf, text, h=5):
    """multi_cell that always resets the cursor to the left margin afterward."""
    pdf.multi_cell(0, h, _pdf_safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def build_pdf(level_key: str, r, projection, values: dict, engagement_measures: list,
              settings: LinkingSettings) -> bytes:
    """Build a one-page PDF summary of the projected result.

    Contains only aggregate, school-level numbers -- no student names, IDs,
    or row-level data -- so it's safe to hand off, print, or paste into
    another tool (including an AI assistant) for further analysis.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    _line(pdf, "Interim IXL -> Projected NSPF Estimate", h=8)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(180, 60, 0)
    _line(
        pdf,
        "PROJECTED / INTERIM -- NOT AN OFFICIAL NDE RATING. Built from an IXL diagnostic "
        "snapshot using explicit linking assumptions (below), not official SBAC results, "
        "the state's growth model, or official AGP determinations. MGP cannot be derived "
        "from IXL and is excluded. Not suitable for public, board, or funder-facing "
        "reporting.",
        h=6,
    )
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 11)
    _line(pdf, "Linking assumptions used in this projection", h=6)
    pdf.set_font("Helvetica", "", 10)
    _line(pdf, f"- Proficiency proxy: IXL level >= grade x 100 {settings.proficiency_offset:+g} points")
    _line(pdf, f"- Expected gain: {settings.annual_gain:g} points per year, prorated to "
               f"{settings.months_elapsed:g} months elapsed")
    _line(pdf, f"- Catch-up target for below-level students: close BOY deficit within "
               f"{settings.catch_up_years:g} years")
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
        '1. "Given the linking assumptions and confidence levels noted, which 1-2 measures are '
        'most likely driving this result, and which should I treat cautiously?"',
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
        '3. "This projection maps IXL levels to proficiency with a heuristic. How could I '
        'calibrate that offset against my school\'s own historical IXL-vs-SBAC results?"',
        h=4,
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 10)
    _line(pdf, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    _line(pdf, f"School level: {level_key}")
    _line(
        pdf,
        f"Students: {projection.n_students}  |  ELA rows: {projection.n_ela_rows}  |  "
        f"Math rows: {projection.n_math_rows}",
    )
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
        _line(pdf, "Student Engagement (entered manually, not derived from IXL)", h=5)
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


st.set_page_config(page_title="Interim IXL -> NSPF Projection", layout="wide")

st.title("Interim IXL \u2192 Projected NSPF Estimate")

st.warning(
    "**This is a projection, not an official NSPF score.** It's built from an IXL "
    "Real-Time Diagnostic snapshot using explicit linking assumptions you control below. "
    "Unlike iReady, IXL provides no vendor SBAC projection and no peer-normed growth "
    "percentile \u2014 so proficiency here is a grade-level heuristic, growth targets are a "
    "catch-up proxy, and MGP is honestly reported as not derivable. Use this for a "
    "mid-year directional check-in \u2014 not for public, board, or funder-facing reporting."
)

st.caption(
    "For the official calculator (type in numbers from a published NSPF rating report), "
    "use the main **NSPF Star-Rating Estimator** page. If your school uses iReady, the "
    "**Interim iReady Projection** page uses the vendor's own SBAC projections and is "
    "higher-confidence."
)

st.divider()

# ---------------------------------------------------------------------
# 1. Upload
# ---------------------------------------------------------------------
st.subheader("1. Upload your IXL export")
st.caption(
    "One file, one row per student, with Math and/or ELA diagnostic level columns "
    "(IXL's diagnostic exports are typically shaped this way). Nothing is saved \u2014 "
    "this file is processed in memory for this browser session only."
)

uploaded = st.file_uploader("IXL diagnostic export", type=["csv", "xlsx"], key="ixl_file")

if uploaded is None:
    st.info("Upload a file above to continue.")
    st.stop()

raw_df = pd.read_csv(uploaded) if uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)

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
    "don't have that data. Mapping prior-year SBAC levels upgrades the gap-closing measure "
    "from a proxy population to the real one."
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
        chosen = st.selectbox(label, columns, index=default_idx, key=f"ixl_map_{field_key}")
        mapping[field_key] = None if chosen == "None" else chosen

missing_required = [k for k, m in CANONICAL_FIELDS.items() if m["required"] and mapping.get(k) is None]
if missing_required:
    st.error(f"Please map required field(s): {', '.join(missing_required)}")
    st.stop()

if mapping.get("math_level") is None and mapping.get("ela_level") is None:
    st.error("Map at least one of: Current Math level, Current ELA level.")
    st.stop()

# ---------------------------------------------------------------------
# 3. Linking assumptions (the honest part)
# ---------------------------------------------------------------------
st.divider()
st.subheader("3. Linking assumptions")
st.caption(
    "IXL's scale runs ~100 points per grade level (700 \u2248 start of 7th grade). These "
    "controls make the IXL\u2192NSPF link explicit and adjustable \u2014 there is no published "
    "IXL\u2192SBAC concordance, so calibrate the offset against your own historical "
    "IXL-vs-SBAC results if you have them."
)

s1, s2, s3 = st.columns(3)
with s1:
    offset = st.slider(
        "Proficiency threshold offset (points vs grade\u00d7100)",
        min_value=-100, max_value=100, value=0, step=5,
        help="0 = 'at grade level counts as projected proficient'. Raise it if your school's "
             "history shows students need to be above grade level on IXL to reach SBAC L3.",
        key="ixl_offset",
    )
with s2:
    months = st.slider(
        "Months since BOY snapshot", min_value=1.0, max_value=9.0, value=4.0, step=0.5,
        help="Used to prorate the annual growth target for the growth-proxy measures.",
        key="ixl_months",
    )
with s3:
    annual_gain = st.slider(
        "Expected annual gain (IXL points)", min_value=50, max_value=150, value=100, step=5,
        help="100 \u2248 one grade level per year on IXL's scale.",
        key="ixl_gain",
    )

settings = LinkingSettings(
    proficiency_offset=float(offset),
    annual_gain=float(annual_gain),
    months_elapsed=float(months),
)

# ---------------------------------------------------------------------
# 4. Aggregate (student-level data discarded immediately after this)
# ---------------------------------------------------------------------
canonical_df = apply_mapping(raw_df, mapping)
projection = project_rates(canonical_df, settings)
del canonical_df, raw_df  # done with per-student data for this run

st.divider()
st.subheader("4. Projected rates")
st.caption(
    f"{projection.n_students:,} unique students \u00b7 {projection.n_ela_rows:,} ELA rows \u00b7 "
    f"{projection.n_math_rows:,} Math rows"
)

CONF_BADGE = {"high": "\U0001F7E2 High confidence",
              "medium": "\U0001F7E1 Medium confidence (linking assumption, not vendor projection)",
              "low": "\U0001F534 Low confidence (proxy measure or not derivable from IXL)"}

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
            reported = st.checkbox("Include in projection", value=(d.n >= 1), key=f"ixl_rep_{d.key}")
    with c3:
        if d.value is not None:
            st.metric("Rate", f"{d.value:g}%", help=d.note)
        else:
            st.caption(d.note)
    values[d.key] = d.value if (d.value is not None and reported) else None

# ---------------------------------------------------------------------
# 5. Run the SAME unmodified NSPF engine
# ---------------------------------------------------------------------
st.divider()
st.subheader("5. Projected NSPF result")

level_key = st.radio("School level", list(LEVELS.keys()), index=1, horizontal=True, key="ixl_level_proj")
spec = LEVELS[level_key]

st.markdown("**Student Engagement \u2014 enter these directly (not derived from IXL)**")
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
            key=f"ixl_eng_{level_key}_{md.key}",
        )
    with e2:
        st.write("")
        reported = st.checkbox("Reported", value=False, key=f"ixl_eng_rep_{level_key}_{md.key}")
    values[md.key] = val if reported else None

    if md.is_ca and reported:
        use_prior = st.checkbox(
            "I have last year's Chronic Absenteeism rate (enables reduction/incentive)",
            value=False, key=f"ixl_eng_useprior_{level_key}",
        )
        if use_prior:
            prior_ca_value = st.number_input(
                "Prior-year Chronic Absenteeism %", min_value=0.0, max_value=100.0,
                value=float(spec.ca_default_prior), step=0.1, key=f"ixl_eng_priorca_{level_key}",
            )

r = compute(level_key, values, prior_ca=prior_ca_value)

st.error(
    "PROJECTED / INTERIM \u2014 not an official NDE rating, not suitable for public reporting. "
    "MGP is not derivable from IXL, so this projection is structurally partial."
)

if not r.rated:
    st.warning(
        "**Not Rated (provisional)** \u2014 this projection is missing required measure(s): "
        f"{', '.join(r.missing_required)}. That's expected for IXL data: MGP can't be derived, "
        "and growth proxies require a BOY-level column. The index below only reflects the "
        "measures that were available."
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
    "Student Engagement measures above were entered manually, not derived from IXL \u2014 "
    "double-check they're accurate before trusting the result."
)

st.divider()
st.subheader("6. Export")
pdf_bytes = build_pdf(level_key, r, projection, values, engagement_measures, settings)
st.download_button(
    "\U0001F4C4 Download results as PDF",
    data=pdf_bytes,
    file_name=f"interim_ixl_nspf_projection_{level_key.lower()}.pdf",
    mime="application/pdf",
)
st.caption(
    "This PDF contains only aggregate, school-level numbers \u2014 no student names, IDs, or "
    "row-level data \u2014 and records the linking assumptions used, so the PROJECTED/INTERIM "
    "disclaimer and the methodology travel with the document."
)

st.divider()
if st.button("Clear uploaded data now", key="ixl_clear"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.caption(
    "Nothing from this page is written to a database or disk. Uploaded data exists only in this "
    "browser session's memory and is cleared when you close the tab, refresh, or click Clear above."
)
