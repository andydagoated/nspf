"""
NWEA MAP Growth -> NSPF Projected Rates
========================================
Turns a per-student MAP Growth export (Comprehensive Data File or Combined
Report, BOY/MOY) into the aggregate rates nspf_engine.compute() expects.

THIS PRODUCES A PROJECTION, NOT AN OFFICIAL NSPF MEASURE.

Confidence by measure:
  - pooled_proficiency  HIGH    when built from NWEA's Projected Proficiency
                                (state linking study, e.g. Smarter Balanced);
                        LOW     when built from an achievement-percentile cut
                                fallback the user supplies
  - math_agp / ela_agp  MEDIUM  proxied by Met Projected Growth (NWEA's own
                                growth projection, not the state AGP target)
  - math_gap / ela_gap  MEDIUM  needs Met Projected Growth AND a matched
                                prior-year state achievement level
  - math_mgp / ela_mgp  LOW     median Conditional Growth Percentile (CGP).
                                CGP is the closest MAP analog to a student
                                growth percentile but is NOT the state's
                                official SGP model.

MAP quirks handled here:
  - Course values: "Reading" maps to ELA; "Language Usage" and "Science" rows
    are dropped (counted, surfaced to the UI) because NSPF's ELA measures are
    anchored to the reading/ELA assessment.
  - Met Projected Growth arrives as "Yes*/No*" (asterisk = projection based on
    incomplete data); the flag is read leniently, the asterisk is ignored.
  - If the met flag is absent but Observed Growth and Projected Growth are
    both present, met = observed >= projected.
  - Multi-term files (Fall + Winter in one CDF) are filtered to the most
    recent term so students aren't double-counted; if terms can't be parsed,
    all rows are kept and the caller is warned via ProjectionResult.term_note.

No student-level data is written to disk anywhere in this module. Every
function takes a DataFrame in memory and returns aggregates -- callers are
responsible for discarding the input DataFrame once aggregation is done.
"""

from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional
import pandas as pd


# ----------------------------------------------------------------------
# Canonical schema. UI code maps a school's raw column names onto these
# keys; nothing downstream needs to know the original headers.
# ----------------------------------------------------------------------

CANONICAL_FIELDS = {
    "student_id":         {"required": True,  "label": "Student ID (any unique identifier)"},
    "subject":            {"required": True,  "label": "Course / Subject (Reading, Mathematics, ...)"},
    "first_name":         {"required": False, "label": "First name (for the workbook export)"},
    "last_name":          {"required": False, "label": "Last name (for the workbook export)"},
    "grade":              {"required": False, "label": "Grade level"},
    "term":               {"required": False, "label": "Term (e.g. 'Winter 2026-2027')"},
    "projected_prof":     {"required": False, "label": "Projected Proficiency Level (linking study)"},
    "percentile":         {"required": False, "label": "Achievement / Test Percentile (1-99)"},
    "cgp":                {"required": False, "label": "Conditional Growth Percentile (1-99)"},
    "met_growth":         {"required": False, "label": "Met Projected Growth (Yes/No)"},
    "observed_growth":    {"required": False, "label": "Observed Growth (RIT)"},
    "projected_growth":   {"required": False, "label": "Projected Growth (RIT)"},
    "prior_level_num":    {"required": False, "label": "Prior-year State Achievement Level (# 1-4)"},
}

