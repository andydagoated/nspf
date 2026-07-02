"""
Interim iReady -> Projected NSPF Estimate
==========================================
Lets a school leader upload a per-student iReady interim diagnostic export
(BOY/MOY) and see a PROJECTED NSPF index/star rating, using the same
unmodified nspf_engine.compute() as the official calculator.

This is a projection, not an official score:
  - It uses iReady's Probable SBAC Level and (if present) iReady's own
    growth percentile / target-met flags -- not the state's official SBAC
    results, official SGP growth model, or AGP determinations.
  - Any measure the upload can't support is left unreported. The engine's
    existing "required for rating" logic then correctly flags the school as
    Not Rated (provisional) rather than faking a complete score.

Data handling:
  - Nothing here is written to disk. The uploaded file is read directly
    into memory (pandas), aggregated into school-level rates, and the
    per-student DataFrame is discarded. Only the aggregate rates and the
    resulting score live in st.session_state for the rest of the browser
    session.
  - A "Clear uploaded data" button wipes session state immediately.
"""

from __future__ import annotations
import pandas as pd
import streamlit as st

from nspf_engine import LEVELS, compute
from iready_ingest import CANONICAL_FIELDS, guess_mapping, apply_mapping, project_rates

st.set_page_config(page_title="Interim iReady -> NSPF Projection", layout="wide")

st.title("Interim iReady \u2192 Projected NSPF Estimate")

st.warning(
    "**This is a projection, not an official NSPF score.** It's built from an interim "
    "iReady diagnostic (BOY/MOY), not official end-of-year SBAC results. Growth-based "
    "measures (MGP) use iReady's own growth percentile, which is not the state's official "
    "growth model. Use this for a mid-year directional check-in \u2014 not for public, board, "
    "or funder-facing reporting."
)

st.caption(
    "For the official calculator (type in numbers from a published NSPF rating report), "
    "use the main **NSPF Star-Rating Estimator** page in the sidebar."
)

st.divider()

# ---------------------------------------------------------------------
# 1. Upload
# ---------------------------------------------------------------------
st.subheader("1. Upload your iReady export")
st.caption(
    "One file with a Subject column (ELA/Math), or upload separately below. "
    "Nothing is saved \u2014 this file is processed in memory for this browser session only."
)

col_a, col_b = st.columns(2)
with col_a:
    combined_file = st.file_uploader("Combined file (has an ELA/Math Subject column)",
                                      type=["csv", "xlsx"], key="combined")
with col_b:
    st.caption("— or, if ELA and Math are separate exports —")
    ela_file = st.file_uploader("ELA export", type=["csv", "xlsx"], key="ela")
    math_file = st.file_uploader("Math export", type=["csv", "xlsx"], key="math")


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
st.caption("Confirm or correct the auto-detected mapping. Leave optional fields as 'None' if you don't have that data.")

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

# If subject was provided via separate ELA/Math uploads, use that instead of a mapped column
if "__subject_override" in raw_df.columns and mapping.get("subject") is None:
    raw_df["__subject_for_mapping"] = raw_df["__subject_override"]
    mapping["subject"] = "__subject_for_mapping"

missing_required = [k for k, m in CANONICAL_FIELDS.items() if m["required"] and mapping.get(k) is None]
if missing_required:
    st.error(f"Please map required field(s): {', '.join(missing_required)}")
    st.stop()

# ---------------------------------------------------------------------
# 3. Aggregate (student-level data discarded immediately after this)
# ---------------------------------------------------------------------
canonical_df = apply_mapping(raw_df, mapping)
projection = project_rates(canonical_df)
del canonical_df, raw_df  # done with per-student data for this run

st.divider()
st.subheader("3. Projected rates")
st.caption(
    f"{projection.n_students:,} unique students \u00b7 {projection.n_ela_rows:,} ELA rows \u00b7 "
    f"{projection.n_math_rows:,} Math rows"
)

CONF_BADGE = {"high": "\U0001F7E2 High confidence", "medium": "\U0001F7E1 Medium confidence",
              "low": "\U0001F534 Low confidence (not the state's official growth model)"}

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

level_key = st.radio("School level", list(LEVELS.keys()), index=1, horizontal=True, key="level_proj")

r = compute(level_key, values, prior_ca=None)

st.error(
    "PROJECTED / INTERIM \u2014 not an official NDE rating, not suitable for public reporting."
)

if not r.rated:
    st.warning(
        "**Not Rated (provisional)** \u2014 this projection is missing required measure(s): "
        f"{', '.join(r.missing_required)}. That's expected if your iReady export doesn't include "
        "growth percentiles or AGP target-met flags. The index below only reflects the measures "
        "that were available."
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
    "Student Engagement measures (chronic absenteeism, credit sufficiency, etc.) require "
    "attendance/enrollment data this tool doesn't take, so they're excluded here \u2014 the "
    "official calculator (main page) can include them if you have those rates."
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
