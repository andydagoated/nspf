"""
iReady Interim Diagnostic -> NSPF Projected Rates
==================================================
Turns a per-student iReady interim diagnostic export (BOY/MOY) into the
aggregate rates nspf_engine.compute() expects.

THIS PRODUCES A PROJECTION, NOT AN OFFICIAL NSPF MEASURE.

Confidence by measure:
  - pooled_proficiency  HIGH    direct count of Probable SBAC Level 3-4 vs 1-2
  - math_agp / ela_agp  MEDIUM  depends on the file having a target-met flag
  - math_gap / ela_gap  MEDIUM  depends on target-met flag AND a matched
                                prior-year achievement level
  - math_mgp / ela_mgp  LOW     iReady's own growth percentile, not the
                                state's official SGP growth model

No student-level data is written to disk anywhere in this module. Every
function here takes a DataFrame in memory and returns either a DataFrame or
a dict of aggregate numbers -- callers are responsible for discarding the
input DataFrame once aggregation is done.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import pandas as pd


# ----------------------------------------------------------------------
# Canonical schema this module aggregates against. UI code maps a school's
# raw column names onto these keys; nothing downstream needs to know what
# the original file's headers looked like.
# ----------------------------------------------------------------------

CANONICAL_FIELDS = {
    "student_id":        {"required": True,  "label": "Student ID (any unique identifier)"},
    "subject":            {"required": True,  "label": "Subject (ELA / Math)"},
    "grade":              {"required": False, "label": "Grade level"},
    "probable_level_num": {"required": True,  "label": "Probable SBAC Level (# 1-4)"},
    "prior_level_num":    {"required": False, "label": "Prior-year Achievement Level (# 1-4)"},
    "growth_percentile":  {"required": False, "label": "Growth / Student Growth Percentile (1-99)"},
    "agp_met":            {"required": False, "label": "Met Annual Growth Target (Y/N)"},
}

# Best-guess header aliases, used to pre-select a mapping for the user to confirm.
COLUMN_ALIASES = {
    "student_id": ["student id", "studentid", "student_id", "state student id",
                   "student state id", "id"],
    "subject": ["subject"],
    "grade": ["grade", "student grade"],
    "probable_level_num": ["fall probable sbac level (#)", "winter probable sbac level (#)",
                           "spring probable sbac level (#)", "probable sbac level (#)",
                           "probable level (#)", "probable level #"],
    "prior_level_num": ["2024 sbac achievement level (#)", "2025 sbac achievement level (#)",
                        "prior sbac achievement level (#)", "prior achievement level (#)",
                        "prior year achievement level (#)"],
    "growth_percentile": ["sgp", "student growth percentile", "growth percentile"],
    "agp_met": ["agp met", "met agp target", "agp target met"],
}


def guess_mapping(columns: list[str]) -> dict[str, Optional[str]]:
    """Best-effort auto-mapping of raw column names to canonical fields.

    Returns {canonical_key: raw_column_name_or_None}. Always requires human
    confirmation in the UI -- this is a starting point, not a final answer.
    """
    normalized = {c: " ".join(str(c).lower().split()) for c in columns}
    mapping: dict[str, Optional[str]] = {}
    for field_key, aliases in COLUMN_ALIASES.items():
        match = None
        for raw_col, norm in normalized.items():
            if norm in aliases:
                match = raw_col
                break
        if match is None:
            for raw_col, norm in normalized.items():
                if any(alias in norm for alias in aliases):
                    match = raw_col
                    break
        mapping[field_key] = match
    return mapping


def apply_mapping(raw: pd.DataFrame, mapping: dict[str, Optional[str]]) -> pd.DataFrame:
    """Rename/select mapped columns into a clean canonical DataFrame.

    Unmapped optional fields become all-null columns so downstream code can
    check `.notna().any()` uniformly rather than branching on column presence.
    """
    out = pd.DataFrame(index=raw.index)
    for field_key in CANONICAL_FIELDS:
        raw_col = mapping.get(field_key)
        out[field_key] = raw[raw_col] if raw_col is not None else pd.NA

    out["subject"] = out["subject"].astype(str).str.strip().str.upper()
    out["subject"] = out["subject"].replace({
        "ELA": "ELA", "READING": "ELA", "ENGLISH": "ELA", "ENGLISH LANGUAGE ARTS": "ELA",
        "MATH": "MATH", "MATHEMATICS": "MATH",
    })

    for col in ["probable_level_num", "prior_level_num", "growth_percentile"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    if out["agp_met"].notna().any():
        out["agp_met"] = (
            out["agp_met"].astype(str).str.strip().str.upper().isin(["Y", "YES", "TRUE", "1"])
        )
    else:
        out["agp_met"] = pd.NA

    return out


MIN_N = 10  # below this many tested students for a subject, treat the rate as unreliable


@dataclass
class ProjectedRate:
    key: str
    label: str
    value: Optional[float]
    n: int
    confidence: str          # "high" | "medium" | "low"
    note: str = ""


@dataclass
class ProjectionResult:
    rates: dict                     # {measure_key: value_or_None} -- feed straight to nspf_engine.compute
    detail: list                    # list[ProjectedRate], for display
    n_students: int
    n_ela_rows: int
    n_math_rows: int


def _pct_meeting(sub: pd.DataFrame) -> tuple[Optional[float], int]:
    valid = sub["probable_level_num"].dropna()
    n = len(valid)
    if n == 0:
        return None, 0
    return round((valid >= 3).mean() * 100.0, 1), n


def _median_growth(sub: pd.DataFrame) -> tuple[Optional[float], int]:
    valid = sub["growth_percentile"].dropna()
    n = len(valid)
    if n == 0:
        return None, 0
    return round(float(valid.median()), 1), n


def _pct_agp_met(sub: pd.DataFrame) -> tuple[Optional[float], int]:
    valid = sub["agp_met"].dropna()
    n = len(valid)
    if n == 0:
        return None, 0
    return round(valid.mean() * 100.0, 1), n


def _pct_gap_met(sub: pd.DataFrame) -> tuple[Optional[float], int]:
    """Among students who were NOT proficient last year, % who met this year's AGP target."""
    gap_pop = sub[(sub["prior_level_num"].notna()) & (sub["prior_level_num"] < 3)]
    valid = gap_pop["agp_met"].dropna()
    n = len(valid)
    if n == 0:
        return None, 0
    return round(valid.mean() * 100.0, 1), n