# Best-guess header aliases from NWEA CDF / Combined Report exports.
COLUMN_ALIASES = {
    "student_id": ["studentid", "student id", "student_id", "state student id",
                   "student state id", "id"],
    "subject": ["course", "subject", "measurementscale", "discipline"],
    "first_name": ["studentfirstname", "student first name", "first name", "firstname"],
    "last_name": ["studentlastname", "student last name", "last name", "lastname"],
    "grade": ["grade", "student grade", "tests grade"],
    "term": ["termname", "term name", "term", "term tested", "termtested"],
    "projected_prof": ["projectedproficiencylevel1", "projected proficiency level 1",
                       "projectedproficiencylevel2", "projected proficiency level 2",
                       "projectedproficiencylevel3", "projected proficiency level 3",
                       "projectedproficiencylevel", "projected proficiency level",
                       "projected proficiency"],
    "percentile": ["testpercentile", "test percentile", "achievement percentile",
                   "percentile", "achievementquintile percentile", "percentile rank"],
    "cgp": ["conditionalgrowthpercentile", "conditional growth percentile", "cgp",
            "falltowinterconditionalgrowthpercentile", "falltospringconditionalgrowthpercentile",
            "fall to winter conditional growth percentile",
            "fall to spring conditional growth percentile"],
    "met_growth": ["metprojectedgrowth", "met projected growth", "met growth projection",
                   "falltowintermetprojectedgrowth", "falltospringmetprojectedgrowth",
                   "fall to winter met projected growth", "fall to spring met projected growth"],
    "observed_growth": ["observedgrowth", "observed growth", "falltowinterobservedgrowth",
                        "falltospringobservedgrowth", "fall to winter observed growth",
                        "fall to spring observed growth"],
    "projected_growth": ["projectedgrowth", "projected growth", "falltowinterprojectedgrowth",
                         "falltospringprojectedgrowth", "fall to winter projected growth",
                         "fall to spring projected growth"],
    "prior_level_num": ["prior sbac achievement level (#)", "prior achievement level (#)",
                        "prior year achievement level (#)", "prior achievement level",
                        "2025 sbac achievement level (#)", "2026 sbac achievement level (#)"],
}


def guess_mapping(columns: list[str]) -> dict[str, Optional[str]]:
    """Best-effort auto-mapping of raw column names to canonical fields.

    Returns {canonical_key: raw_column_name_or_None}. Always requires human
    confirmation in the UI -- this is a starting point, not a final answer.
    """
    normalized = {c: " ".join(str(c).lower().split()) for c in columns}
    mapping: dict[str, Optional[str]] = {}
    claimed: set = set()
    # Pass 1: exact alias matches for every field.
    for field_key, aliases in COLUMN_ALIASES.items():
        match = None
        for raw_col, norm in normalized.items():
            if norm in aliases and raw_col not in claimed:
                match = raw_col
                break
        mapping[field_key] = match
        if match is not None:
            claimed.add(match)
    # Pass 2: substring fallback, never re-claiming a column another field owns
    # (prevents e.g. MetProjectedGrowth also matching projected_growth).
    for field_key, aliases in COLUMN_ALIASES.items():
        if mapping[field_key] is not None:
            continue
        for raw_col, norm in normalized.items():
            if raw_col in claimed:
                continue
            if any(alias in norm for alias in aliases):
                mapping[field_key] = raw_col
                claimed.add(raw_col)
                break
    return mapping


# --- Parsers -----------------------------------------------------------

_LEVEL_DIGIT = re.compile(r"([1-4])")

# Keyword fallbacks for linking-study proficiency text when no digit appears.
# Negations must be checked BEFORE positives ("not on track" contains "on track").
_PROF_KEYWORDS = [
    (("does not", "not met", "not on track", "below", "minimal", "novice"), 1),
    (("approach", "nearly", "partial", "close"), 2),
    (("exceed",), 4),
    (("meets", "met ", "on track", "proficient"), 3),
]


def parse_prof_level(value) -> Optional[float]:
    """'Level 3', 'L3', '3', 'Meets Standard', 'Not on Track' -> 1-4 or None."""
    if pd.isna(value):
        return None
    s = str(value).strip().lower()
    if not s:
        return None
    m = _LEVEL_DIGIT.search(s)
    if m:
        return float(m.group(1))
    for keys, level in _PROF_KEYWORDS:
        if any(k in s for k in keys):
            return float(level)
    return None


def parse_yes_no(value) -> Optional[bool]:
    """'Yes', 'Yes*', 'No*', 'Y', 'TRUE', '1' -> bool; blank/'*' alone -> None."""
    if pd.isna(value):
        return None
    s = re.sub(r"[^a-z0-9]", "", str(value).strip().lower())
    if not s:
        return None
    if s.startswith(("y", "t")) or s == "1":
        return True
    if s.startswith(("n", "f")) or s == "0":
        return False
    return None


