"""
Nevada School Performance Framework (NSPF) - Middle School Star-Rating Engine
=============================================================================
Faithful implementation of the 2024-25 NSPF Manual (version 8-15-2025),
NDE Office of Assessment, Data, and Accountability Management.

Measure labels here match the line items on an official NSPF school rating
report, so values read off a report map 1:1 onto this tool.

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
  CA Reduction PAT ........... Table 17  (see note below)
  Academic Learning Plans .... Table 18
  8th Grade Credits PAT ...... Table 19

CHRONIC ABSENTEEISM (Section 5.1.5): the engine implements all three paths a
school report shows -
  1. the rate PAT (Table 16),
  2. the +1 Incentive Point for a 10%+ reduction (Section 5.1.5.1), and
  3. the Reduction-rate PAT alternative (Table 17), taking whichever is higher.
The "reduction rate" is the percent decrease in the rate over the prior year,
confirmed by NSPF school rating reports (e.g. a school dropping 42.5% -> 28.5%
shows a 32.9% reduction earning 5 reduction-rate points). Paths 2 and 3 activate
only when a prior-year rate is supplied.

DELIBERATE OMISSIONS (require student-level data this tool does not take):
  - n-size sufficiency and multi-year pooling (Sections 1.2.1, 3.2)
  - CSI / TSI / ATSI school designations (Section 7)
  - Assessment participation warnings/penalties (Section 6)
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
    """Higher-is-better Point Attribution Table; bands in DESCENDING threshold order."""
    def scorer(value: float) -> float:
        v = truncate_tenth(value)
        for thr, pts in bands:
            if v >= thr:
                return pts
        return fallback
    return scorer


def pat_low(bands: list[tuple[float, float]], fallback: float) -> Callable[[float], float]:
    """Lower-is-better PAT (chronic absenteeism); bands in ASCENDING threshold order."""
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

PAT_CA_REDUCTION = pat_high(                                                 # Table 17 (max 5)
    [(25, 5), (22.5, 4.5), (20, 4), (17.5, 3.5), (15, 3), (12.5, 2.5),
     (10, 2), (7.5, 1.5), (5, 1), (2.5, 0.5)], fallback=0)

PAT_ALP = pat_high([(95, 2)], fallback=0)                                    # Table 18 (max 2; manual lists only >=95)

PAT_CREDIT8 = pat_high([(90, 3), (75, 2), (60, 1)], fallback=0)              # Table 19 (max 3)


def absenteeism_detail(current: float, prior: Optional[float]) -> tuple[float, str]:
    """Chronic absenteeism points and the path used (rate / incentive / reduction)."""
    base = PAT_ABSENTEEISM(current)
    if prior is None or prior <= 0:
        return base, "rate"
    rate_points = base
    incentive = truncate_tenth(current) <= prior * 0.9          # 10%+ reduction
    if incentive:
        rate_points = min(10.0, base + 1.0)                      # Incentive Point (5.1.5.1)
    reduction_rate = truncate_tenth((prior - current) / prior * 100.0)
    reduction_points = PAT_CA_REDUCTION(reduction_rate) if reduction_rate > 0 else 0.0
    if reduction_points > rate_points:                           # take the higher (Table 17)
        return reduction_points, f"reduction rate {reduction_rate}%"
    return rate_points, ("rate + incentive" if incentive else "rate")


# ------------------------------------------------------------------
# Star ratings - Table 2 (Middle School)
# ------------------------------------------------------------------

STAR_CUTS = [(5, 80.0), (4, 70.0), (3, 50.0), (2, 29.0), (1, 0.0)]

def index_to_stars(index: float) -> int:
    for stars, lower in STAR_CUTS:
        if index >= lower:
            return stars
    return 1


# Indicator weights (Table 10), names matching the school rating report
INDICATOR_WEIGHTS = {
    "Academic Achievement": 25,
    "Student Growth": 30,
    "English Language Proficiency": 10,
    "Closing Opportunity Gaps": 20,
    "Student Engagement": 15,
}
COMPONENT_ORDER = list(INDICATOR_WEIGHTS.keys())
REQUIRED_FOR_RATING = ["pooled_proficiency", "math_mgp", "ela_mgp", "math_agp_pct", "ela_agp_pct"]


# ------------------------------------------------------------------
# Inputs (field names mirror the report's measure lines)
# ------------------------------------------------------------------

@dataclass
class MiddleSchoolInputs:
    pooled_proficiency: Optional[float] = None      # "Pooled Proficiency"
    math_mgp: Optional[float] = None                # "Math MGP" (school median)
    ela_mgp: Optional[float] = None                 # "ELA MGP"
    math_agp_pct: Optional[float] = None            # "Met Math AGP Target"
    ela_agp_pct: Optional[float] = None             # "Met ELA AGP Target"
    wida_agp_pct: Optional[float] = None            # "Met EL AGP Target"
    math_gap_pct: Optional[float] = None            # "Prior Non-Proficient Met Math AGP Target"
    ela_gap_pct: Optional[float] = None             # "Prior Non-Proficient Met ELA AGP Target"
    chronic_absenteeism: Optional[float] = None     # "Chronic Absenteeism" (current year)
    prior_chronic_absenteeism: Optional[float] = None   # prior-year rate (enables incentive + reduction)
    alp_pct: Optional[float] = None                 # "Academic Learning Plans"
    credit8_pct: Optional[float] = None             # "8th Grade Credit Requirements"


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
    note: str = ""


def build_measures(inp: MiddleSchoolInputs) -> list[Measure]:
    spec = [
        ("pooled_proficiency", "Pooled Proficiency", "Academic Achievement", 25, inp.pooled_proficiency, PAT_POOLED),
        ("math_mgp", "Math MGP", "Student Growth", 10, inp.math_mgp, PAT_MGP),
        ("ela_mgp", "ELA MGP", "Student Growth", 10, inp.ela_mgp, PAT_MGP),
        ("math_agp_pct", "Met Math AGP Target", "Student Growth", 5, inp.math_agp_pct, PAT_AGP_MATH),
        ("ela_agp_pct", "Met ELA AGP Target", "Student Growth", 5, inp.ela_agp_pct, PAT_AGP_ELA),
        ("wida_agp_pct", "Met EL AGP Target", "English Language Proficiency", 10, inp.wida_agp_pct, PAT_WIDA),
        ("math_gap_pct", "Prior Non-Proficient Met Math AGP Target", "Closing Opportunity Gaps", 10, inp.math_gap_pct, PAT_GAP_MATH),
        ("ela_gap_pct", "Prior Non-Proficient Met ELA AGP Target", "Closing Opportunity Gaps", 10, inp.ela_gap_pct, PAT_GAP_ELA),
        ("alp_pct", "Academic Learning Plans", "Student Engagement", 2, inp.alp_pct, PAT_ALP),
        ("credit8_pct", "8th Grade Credit Requirements", "Student Engagement", 3, inp.credit8_pct, PAT_CREDIT8),
    ]
    measures = []
    for key, label, comp, maxp, val, scorer in spec:
        applies = val is not None
        measures.append(Measure(key, label, comp, maxp, val, scorer(val) if applies else 0.0, applies))

    ca_applies = inp.chronic_absenteeism is not None
    if ca_applies:
        ca_earned, ca_note = absenteeism_detail(inp.chronic_absenteeism, inp.prior_chronic_absenteeism)
    else:
        ca_earned, ca_note = 0.0, ""
    measures.append(Measure("chronic_absenteeism", "Chronic Absenteeism", "Student Engagement",
                            10, inp.chronic_absenteeism, ca_earned, ca_applies, ca_note))
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
# Built-in validation: Carroll M Johnston STEM Academy (Clark, 2024-25)
# Official report: AA 6, Growth 16.5, EL 10, Gaps 10, Engagement 9 -> 51.5, 3 stars.
# ------------------------------------------------------------------

if __name__ == "__main__":
    carroll = MiddleSchoolInputs(
        pooled_proficiency=26.2,
        math_mgp=56, ela_mgp=51,
        math_agp_pct=21, ela_agp_pct=39.9,
        wida_agp_pct=37.5,
        math_gap_pct=11.7, ela_gap_pct=26.6,
        chronic_absenteeism=28.5, prior_chronic_absenteeism=42.5,
        alp_pct=95,            # report shows ">95"
        credit8_pct=81.8,
    )
    r = compute(carroll)
    expected = {"Academic Achievement": 6.0, "Student Growth": 16.5,
                "English Language Proficiency": 10.0, "Closing Opportunity Gaps": 10.0,
                "Student Engagement": 9.0}
    print("VALIDATION - Carroll M Johnston STEM Academy (official: 51.5 / 3 stars)")
    print(f"  Computed index: {r.index}  stars: {r.stars}  rated: {r.rated}")
    ok = abs(r.index - 51.5) < 1e-9 and r.stars == 3
    for comp in COMPONENT_ORDER:
        got = round(r.by_component[comp]["earned"], 1)
        want = expected[comp]
        flag = "OK " if abs(got - want) < 1e-9 else "FAIL"
        if abs(got - want) >= 1e-9:
            ok = False
        print(f"  {flag} {comp:<30} {got} / {r.by_component[comp]['possible']}  (official {want})")
    ca = next(m for m in r.measures if m.key == "chronic_absenteeism")
    print(f"  Chronic absenteeism path: {ca.note}  ->  {ca.earned} pts")
    print("RESULT:", "ALL MATCH OFFICIAL REPORT" if ok else "MISMATCH")
