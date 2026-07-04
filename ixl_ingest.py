"""
IXL Diagnostic Snapshot -> NSPF Projected Rates
================================================
Turns a per-student IXL Real-Time Diagnostic export into the aggregate
rates nspf_engine.compute() expects.

THIS PRODUCES A PROJECTION, NOT AN OFFICIAL NSPF MEASURE.

How this differs from the iReady path (iready_ingest.py)
---------------------------------------------------------
iReady exports include a "Probable SBAC Level" -- a proficiency projection
computed by the vendor. IXL exports do NOT. IXL reports a diagnostic level
on its own scale, where roughly 100 points = one grade level (e.g. a level
of 700 ~= working at the start of 7th grade). There is no published
IXL -> SBAC concordance for Nevada, so this module applies two EXPLICIT,
ADJUSTABLE linking assumptions instead of pretending an equivalence exists:

  Linking rule 1 (proficiency proxy):
      projected proficient  <=>  level >= grade*100 + offset
      Default offset = 0 ("at or above grade level ~= on track to L3+").
      The offset is a UI slider so a school can calibrate it against its
      own historical IXL-vs-SBAC results.

  Linking rule 2 (growth-target / AGP proxy, needs a BOY level too):
      expected gain for the elapsed window is prorated from an expected
      ANNUAL gain (default 100 points ~= one grade level per year).
      Students BELOW grade level at BOY get a steeper catch-up target:
      annual target = annual_gain + (BOY deficit / 3), i.e. on pace to
      close the gap within three years while content advances -- a
      deliberate analog of the state's 3-year AGP concept, NOT the
      state's actual AGP determination.

Confidence by measure:
  - pooled_proficiency  MEDIUM  linking rule 1 is an assumption, not a
                                vendor projection or a validated concordance
  - math_agp / ela_agp  LOW     linking rule 2 proxy; needs BOY + current
  - math_gap / ela_gap  LOW     rule-2 proxy among students below grade
                                level at BOY (or prior SBAC < 3 if mapped,
                                which upgrades the population to the real
                                gap-closing definition -> MEDIUM)
  - math_mgp / ela_mgp  NOT DERIVABLE. IXL has no peer-normed growth
                                percentile. Reported as unavailable rather
                                than faked; the engine's existing logic
                                treats the school as provisionally rated.

No student-level data is written to disk anywhere in this module. Every
function takes a DataFrame in memory and returns aggregates -- callers are
responsible for discarding the input DataFrame once aggregation is done.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import pandas as pd

# Reuse the result containers so pages can treat both ingest paths identically.
from iready_ingest import ProjectedRate, ProjectionResult, MIN_N


# ----------------------------------------------------------------------
# Canonical schema. IXL diagnostic exports are typically WIDE (one row per
# student, separate Math / ELA level columns), so the canonical form here
# is wide too; _to_long() melts it before aggregation.
# ----------------------------------------------------------------------

CANONICAL_FIELDS = {
    "student_id":     {"required": True,  "label": "Student ID (any unique identifier)"},
    "grade":          {"required": True,  "label": "Grade level (needed for the grade-level linking rule)"},
    "math_level":     {"required": False, "label": "Current Math diagnostic level"},
    "ela_level":      {"required": False, "label": "Current ELA diagnostic level"},
    "math_level_boy": {"required": False, "label": "Beginning-of-year Math level (enables growth proxy)"},
    "ela_level_boy":  {"required": False, "label": "Beginning-of-year ELA level (enables growth proxy)"},
    "prior_math_level_num": {"required": False, "label": "Prior-year SBAC Math Achievement Level (# 1-4)"},
    "prior_ela_level_num":  {"required": False, "label": "Prior-year SBAC ELA Achievement Level (# 1-4)"},
}

# Best-guess header aliases, used to pre-select a mapping for the user to confirm.
COLUMN_ALIASES = {
    "student_id": ["student id", "studentid", "student_id", "state student id",
                   "student state id", "id number", "id"],
    "grade": ["grade", "grade level", "student grade"],
    "math_level": ["math level", "overall math level", "current math level",
                   "math diagnostic level", "math overall"],
    "ela_level": ["ela level", "overall ela level", "current ela level",
                  "language arts level", "ela diagnostic level", "ela overall",
                  "overall language arts level"],
    "math_level_boy": ["boy math level", "beginning of year math level", "fall math level",
                       "math level (boy)", "starting math level", "math level start"],
    "ela_level_boy": ["boy ela level", "beginning of year ela level", "fall ela level",
                      "ela level (boy)", "starting ela level", "ela level start",
                      "beginning of year language arts level"],
    "prior_math_level_num": ["prior sbac math level (#)", "prior math achievement level (#)",
                             "2025 sbac math level (#)", "sbac math level"],
    "prior_ela_level_num": ["prior sbac ela level (#)", "prior ela achievement level (#)",
                            "2025 sbac ela level (#)", "sbac ela level"],
}


def guess_mapping(columns: list[str]) -> dict[str, Optional[str]]:
    """Best-effort auto-mapping of raw column names to canonical fields.

    Returns {canonical_key: raw_column_name_or_None}. Always requires human
    confirmation in the UI -- this is a starting point, not a final answer.
    """
    normalized = {c: " ".join(str(c).lower().split()) for c in columns}
    mapping: dict[str, Optional[str]] = {}
    claimed: set = set()
    for field_key, aliases in COLUMN_ALIASES.items():
        match = None
        for raw_col, norm in normalized.items():
            if raw_col not in claimed and norm in aliases:
                match = raw_col
                break
        if match is None:
            for raw_col, norm in normalized.items():
                if raw_col not in claimed and any(alias in norm for alias in aliases):
                    match = raw_col
                    break
        if match is not None:
            claimed.add(match)
        mapping[field_key] = match
    return mapping


def apply_mapping(raw: pd.DataFrame, mapping: dict[str, Optional[str]]) -> pd.DataFrame:
    """Rename/select mapped columns into a clean canonical (wide) DataFrame.

    Unmapped optional fields become all-null columns so downstream code can
    check `.notna().any()` uniformly rather than branching on column presence.
    """
    out = pd.DataFrame(index=raw.index)
    for field_key in CANONICAL_FIELDS:
        raw_col = mapping.get(field_key)
        out[field_key] = raw[raw_col] if raw_col is not None else pd.NA

    numeric_cols = ["grade", "math_level", "ela_level", "math_level_boy",
                    "ela_level_boy", "prior_math_level_num", "prior_ela_level_num"]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    return out


@dataclass
class LinkingSettings:
    """The explicit assumptions connecting IXL's scale to NSPF-shaped rates.

    Every value here is surfaced as a UI control -- nothing is hidden.
    """
    proficiency_offset: float = 0.0   # points added to grade*100 threshold
    annual_gain: float = 100.0        # expected IXL points per full school year
    months_elapsed: float = 4.0       # months between BOY snapshot and this one
    catch_up_years: float = 3.0       # AGP analog horizon for below-level students

    @property
    def window_fraction(self) -> float:
        return max(0.0, min(1.0, self.months_elapsed / 9.0))  # 9-month school year


def _to_long(df: pd.DataFrame) -> pd.DataFrame:
    """Melt the canonical wide frame into one row per (student, subject)."""
    frames = []
    for subject, level_col, boy_col, prior_col in [
        ("MATH", "math_level", "math_level_boy", "prior_math_level_num"),
        ("ELA", "ela_level", "ela_level_boy", "prior_ela_level_num"),
    ]:
        sub = pd.DataFrame({
            "student_id": df["student_id"],
            "grade": df["grade"],
            "subject": subject,
            "level": df[level_col],
            "level_boy": df[boy_col],
            "prior_level_num": df[prior_col],
        })
        frames.append(sub[sub["level"].notna()])
    return pd.concat(frames, ignore_index=True)


def _derive_flags(long_df: pd.DataFrame, s: LinkingSettings) -> pd.DataFrame:
    """Apply the two linking rules; returns long_df with proxy columns added."""
    out = long_df.copy()
    grade_threshold = out["grade"] * 100.0 + s.proficiency_offset

    # Rule 1: proficiency proxy
    out["proficient_proxy"] = out["level"] >= grade_threshold

    # Rule 2: growth-target proxy (only where a BOY level exists)
    has_growth = out["level_boy"].notna()
    boy_deficit = (grade_threshold - out["level_boy"]).clip(lower=0.0)
    annual_target = s.annual_gain + boy_deficit / s.catch_up_years
    window_target = annual_target * s.window_fraction
    actual_gain = out["level"] - out["level_boy"]
    out["agp_met_proxy"] = pd.NA
    out.loc[has_growth, "agp_met_proxy"] = (
        actual_gain[has_growth] >= window_target[has_growth]
    )

    # Gap population: prior SBAC non-proficient if mapped, else below grade at BOY
    out["has_real_prior"] = out["prior_level_num"].notna()
    out["gap_population"] = pd.NA
    out.loc[out["has_real_prior"], "gap_population"] = out.loc[out["has_real_prior"], "prior_level_num"] < 3
    fallback = (~out["has_real_prior"]) & has_growth
    out.loc[fallback, "gap_population"] = out.loc[fallback, "level_boy"] < grade_threshold[fallback]

    return out


def _pct(series: pd.Series) -> tuple[Optional[float], int]:
    valid = series.dropna()
    n = len(valid)
    if n == 0:
        return None, 0
    return round(valid.astype(bool).mean() * 100.0, 1), n


def project_rates(df: pd.DataFrame, settings: Optional[LinkingSettings] = None) -> ProjectionResult:
    """Aggregate a canonical (wide) per-student DataFrame into NSPF-shaped rates.

    `df` must already be run through apply_mapping(). This function only
    reads it in memory and returns aggregate numbers -- callers should
    discard `df` immediately afterward.
    """
    s = settings or LinkingSettings()
    long_df = _derive_flags(_to_long(df), s)

    ela = long_df[long_df["subject"] == "ELA"]
    math = long_df[long_df["subject"] == "MATH"]

    pooled_val, pooled_n = _pct(long_df["proficient_proxy"])
    math_agp_val, math_agp_n = _pct(math["agp_met_proxy"])
    ela_agp_val, ela_agp_n = _pct(ela["agp_met_proxy"])

    def gap_rate(sub: pd.DataFrame) -> tuple[Optional[float], int, bool]:
        pop = sub[sub["gap_population"].fillna(False).astype(bool)]
        val, n = _pct(pop["agp_met_proxy"])
        used_real_prior = bool(pop["has_real_prior"].all()) and len(pop) > 0
        return val, n, used_real_prior

    math_gap_val, math_gap_n, math_gap_real = gap_rate(math)
    ela_gap_val, ela_gap_n, ela_gap_real = gap_rate(ela)

    def note_for(n, extra=""):
        base = f"n={n} — below usual minimum-N; treat as directional only" if 0 < n < MIN_N else f"n={n}"
        return f"{base}{('; ' + extra) if extra else ''}"

    link1 = f"linking rule: level >= grade*100{s.proficiency_offset:+g}"
    link2 = (f"proxy target: {s.annual_gain:g} pts/yr (+deficit/{s.catch_up_years:g}yr if below level), "
             f"prorated to {s.months_elapsed:g} months")

    detail = [
        ProjectedRate("pooled_proficiency", "Pooled Proficiency (IXL level vs grade)", pooled_val, pooled_n,
                      "medium", note_for(pooled_n, link1)),
        ProjectedRate("math_mgp", "Math MGP", None, 0,
                      "low", "not derivable from IXL — no peer-normed growth percentile exists"),
        ProjectedRate("ela_mgp", "ELA MGP", None, 0,
                      "low", "not derivable from IXL — no peer-normed growth percentile exists"),
        ProjectedRate("math_agp", "Met Math Growth Target (IXL proxy)", math_agp_val, math_agp_n,
                      "low", note_for(math_agp_n, link2)),
        ProjectedRate("ela_agp", "Met ELA Growth Target (IXL proxy)", ela_agp_val, ela_agp_n,
                      "low", note_for(ela_agp_n, link2)),
        ProjectedRate("math_gap", "Prior Non-Proficient Met Math Target (proxy)", math_gap_val, math_gap_n,
                      "medium" if math_gap_real else "low",
                      note_for(math_gap_n, "population = prior SBAC < 3" if math_gap_real
                               else "population = below grade level at BOY (proxy)")),
        ProjectedRate("ela_gap", "Prior Non-Proficient Met ELA Target (proxy)", ela_gap_val, ela_gap_n,
                      "medium" if ela_gap_real else "low",
                      note_for(ela_gap_n, "population = prior SBAC < 3" if ela_gap_real
                               else "population = below grade level at BOY (proxy)")),
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
    rng = np.random.default_rng(7)
    n = 90
    grades = rng.choice([6, 7, 8], size=n)
    boy_math = grades * 100 - rng.integers(-40, 160, size=n)   # some below, some above
    boy_ela = grades * 100 - rng.integers(-40, 140, size=n)
    synthetic = pd.DataFrame({
        "Student ID": [f"S{i:04d}" for i in range(n)],
        "Grade level": grades,
        "Overall Math Level": boy_math + rng.integers(0, 70, size=n),
        "Overall ELA Level": boy_ela + rng.integers(10, 80, size=n),
        "BOY Math Level": boy_math,
        "BOY ELA Level": boy_ela,
        "Prior SBAC Math Level (#)": rng.choice([1, 2, 3, 4], size=n, p=[0.2, 0.3, 0.35, 0.15]),
    })
    mapping = guess_mapping(list(synthetic.columns))
    print("Auto-mapping:", mapping)
    canon = apply_mapping(synthetic, mapping)
    result = project_rates(canon, LinkingSettings(months_elapsed=4))
    print(f"\nStudents: {result.n_students}  ELA rows: {result.n_ela_rows}  Math rows: {result.n_math_rows}\n")
    for d in result.detail:
        val = f"{d.value}" if d.value is not None else "—"
        print(f"  [{d.confidence:6}] {d.label:48} = {val:>6}  ({d.note})")