def project_rates(df: pd.DataFrame) -> ProjectionResult:
    """Aggregate a canonical per-student DataFrame into NSPF-shaped rates.

    `df` must already be run through apply_mapping(). This function only
    reads it in memory and returns aggregate numbers -- callers should
    discard `df` immediately afterward.
    """
    ela = df[df["subject"] == "ELA"]
    math = df[df["subject"] == "MATH"]

    all_rows = df[df["subject"].isin(["ELA", "MATH"])]
    pooled_val, pooled_n = _pct_meeting(all_rows)

    ela_mgp_val, ela_mgp_n = _median_growth(ela)
    math_mgp_val, math_mgp_n = _median_growth(math)

    ela_agp_val, ela_agp_n = _pct_agp_met(ela)
    math_agp_val, math_agp_n = _pct_agp_met(math)

    ela_gap_val, ela_gap_n = _pct_gap_met(ela)
    math_gap_val, math_gap_n = _pct_gap_met(math)

    def note_for(n, min_n=MIN_N):
        return f"n={n} — below usual minimum-N; treat as directional only" if 0 < n < min_n else f"n={n}"

    detail = [
        ProjectedRate("pooled_proficiency", "Pooled Proficiency (ELA+Math)", pooled_val, pooled_n,
                      "high", note_for(pooled_n)),
        ProjectedRate("math_mgp", "Math MGP (iReady growth %, not state SGP)", math_mgp_val, math_mgp_n,
                      "low", note_for(math_mgp_n)),
        ProjectedRate("ela_mgp", "ELA MGP (iReady growth %, not state SGP)", ela_mgp_val, ela_mgp_n,
                      "low", note_for(ela_mgp_n)),
        ProjectedRate("math_agp", "Met Math AGP Target", math_agp_val, math_agp_n,
                      "medium", note_for(math_agp_n)),
        ProjectedRate("ela_agp", "Met ELA AGP Target", ela_agp_val, ela_agp_n,
                      "medium", note_for(ela_agp_n)),
        ProjectedRate("math_gap", "Prior Non-Proficient Met Math AGP Target", math_gap_val, math_gap_n,
                      "medium", note_for(math_gap_n)),
        ProjectedRate("ela_gap", "Prior Non-Proficient Met ELA AGP Target", ela_gap_val, ela_gap_n,
                      "medium", note_for(ela_gap_n)),
    ]

    rates = {d.key: d.value for d in detail}

    return ProjectionResult(
        rates=rates,
        detail=detail,
        n_students=df["student_id"].nunique() if "student_id" in df else len(df),
        n_ela_rows=len(ela),
        n_math_rows=len(math),
    )


if __name__ == "__main__":
    # Smoke test with synthetic data -- no real student records.
    import numpy as np
    rng = np.random.default_rng(0)
    n = 80
    synthetic = pd.DataFrame({
        "Student ID": [f"S{i:04d}" for i in range(n)],
        "Subject": (["ELA"] * (n // 2)) + (["MATH"] * (n // 2)),
        "Grade": rng.choice([6, 7, 8], size=n),
        "Probable Level (#)": rng.choice([1, 2, 3, 4], size=n, p=[0.35, 0.3, 0.25, 0.1]),
        "SGP": rng.integers(1, 100, size=n),
        "AGP Met": rng.choice(["Y", "N"], size=n),
        "Prior Achievement Level (#)": rng.choice([1, 2, 3, 4], size=n, p=[0.4, 0.3, 0.2, 0.1]),
    })
    mapping = guess_mapping(list(synthetic.columns))
    print("Auto-mapping:", mapping)
    canon = apply_mapping(synthetic, mapping)
    result = project_rates(canon)
    print(f"\nStudents: {result.n_students}  ELA rows: {result.n_ela_rows}  Math rows: {result.n_math_rows}\n")
    for d in result.detail:
        print(f"  [{d.confidence:6}] {d.label:45} = {d.value}  ({d.note})")