_SEASON_ORDER = {"fall": 0, "winter": 1, "spring": 2, "summer": 3}
_TERM_RE = re.compile(r"(fall|winter|spring|summer)\D*(\d{4})", re.IGNORECASE)


def term_sort_key(term) -> Optional[tuple]:
    """'Winter 2026-2027' -> (2026, 1). None when unparseable."""
    if pd.isna(term):
        return None
    m = _TERM_RE.search(str(term))
    if not m:
        return None
    season, year = m.group(1).lower(), int(m.group(2))
    return (year, _SEASON_ORDER[season])


def apply_mapping(raw: pd.DataFrame, mapping: dict[str, Optional[str]]) -> pd.DataFrame:
    """Rename/select mapped columns into a clean canonical DataFrame.

    Unmapped optional fields become all-null columns so downstream code can
    check `.notna().any()` uniformly rather than branching on presence.
    """
    out = pd.DataFrame(index=raw.index)
    for field_key in CANONICAL_FIELDS:
        raw_col = mapping.get(field_key)
        out[field_key] = raw[raw_col] if raw_col is not None else pd.NA

    subj = out["subject"].astype(str).str.strip().str.upper()
    out["subject"] = subj.replace({
        "READING": "ELA", "ELA": "ELA", "ENGLISH": "ELA",
        "ENGLISH LANGUAGE ARTS": "ELA", "READING (SPANISH)": "ELA",
        "MATH": "MATH", "MATHEMATICS": "MATH", "MATH K-12": "MATH",
        "MATHEMATICS K-12": "MATH", "GROWTH: MATH K-12": "MATH",
        "GROWTH: READING K-12": "ELA",
    })
    # Anything else ("LANGUAGE USAGE", "SCIENCE...", etc.) stays as-is and is
    # excluded by project_rates, which counts what it dropped.

    out["projected_prof"] = out["projected_prof"].map(parse_prof_level)
    out["met_growth"] = out["met_growth"].map(parse_yes_no)
    for col in ["percentile", "cgp", "observed_growth", "projected_growth", "prior_level_num"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    # Growth-met fallback: observed vs projected RIT growth.
    need = out["met_growth"].isna() & out["observed_growth"].notna() & out["projected_growth"].notna()
    out.loc[need, "met_growth"] = out.loc[need, "observed_growth"] >= out.loc[need, "projected_growth"]

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
    n_dropped_other: int            # Language Usage / Science / unrecognized courses
    term_used: Optional[str]        # term the projection was filtered to, if any
    term_note: str = ""


def _latest_term_filter(df: pd.DataFrame) -> tuple[pd.DataFrame, Optional[str], str]:
    """Keep only the most recent term when several are present."""
    if not df["term"].notna().any():
        return df, None, ""
    keys = df["term"].map(term_sort_key)
    parseable = keys.notna()
    terms = df.loc[parseable, "term"].astype(str)
    if terms.nunique() <= 1:
        only = terms.iloc[0] if len(terms) else None
        return df, only, ""
    latest_key = max(keys[parseable])
    latest_terms = {t for t, k in zip(terms, keys[parseable]) if k == latest_key}
    latest_name = sorted(latest_terms)[0]
    kept = df[parseable & (keys == latest_key)]
    note = (f"Multiple terms found; using {latest_name} only "
            f"({len(kept):,} of {len(df):,} rows) so students aren't double-counted.")
    return kept, latest_name, note


def _dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """One row per student per subject (a student retested in a term keeps the first row)."""
    if df["student_id"].notna().any():
        return df.drop_duplicates(subset=["student_id", "subject"], keep="first")
    return df


def _pct_proficient(sub: pd.DataFrame, percentile_cut: Optional[float]) -> tuple[Optional[float], int, str]:
    """% projected proficient. Linking-study level when present; percentile-cut fallback otherwise."""
    levels = sub["projected_prof"].dropna()
    if len(levels) > 0:
        return round((levels >= 3).mean() * 100.0, 1), len(levels), "linking"
    if percentile_cut is not None:
        pct = sub["percentile"].dropna()
        if len(pct) > 0:
            return round((pct >= percentile_cut).mean() * 100.0, 1), len(pct), "percentile"
    return None, 0, "none"


def _median_cgp(sub: pd.DataFrame) -> tuple[Optional[float], int]:
    valid = sub["cgp"].dropna()
    if len(valid) == 0:
        return None, 0
    return round(float(valid.median()), 1), len(valid)


def _pct_met_growth(sub: pd.DataFrame) -> tuple[Optional[float], int]:
    valid = sub["met_growth"].dropna()
    if len(valid) == 0:
        return None, 0
    return round(valid.astype(bool).mean() * 100.0, 1), len(valid)


def _pct_gap_met(sub: pd.DataFrame) -> tuple[Optional[float], int]:
    """Among students NOT proficient on last year's state test, % who met projected growth."""
    gap_pop = sub[(sub["prior_level_num"].notna()) & (sub["prior_level_num"] < 3)]
    valid = gap_pop["met_growth"].dropna()
    if len(valid) == 0:
        return None, 0
    return round(valid.astype(bool).mean() * 100.0, 1), len(valid)


def project_rates(df: pd.DataFrame, percentile_cut: Optional[float] = None) -> ProjectionResult:
    """Aggregate a canonical per-student DataFrame into NSPF-shaped rates.

    `df` must already be run through apply_mapping(). Reads in memory only;
    callers should discard `df` immediately afterward.

    percentile_cut: optional achievement-percentile threshold used to estimate
    proficiency ONLY when no linking-study Projected Proficiency data exists.
    """
    df, term_used, term_note = _latest_term_filter(df)
    df = _dedupe(df)

    known = df[df["subject"].isin(["ELA", "MATH"])]
    n_dropped = len(df) - len(known)
    ela = known[known["subject"] == "ELA"]
    math = known[known["subject"] == "MATH"]

    pooled_val, pooled_n, pooled_src = _pct_proficient(known, percentile_cut)
    ela_mgp_val, ela_mgp_n = _median_cgp(ela)
    math_mgp_val, math_mgp_n = _median_cgp(math)
    ela_agp_val, ela_agp_n = _pct_met_growth(ela)
    math_agp_val, math_agp_n = _pct_met_growth(math)
    ela_gap_val, ela_gap_n = _pct_gap_met(ela)
    math_gap_val, math_gap_n = _pct_gap_met(math)

    def note_for(n, min_n=MIN_N):
        return f"n={n} — below usual minimum-N; treat as directional only" if 0 < n < min_n else f"n={n}"

    if pooled_src == "linking":
        pooled_conf = "high"
        pooled_note = f"NWEA linking-study Projected Proficiency; {note_for(pooled_n)}"
    elif pooled_src == "percentile":
        pooled_conf = "low"
        pooled_note = (f"Estimated from achievement percentile >= {percentile_cut:g} "
                       f"(user-set cut, NOT a linking study); {note_for(pooled_n)}")
    else:
        pooled_conf = "high"
        pooled_note = "no Projected Proficiency data in this upload"

    detail = [
        ProjectedRate("pooled_proficiency", "Pooled Proficiency (ELA+Math)", pooled_val, pooled_n,
                      pooled_conf, pooled_note),
        ProjectedRate("math_mgp", "Math MGP (MAP CGP median, not state SGP)", math_mgp_val, math_mgp_n,
                      "low", note_for(math_mgp_n)),
        ProjectedRate("ela_mgp", "ELA MGP (MAP CGP median, not state SGP)", ela_mgp_val, ela_mgp_n,
                      "low", note_for(ela_mgp_n)),
        ProjectedRate("math_agp", "Met Math AGP Target (proxied by Met Projected Growth)",
                      math_agp_val, math_agp_n, "medium", note_for(math_agp_n)),
        ProjectedRate("ela_agp", "Met ELA AGP Target (proxied by Met Projected Growth)",
                      ela_agp_val, ela_agp_n, "medium", note_for(ela_agp_n)),
        ProjectedRate("math_gap", "Prior Non-Proficient Met Math AGP Target",
                      math_gap_val, math_gap_n, "medium", note_for(math_gap_n)),
        ProjectedRate("ela_gap", "Prior Non-Proficient Met ELA AGP Target",
                      ela_gap_val, ela_gap_n, "medium", note_for(ela_gap_n)),
    ]

    return ProjectionResult(
        rates={d.key: d.value for d in detail},
        detail=detail,
        n_students=known["student_id"].nunique() if known["student_id"].notna().any() else len(known),
        n_ela_rows=len(ela),
        n_math_rows=len(math),
        n_dropped_other=n_dropped,
        term_used=term_used,
        term_note=term_note,
    )


if __name__ == "__main__":
    # Smoke test with synthetic data -- no real student records.
    import numpy as np
    rng = np.random.default_rng(7)
    n = 120
    synthetic = pd.DataFrame({
        "StudentID": [f"S{i:04d}" for i in range(n)] * 2,
        "Course": (["Reading"] * n) + (["Mathematics"] * n),
        "Grade": list(rng.choice([6, 7, 8], size=n)) * 2,
        "TermName": (["Fall 2026-2027"] * (n // 2) + ["Winter 2026-2027"] * (n - n // 2)) * 2,
        "ProjectedProficiencyLevel1": rng.choice(
            ["Level 1", "Level 2", "Level 3", "Level 4"], size=2 * n, p=[0.3, 0.3, 0.3, 0.1]),
        "TestPercentile": rng.integers(1, 100, size=2 * n),
        "ConditionalGrowthPercentile": rng.integers(1, 100, size=2 * n),
        "MetProjectedGrowth": rng.choice(["Yes", "Yes*", "No", "No*"], size=2 * n),
        "Prior Achievement Level (#)": rng.choice([1, 2, 3, 4], size=2 * n, p=[0.4, 0.3, 0.2, 0.1]),
    })
    mapping = guess_mapping(list(synthetic.columns))
    print("Auto-mapping:", mapping)
    canon = apply_mapping(synthetic, mapping)
    result = project_rates(canon)
    print(f"\nTerm used: {result.term_used}  ({result.term_note})")
    print(f"Students: {result.n_students}  ELA rows: {result.n_ela_rows}  "
          f"Math rows: {result.n_math_rows}  Dropped (non-ELA/Math): {result.n_dropped_other}\n")
    for d in result.detail:
        print(f"  [{d.confidence:6}] {d.label:55} = {d.value}  ({d.note})")

    # Percentile-cut fallback path
    no_link = synthetic.drop(columns=["ProjectedProficiencyLevel1"])
    canon2 = apply_mapping(no_link, guess_mapping(list(no_link.columns)))
    r2 = project_rates(canon2, percentile_cut=60)
    pooled = [d for d in r2.detail if d.key == "pooled_proficiency"][0]
    print(f"\nFallback pooled proficiency: {pooled.value} [{pooled.confidence}] ({pooled.note})")

    # Parser unit checks
    checks = [
        (parse_prof_level("Level 3"), 3.0), (parse_prof_level("L4"), 4.0),
        (parse_prof_level("Meets Standard"), 3.0), (parse_prof_level("Not on Track"), 1.0),
        (parse_prof_level("Approaching"), 2.0), (parse_prof_level(None), None),
        (parse_yes_no("Yes*"), True), (parse_yes_no("No*"), False), (parse_yes_no(""), None),
        (term_sort_key("Winter 2026-2027"), (2026, 1)), (term_sort_key("Fall 2026-2027"), (2026, 0)),
    ]
    ok = all(got == want for got, want in checks)
    print("\nParser checks:", "ALL PASS" if ok else f"FAILURES: {[c for c in checks if c[0] != c[1]]}")
