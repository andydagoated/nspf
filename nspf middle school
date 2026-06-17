"""
Nevada School Performance Framework (NSPF) - Middle School Star-Rating Calculator
=================================================================================

This module computes a middle school's NSPF index (0-100) and star rating (1-5)
from its raw indicator values. It is the DETERMINISTIC core of a larger
prediction pipeline: forecast the indicator inputs separately, then run them
through this engine.

-------------------------------------------------------------------------------
!!  READ BEFORE USING  !!
-------------------------------------------------------------------------------
The NDE revises NSPF point allocations, indicator scoring rubrics, and star
cut scores periodically. EVERY number in the CONFIG section below is an
ILLUSTRATIVE PLACEHOLDER based on the framework's general historical structure.
You MUST replace them with the exact values from the official NDE NSPF technical
guide for the school year you are predicting.

Validation gate: before trusting any projection, feed in last year's ACTUAL
published indicator values for a batch of real middle schools (from the Nevada
Report Card / accountability portal) and confirm this engine reproduces their
published star ratings. If it doesn't match, the CONFIG is wrong.
-------------------------------------------------------------------------------

Design notes:
- The index is computed as (points earned / points possible) * 100. This handles
  schools that are missing an indicator (e.g., a small charter with too few
  English learners to report) by dropping that indicator from BOTH earned and
  possible, rather than forcing a fixed denominator. Confirm this matches the
  official reweighting / minimum-N rules for your year.
- Each indicator's scorer returns a FRACTION in [0, 1] of its max points. Swap
  in the official rubric (proportional, banded thresholds, etc.) per indicator.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional


# ============================================================
# 1. SCORING PRIMITIVES
#    Each returns a fraction in [0, 1] of an indicator's max points.
#    Replace with the official NSPF rubric for each indicator.
# ============================================================

def linear_fraction(floor: float, ceiling: float, higher_is_better: bool = True
                    ) -> Callable[[float], float]:
    """Proportional credit between a floor (0 pts) and ceiling (full pts)."""
    def scorer(value: float) -> float:
        if ceiling == floor:
            return 1.0
        frac = (value - floor) / (ceiling - floor)
        if not higher_is_better:
            frac = 1.0 - frac
        return max(0.0, min(1.0, frac))
    return scorer


def band_fraction(bands: list[tuple[float, float]], higher_is_better: bool = True
                 ) -> Callable[[float], float]:
    """
    Threshold bands. `bands` = list of (threshold, fraction), evaluated in order.
    For higher_is_better, the first band whose threshold the value meets/exceeds
    wins. NSPF frequently uses banded cut points like this.
    """
    ordered = sorted(bands, key=lambda b: b[0], reverse=higher_is_better)
    def scorer(value: float) -> float:
        for threshold, frac in ordered:
            if (higher_is_better and value >= threshold) or \
               (not higher_is_better and value <= threshold):
                return frac
        return 0.0
    return scorer


# ============================================================
# 2. RAW INPUTS
#    A middle school's indicator values for one year.
#    Use None for any indicator that does not apply / is suppressed by min-N.
# ============================================================

@dataclass
class MiddleSchoolInputs:
    # --- Academic Achievement (proficiency rates, % of students proficient) ---
    ela_proficiency: Optional[float] = None        # 0-100
    math_proficiency: Optional[float] = None        # 0-100
    science_proficiency: Optional[float] = None      # 0-100

    # --- Student Growth (Median Growth Percentile, 1-99) ---
    ela_mgp: Optional[float] = None                  # 1-99
    math_mgp: Optional[float] = None                 # 1-99
    # Adequate Growth Percentile: % of students meeting their growth target
    ela_agp_pct: Optional[float] = None              # 0-100
    math_agp_pct: Optional[float] = None             # 0-100

    # --- English Learner Progress (% making progress toward proficiency) ---
    el_progress: Optional[float] = None              # 0-100

    # --- Closing Opportunity Gaps ---
    # Stand-in for the gap-closing measure (e.g., growth of the lowest quartile
    # or prior-non-proficient students). Confirm the exact official definition.
    opportunity_gap_index: Optional[float] = None    # 0-100

    # --- Student Engagement ---
    chronic_absenteeism: Optional[float] = None      # 0-100, LOWER is better
    climate_survey: Optional[float] = None           # 0-100, optional


# ============================================================
# 3. CONFIG  --  *** ALL PLACEHOLDERS: VERIFY AGAINST NDE GUIDE ***
# ============================================================

@dataclass
class NSPFConfig:
    # ---- Max points per indicator (must reflect official weights) ----
    # Historical MS structure sums to ~100 across these five components.
    pts_ela_proficiency: float = 10.0
    pts_math_proficiency: float = 10.0
    pts_science_proficiency: float = 10.0          # Achievement subtotal ~30

    pts_ela_mgp: float = 7.5
    pts_math_mgp: float = 7.5
    pts_ela_agp: float = 7.5
    pts_math_agp: float = 7.5                       # Growth subtotal ~30

    pts_el_progress: float = 10.0                   # EL subtotal ~10

    pts_opportunity_gap: float = 20.0              # Gap subtotal ~20

    pts_chronic_absenteeism: float = 7.5
    pts_climate_survey: float = 2.5                # Engagement subtotal ~10

    # ---- Star cut scores on the 0-100 index (lower bound, inclusive) ----
    # PLACEHOLDERS. Replace with official cut scores for your year.
    star_cuts: list[tuple[int, float]] = field(default_factory=lambda: [
        (5, 82.0),
        (4, 65.0),
        (3, 50.0),
        (2, 27.0),
        (1, 0.0),
    ])

    # ---- Per-indicator scoring rubrics (fraction of max points earned) ----
    # PLACEHOLDERS. Replace each with the official rubric.
    def scorers(self) -> dict[str, Callable[[float], float]]:
        return {
            "ela_proficiency":     linear_fraction(0, 100),
            "math_proficiency":    linear_fraction(0, 100),
            "science_proficiency": linear_fraction(0, 100),
            "ela_mgp":             linear_fraction(35, 65),   # MGP ~50 = median
            "math_mgp":            linear_fraction(35, 65),
            "ela_agp_pct":         linear_fraction(0, 100),
            "math_agp_pct":        linear_fraction(0, 100),
            "el_progress":         linear_fraction(0, 100),
            "opportunity_gap_index": linear_fraction(0, 100),
            # chronic absenteeism: lower is better, banded as an example
            "chronic_absenteeism": band_fraction(
                [(10, 1.0), (15, 0.75), (20, 0.5), (30, 0.25)],
                higher_is_better=False),
            "climate_survey":      linear_fraction(0, 100),
        }


# ============================================================
# 4. INDICATOR ASSEMBLY
# ============================================================

@dataclass
class Indicator:
    name: str
    component: str
    value: Optional[float]
    max_points: float
    scorer: Callable[[float], float]

    @property
    def applies(self) -> bool:
        return self.value is not None

    @property
    def earned(self) -> float:
        return 0.0 if not self.applies else self.max_points * self.scorer(self.value)


def build_indicators(inp: MiddleSchoolInputs, cfg: NSPFConfig) -> list[Indicator]:
    s = cfg.scorers()
    spec = [
        # name, component, value, max_points, scorer_key
        ("ela_proficiency",     "Academic Achievement", inp.ela_proficiency,    cfg.pts_ela_proficiency,     "ela_proficiency"),
        ("math_proficiency",    "Academic Achievement", inp.math_proficiency,   cfg.pts_math_proficiency,    "math_proficiency"),
        ("science_proficiency", "Academic Achievement", inp.science_proficiency,cfg.pts_science_proficiency, "science_proficiency"),
        ("ela_mgp",             "Growth",               inp.ela_mgp,            cfg.pts_ela_mgp,             "ela_mgp"),
        ("math_mgp",            "Growth",               inp.math_mgp,           cfg.pts_math_mgp,            "math_mgp"),
        ("ela_agp_pct",         "Growth",               inp.ela_agp_pct,        cfg.pts_ela_agp,             "ela_agp_pct"),
        ("math_agp_pct",        "Growth",               inp.math_agp_pct,       cfg.pts_math_agp,            "math_agp_pct"),
        ("el_progress",         "English Learner",      inp.el_progress,        cfg.pts_el_progress,         "el_progress"),
        ("opportunity_gap_index","Closing Opportunity Gaps", inp.opportunity_gap_index, cfg.pts_opportunity_gap, "opportunity_gap_index"),
        ("chronic_absenteeism", "Student Engagement",   inp.chronic_absenteeism,cfg.pts_chronic_absenteeism, "chronic_absenteeism"),
        ("climate_survey",      "Student Engagement",   inp.climate_survey,     cfg.pts_climate_survey,      "climate_survey"),
    ]
    return [Indicator(n, comp, val, mp, s[key]) for (n, comp, val, mp, key) in spec]


# ============================================================
# 5. TOTAL + STAR MAPPING + RESULT
# ============================================================

def index_to_stars(index: float, cfg: NSPFConfig) -> int:
    for stars, lower in sorted(cfg.star_cuts, key=lambda c: c[1], reverse=True):
        if index >= lower:
            return stars
    return 1


@dataclass
class Result:
    index: float
    stars: int
    earned: float
    possible: float
    by_component: dict[str, dict[str, float]]
    by_indicator: list[Indicator]
    points_to_next_star: Optional[float]
    next_star: Optional[int]


def compute(inp: MiddleSchoolInputs, cfg: Optional[NSPFConfig] = None) -> Result:
    cfg = cfg or NSPFConfig()
    indicators = build_indicators(inp, cfg)
    applied = [i for i in indicators if i.applies]

    earned = sum(i.earned for i in applied)
    possible = sum(i.max_points for i in applied)
    index = (earned / possible * 100.0) if possible else 0.0
    stars = index_to_stars(index, cfg)

    # component breakdown
    comp: dict[str, dict[str, float]] = {}
    for i in applied:
        c = comp.setdefault(i.component, {"earned": 0.0, "possible": 0.0})
        c["earned"] += i.earned
        c["possible"] += i.max_points

    # distance to next star (in index points)
    higher = sorted([(s, l) for s, l in cfg.star_cuts if s > stars], key=lambda c: c[1])
    next_star, pts_to_next = (None, None)
    if higher:
        next_star, lower = higher[0]
        pts_to_next = round(lower - index, 2)

    return Result(round(index, 2), stars, round(earned, 2), round(possible, 2),
                  comp, indicators, pts_to_next, next_star)


# ============================================================
# 6. DEMO  (run:  python nspf_middle_school.py)
# ============================================================

if __name__ == "__main__":
    sample = MiddleSchoolInputs(
        ela_proficiency=48,
        math_proficiency=35,
        science_proficiency=40,
        ela_mgp=52,
        math_mgp=47,
        ela_agp_pct=44,
        math_agp_pct=38,
        el_progress=55,
        opportunity_gap_index=46,
        chronic_absenteeism=18,   # lower is better
        climate_survey=70,
    )

    r = compute(sample)
    print("=" * 60)
    print("NSPF MIDDLE SCHOOL — ILLUSTRATIVE OUTPUT (placeholder config)")
    print("=" * 60)
    print(f"Index: {r.index} / 100   ->   {r.stars} star(s)")
    print(f"Points earned: {r.earned} of {r.possible} possible")
    if r.next_star:
        print(f"Distance to {r.next_star} stars: {r.points_to_next_star} index points")
    print("-" * 60)
    print("Component breakdown:")
    for name, c in r.by_component.items():
        pct = c["earned"] / c["possible"] * 100 if c["possible"] else 0
        print(f"  {name:<26} {c['earned']:5.1f} / {c['possible']:5.1f}  ({pct:4.0f}%)")
    print("-" * 60)
    print("Indicator detail (earned / max):")
    for i in r.by_indicator:
        status = f"{i.earned:5.2f} / {i.max_points:4.1f}" if i.applies else "  -- not applied --"
        print(f"  {i.name:<24} {status}")
