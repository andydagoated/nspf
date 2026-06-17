"""
Nevada School Performance Framework (NSPF) - Middle School Star-Rating Engine
=============================================================================
Faithful implementation of the 2024-25 NSPF Manual (version 8-15-2025),
NDE Office of Assessment, Data, and Accountability Management.

Authoritative sources within the manual:
  Star cut scores ............ Table 2   (Section 1.2.2)
  Index formula .............. Section 1.2.2  (points earned / points possible x 100)
  Truncation rule ............ Section 1.3   (rates truncated, not rounded, to the tenth)
  Measure weights ............ Table 10  (Section 5.2)
  Pooled Proficiency PAT ..... Table 11
  Math/ELA MGP PAT ........... Table 12
  Math/ELA AGP PAT ........... Table 13
  WIDA AGP PAT ............... Table 14
  Closing Opportunity Gaps ... Table 15
  Chronic Absenteeism PAT .... Table 16
  Academic Learning Plans .... Table 18
  8th Grade Credits PAT ...... Table 19

DELIBERATE OMISSIONS (require student-level data this tool does not take; documented
so the fidelity claim stays honest):
  - n-size sufficiency and multi-year pooling (Sections 1.2.1, 3.2)
  - CSI / TSI / ATSI school designations (Section 7)
  - Assessment participation warnings/penalties (Section 6)
  - Chronic Absenteeism Reduction PAT (Table 17): the manual text does not give an
    explicit "reduction rate" formula, so it is omitted pending NDE confirmation.
    The Chronic Absenteeism Incentive Point (Section 5.1.5.1) IS implemented and
    activates only when a prior-year rate is supplied.
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Callable, Optional


# ------------------------------------------------------------------
# Scoring primitives
# ------------------------------------------------------------------

def truncate_tenth(x: float) -> float:
    """Truncate (not round) to the tenth, per Section 1.3.  59.99 -> 59.9."""
    return math.floor(x * 10) / 10.0


def pat_high(bands: list[tuple[float, float]], fallback: float) -> Callable[[float], float]:
    """Higher-is-better Point Attribution Table.
    `bands` = (threshold, points) in DESCENDING threshold order. The (truncated)
    value earns the points of the first threshold it meets or exceeds; if it meets
    none, it earns `fallback` (the table's bottom band)."""
    def scorer(value: float) -> float:
        v = truncate_tenth(value)
        for thr, pts in bands:
            if v >= thr:
                return pts
        return fallback
    return scorer


def pat_low(bands: list[tuple[float, float]], fallback: float) -> Callable[[float], float]:
    """Lower-is-better PAT (chronic absenteeism).
    `bands` = (threshold, points) in ASCENDING threshold order. The value earns the
    points of the first threshold it falls below; if it falls below none, `fallback`."""
    def scorer(value: float) -> float:
        v = truncate_tenth(value)
        for thr, pts in bands:
            if v < thr:
                return pts
        return fallback
    return scorer


# ------------------------------------------------------------------
# Point Attribution Tables - 2024-25 Middle School (verbatim from the manual)
# ------------------------------------------------------------------

PAT_POOLED = pat_high(                                                       # Table 11 (max 25)
    [(56, 25), (55, 24), (54, 23), (52, 22), (50, 21), (48, 20), (46, 19),
     (44, 18), (42, 17), (41, 16), (40, 15), (39, 14), (37, 13), (36, 12),
     (34, 11), (32, 10), (30, 9), (28, 8), (27, 7), (26, 6), (25, 5),
     (24, 4), (23, 3), (22, 2)], fallback=1)

PAT_MGP = pat_high(                                                          # Table 12 (max 10; Math & ELA identical)
    [(65, 10), (61, 9), (58, 8), (54, 7), (51, 6), (48, 5), (44, 4),
     (40, 3), (35, 2)], fallback=1)

PAT_AGP_MATH = pat_high(                                                     # Table 13 Math (max 5)
    [(42, 5), (39, 4.5), (35, 4), (31, 3.5), (27, 3), (24, 2.5), (21, 2),
     (18, 1.5), (15, 1)], fallback=0.5)

PAT_AGP_ELA = pat_high(                                                      # Table 13 ELA (max 5)
    [(61, 5), (58, 4.5), (55, 4), (51, 3.5), (48, 3), (45, 2.5), (41, 2),
     (37, 1.5), (32, 1)], fallback=0.5)

PAT_WIDA = pat_high(                                                         # Table 14 (max 10)
    [(36, 10), (32, 9), (29, 8), (26, 7), (23, 6), (20, 5), (18, 4),
     (16, 3), (13, 2)], fallback=1)

PAT_GAP_MATH = pat_high(                                                     # Table 15 Math (max 10)
    [(24, 10), (21, 9), (19, 8), (17, 7), (15, 6), (13, 5), (11, 4),
     (10, 3), (8, 2)], fallback=1)

PAT_GAP_ELA = pat_high(                                                      # Table 15 ELA (max 10)
    [(34, 10), (32, 9), (30, 8), (28, 7), (26, 6), (24, 5), (22, 4),
     (19, 3), (16, 2)], fallback=1)

CA_BANDS = [(5, 10), (6, 9.5), (7, 9), (8, 8.5), (9, 8), (10, 7.5), (11, 7),  # Table 16 (max 10)
            (12, 6.5), (13, 6), (14, 5.5), (15, 5), (16, 4.5), (17, 4),
            (18, 3.5), (19, 3), (20, 2.5), (21, 2), (22, 1.5), (23, 1), (24, 0.5)]
PAT_ABSENTEEISM = pat_low(CA_BANDS, fallback=0)

PAT_ALP = pat_high([(95, 2)], fallback=0)                                    # Table 18 (max 2; manual lists only >=95)

PAT_CREDIT8 = pat_high([(90, 3), (75, 2), (60, 1)], fallback=0)              # Table 19 (max 3)


def score_absenteeism(current: float, prior: Optional[float]) -> float:
    """Chronic Absenteeism points (Table 16) plus the Incentive Point (5.1.5.1).
    The incentive adds 1 point (capped at the 10-point max) when the current rate
    is a 10%+ reduction over the prior year (current <= prior * 0.9). It only
    applies when a prior-year rate is supplied."""
    base = PAT_ABSENTEEISM(current)
    if prior is not None and prior > 0 and truncate_tenth(current) <= prior * 0.9:
        return min(10.0, base + 1.0)
    return base


# ------------------------------------------------------------------
# Star ratings - Table 2 (Middle School)
# ------------------------------------------------------------------

STAR_CUTS = [(5, 80.0), (4, 70.0), (3, 50.0), (2, 29.0), (1, 0.0)]

def index_to_stars(index: float) -> int:
    for stars, lower in STAR_CUTS:
        if index >= lower:
            return stars
    return 1


# Indicator weights (Table 10) - for reference/display
INDICATOR_WEIGHTS = {
    "Academic Achievement": 25,
    "Growth": 30,
    "English Learner Progress": 10,
    "Closing Opportunity Gaps": 20,
    "Student Engagement": 15,
}
COMPONENT_ORDER = list(INDICATOR_WEIGHTS.keys())

# Measures required for an all-students rating (Section 1.2; else "Not Rated")
REQUIRED_FOR_RATING = ["pooled_proficiency", "math_mgp", "ela_mgp", "math_agp_pct", "ela_agp_pct"]


# ------------------------------------------------------------------
# Inputs
# ------------------------------------------------------------------

@dataclass
class MiddleSchoolInputs:
    pooled_proficiency: Optional[float] = None      # combined Math+ELA+Science proficiency %
    math_mgp: Optional[float] = None                # median growth percentile (1-99)
    ela_mgp: Optional[float] = None
    math_agp_pct: Optional[float] = None            # % meeting adequate growth
    ela_agp_pct: Optional[float] = None
    wida_agp_pct: Optional[float] = None            # % of ELs meeting WIDA AGP
    math_gap_pct: Optional[float] = None            # Closing Opportunity Gaps, Math
    ela_gap_pct: Optional[float] = None             # Closing Opportunity Gaps, ELA
    chronic_absenteeism: Optional[float] = None     # % chronically absent (lower is better)
    prior_chronic_absenteeism: Optional[float] = None   # optional: enables incentive point
    alp_pct: Optional[float] = None                 # % of MS students with an Academic Learning Plan
    credit8_pct: Optional[float] = None             # % of 8th graders meeting NAC 389 credits


# ------------------------------------------------------------------
# Measures and computation
# ------------------------------------------------------------------

@dataclass
class Measure:
    key: str
    label: str
    component: str
    max_points: float
    value: Optional[float]
    earned: float
    applies: bool


def build_measures(inp: MiddleSchoolInputs) -> list[Measure]:
    spec = [
        # key, label, component, max, value, scorer
        ("pooled_proficiency", "Pooled proficiency", "Academic Achievement", 25, inp.pooled_proficiency, PAT_POOLED),
        ("math_mgp", "Math MGP", "Growth", 10, inp.math_mgp, PAT_MGP),
        ("ela_mgp", "ELA MGP", "Growth", 10, inp.ela_mgp, PAT_MGP),
        ("math_agp_pct", "Math AGP", "Growth", 5, inp.math_agp_pct, PAT_AGP_MATH),
        ("ela_agp_pct", "ELA AGP", "Growth", 5, inp.ela_agp_pct, PAT_AGP_ELA),
        ("wida_agp_pct", "WIDA AGP", "English Learner Progress", 10, inp.wida_agp_pct, PAT_WIDA),
        ("math_gap_pct", "Math closing gaps", "Closing Opportunity Gaps", 10, inp.math_gap_pct, PAT_GAP_MATH),
        ("ela_gap_pct", "ELA closing gaps", "Closing Opportunity Gaps", 10, inp.ela_gap_pct, PAT_GAP_ELA),
        ("alp_pct", "Academic Learning Plans", "Student Engagement", 2, inp.alp_pct, PAT_ALP),
        ("credit8_pct", "8th-grade credits", "Student Engagement", 3, inp.credit8_pct, PAT_CREDIT8),
    ]
    measures = []
    for key, label, comp, maxp, val, scorer in spec:
        applies = val is not None
        measures.append(Measure(key, label, comp, maxp, val, scorer(val) if applies else 0.0, applies))

    # Chronic Absenteeism handled separately (optional incentive point)
    ca_applies = inp.chronic_absenteeism is not None
    ca_earned = score_absenteeism(inp.chronic_absenteeism, inp.prior_chronic_absenteeism) if ca_applies else 0.0
    measures.append(Measure("chronic_absenteeism", "Chronic absenteeism", "Student Engagement",
                            10, inp.chronic_absenteeism, ca_earned, ca_applies))
    return measures


@dataclass
class Result:
    index: float
    stars: int
    rated: bool
    missing_required: list[str]
    earned: float
    possible: float
    by_component: dict[str, dict[str, float]]
    measures: list[Measure]
    next_star: Optional[int]
    points_to_next: Optional[float]


def compute(inp: MiddleSchoolInputs) -> Result:
    measures = build_measures(inp)
    applied = [m for m in measures if m.applies]

    earned = sum(m.earned for m in applied)
    possible = sum(m.max_points for m in applied)
    index = round(earned / possible * 100.0, 1) if possible else 0.0
    stars = index_to_stars(index)

    present = {m.key for m in applied}
    missing_required = [k for k in REQUIRED_FOR_RATING if k not in present]
    rated = len(missing_required) == 0

    comp: dict[str, dict[str, float]] = {}
    for m in applied:
        c = comp.setdefault(m.component, {"earned": 0.0, "possible": 0.0})
        c["earned"] += m.earned
        c["possible"] += m.max_points

    higher = [(s, l) for s, l in STAR_CUTS if s > stars]
    next_star, pts_to_next = (None, None)
    if higher:
        next_star, lower = min(higher, key=lambda x: x[1])
        pts_to_next = round(lower - index, 1)

    return Result(index, stars, rated, missing_required, round(earned, 1), round(possible, 1),
                  comp, measures, next_star, pts_to_next)


# ------------------------------------------------------------------
# Demo / self-check
# ------------------------------------------------------------------

if __name__ == "__main__":
    sample = MiddleSchoolInputs(
        pooled_proficiency=38,
        math_mgp=47, ela_mgp=52,
        math_agp_pct=38, ela_agp_pct=44,
        wida_agp_pct=30,
        math_gap_pct=16, ela_gap_pct=24,
        chronic_absenteeism=18,
        alp_pct=96,
        credit8_pct=80,
    )
    r = compute(sample)
    print("=" * 60)
    print("NSPF MIDDLE SCHOOL - 2024-25 framework (manual v8-15-2025)")
    print("=" * 60)
    print(f"Index: {r.index} / 100   ->   {r.stars} star(s)"
          f"{'' if r.rated else '   [NOT RATED - missing required measures]'}")
    print(f"Points earned: {r.earned} of {r.possible} possible")
    if r.next_star:
        print(f"Index points to {r.next_star} stars: {r.points_to_next}")
    print("-" * 60)
    for comp in COMPONENT_ORDER:
        if comp in r.by_component:
            c = r.by_component[comp]
            print(f"  {comp:<26} {c['earned']:5.1f} / {c['possible']:5.1f}")
    print("-" * 60)
    for m in r.measures:
        detail = f"{m.earned:5.1f} / {m.max_points:4.1f}  (rate {m.value})" if m.applies else "  not reported"
        print(f"  {m.label:<24} {detail}")
