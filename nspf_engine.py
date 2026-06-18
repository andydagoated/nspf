"""
Nevada School Performance Framework (NSPF) - Star-Rating Engine
===============================================================
Faithful implementation of the 2024-25 NSPF Manual (version 8-15-2025) for all
three school levels: Elementary (ES), Middle (MS), and High (HS).

Measure labels match the line items on official NSPF school rating reports.

Manual sources:
  Star cut scores ........ Tables 1 (ES), 2 (MS), 3 (HS)   [Section 1.2.2]
  Index formula .......... Section 1.2.2  (points earned / points possible x 100)
  Truncation ............. Section 1.3    (rates truncated, not rounded, to the tenth)
  ES weights/PATs ........ Tables 1-9   (Section 5.1)
  MS weights/PATs ........ Tables 10-19 (Section 5.2)
  HS weights/PATs ........ Tables 20-32 (Section 5.3)

Chronic absenteeism is scored on its rate table, plus (when a prior-year rate is
supplied) the incentive point and the reduction-rate alternative, taking whichever
is higher - matching school rating reports. The reduction rate is the percent
decrease over the prior year. Incentive and reduction tables differ by level.

DELIBERATE OMISSIONS (need student-level data this tool does not take): n-size
sufficiency and multi-year pooling (1.2.1, 3.2), CSI/TSI/ATSI designations (7),
and assessment participation penalties (6).
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Callable, Optional


def truncate_tenth(x: float) -> float:
    """Truncate (not round) to the tenth, per Section 1.3."""
    return math.floor(x * 10) / 10.0


def pat_high(bands, fallback):
    """Higher-is-better PAT; bands = (threshold, points) DESCENDING."""
    def scorer(value: float) -> float:
        v = truncate_tenth(value)
        for thr, pts in bands:
            if v >= thr:
                return pts
        return fallback
    return scorer


def pat_low(bands, fallback):
    """Lower-is-better PAT (chronic absenteeism); bands ASCENDING (value < thr -> pts)."""
    def scorer(value: float) -> float:
        v = truncate_tenth(value)
        for thr, pts in bands:
            if v < thr:
                return pts
        return fallback
    return scorer


# ==================================================================
# POINT ATTRIBUTION TABLES
# ==================================================================

# --- Shared ---
PAT_MGP = pat_high([(65, 10), (61, 9), (58, 8), (54, 7), (51, 6), (48, 5),       # Tables 4 & 12
                    (44, 4), (40, 3), (35, 2)], 1)
CA_RATE_10 = pat_low([(5, 10), (6, 9.5), (7, 9), (8, 8.5), (9, 8), (10, 7.5),     # Tables 8 & 16
                      (11, 7), (12, 6.5), (13, 6), (14, 5.5), (15, 5), (16, 4.5),
                      (17, 4), (18, 3.5), (19, 3), (20, 2.5), (21, 2), (22, 1.5),
                      (23, 1), (24, 0.5)], 0)

# --- Elementary (Tables 2-9) ---
PAT_ES_POOLED = pat_high([(60, 20), (58, 19), (56, 18), (55, 17), (54, 16), (53, 15),
                          (52, 14), (50, 13), (49, 12), (48, 11), (46, 10), (44, 9),
                          (42, 8), (40, 7), (38, 6), (35, 5), (33, 4), (30, 3), (26, 2)], 1)
PAT_ES_RBG3 = pat_high([(63, 5), (51, 4), (38, 3), (25, 2)], 1)
PAT_ES_AGP_MATH = pat_high([(52, 7.5), (50, 7), (47, 6.5), (44, 6), (41, 5.5), (39, 5),
                            (37, 4.5), (35, 4), (33, 3.5), (31, 3), (29, 2.5), (27, 2),
                            (25, 1.5), (23, 1)], 0.5)
PAT_ES_AGP_ELA = pat_high([(63, 7.5), (61, 7), (59, 6.5), (57, 6), (55, 5.5), (53, 5),
                           (51, 4.5), (49, 4), (47, 3.5), (45, 3), (43, 2.5), (41, 2),
                           (38, 1.5), (35, 1)], 0.5)
PAT_ES_WIDA = pat_high([(57, 10), (54, 9), (51, 8), (48, 7), (45, 6), (42, 5),
                        (39, 4), (36, 3), (33, 2)], 1)
PAT_ES_GAP_MATH = pat_high([(42, 10), (39, 9), (36, 8), (33, 7), (30, 6), (27, 5),
                            (24, 4), (20, 3), (16, 2)], 1)
PAT_ES_GAP_ELA = pat_high([(52, 10), (49, 9), (46, 8), (43, 7), (40, 6), (37, 5),
                           (34, 4), (31, 3), (27, 2)], 1)
PAT_ES_CA_REDUCTION = pat_high([(30, 5), (27, 4.5), (24, 4), (21, 3.5), (18, 3), (15, 2.5),
                                (12, 2), (9, 1.5), (6, 1), (3, 0.5)], 0)

# --- Middle (Tables 10-19) ---
PAT_MS_POOLED = pat_high([(56, 25), (55, 24), (54, 23), (52, 22), (50, 21), (48, 20), (46, 19),
                          (44, 18), (42, 17), (41, 16), (40, 15), (39, 14), (37, 13), (36, 12),
                          (34, 11), (32, 10), (30, 9), (28, 8), (27, 7), (26, 6), (25, 5),
                          (24, 4), (23, 3), (22, 2)], 1)
PAT_MS_AGP_MATH = pat_high([(42, 5), (39, 4.5), (35, 4), (31, 3.5), (27, 3), (24, 2.5),
                            (21, 2), (18, 1.5), (15, 1)], 0.5)
PAT_MS_AGP_ELA = pat_high([(61, 5), (58, 4.5), (55, 4), (51, 3.5), (48, 3), (45, 2.5),
                           (41, 2), (37, 1.5), (32, 1)], 0.5)
PAT_MS_WIDA = pat_high([(36, 10), (32, 9), (29, 8), (26, 7), (23, 6), (20, 5), (18, 4),
                        (16, 3), (13, 2)], 1)
PAT_MS_GAP_MATH = pat_high([(24, 10), (21, 9), (19, 8), (17, 7), (15, 6), (13, 5),
                            (11, 4), (10, 3), (8, 2)], 1)
PAT_MS_GAP_ELA = pat_high([(34, 10), (32, 9), (30, 8), (28, 7), (26, 6), (24, 5),
                           (22, 4), (19, 3), (16, 2)], 1)
PAT_MS_CA_REDUCTION = pat_high([(25, 5), (22.5, 4.5), (20, 4), (17.5, 3.5), (15, 3),
                                (12.5, 2.5), (10, 2), (7.5, 1.5), (5, 1), (2.5, 0.5)], 0)
PAT_ALP = pat_high([(95, 2)], 0)
PAT_CREDIT8 = pat_high([(90, 3), (75, 2), (60, 1)], 0)

# --- High (Tables 20-32) ---
PAT_HS_MATH = pat_high([(42.4, 10), (41.1, 9.5), (39.7, 9), (38.4, 8.5), (37, 8), (35.7, 7.5),
                        (34.3, 7), (33, 6.5), (31.6, 6), (30.3, 5.5), (28.3, 5), (25.3, 4.5),
                        (22.4, 4), (19.4, 3.5), (16.5, 3), (13.5, 2.5), (10.6, 2), (7.6, 1.5),
                        (4.7, 1)], 0.5)
PAT_HS_ELA = pat_high([(55.9, 10), (54.9, 9.5), (53.9, 9), (52.9, 8.5), (51.9, 8), (50.9, 7.5),
                       (49.8, 7), (48.8, 6.5), (47.8, 6), (46.8, 5.5), (44.8, 5), (41.1, 4.5),
                       (37.3, 4), (33.5, 3.5), (29.8, 3), (26, 2.5), (22.2, 2), (18.4, 1.5),
                       (14.7, 1)], 0.5)
PAT_HS_SCIENCE = pat_high([(54.3, 5), (49, 4.5), (43.7, 4), (38.4, 3.5), (33.1, 3),
                           (29.3, 2.5), (25.5, 2), (21.7, 1.5), (17.9, 1)], 0.5)
PAT_HS_ACGR4 = pat_high([(89.4, 25), (88.7, 24), (87.9, 23), (87.2, 22), (86.4, 21), (85.7, 20),
                         (84.9, 19), (84.2, 18), (83.4, 17), (82.7, 16), (81.9, 15), (81.2, 14),
                         (80.4, 13), (79.3, 12), (78.2, 11), (77.1, 10), (75.9, 9), (74.8, 8),
                         (73.7, 7), (72.6, 6), (71.5, 5), (70.4, 4), (69.3, 3), (68.1, 2),
                         (67, 1)], 0)
PAT_HS_ACGR5 = pat_high([(91.4, 5), (85.3, 4), (79.2, 3), (73.1, 2), (67, 1)], 0)
PAT_HS_WIDA = pat_high([(20, 10), (18, 9), (15, 8), (12, 7), (10, 6), (8, 5), (7, 4),
                        (6, 3), (5, 2)], 1)
PAT_HS_CCR_PART = pat_high([(74.5, 10), (73, 9.5), (71.4, 9), (69.9, 8.5), (68.3, 8), (66.8, 7.5),
                            (65.2, 7), (63.7, 6.5), (62.1, 6), (60.6, 5.5), (59, 5), (57.5, 4.5),
                            (55.9, 4), (54.4, 3.5), (52.8, 3), (51.3, 2.5), (49.7, 2), (48.2, 1.5),
                            (46.6, 1)], 0.5)
PAT_HS_CCR_COMP = pat_high([(55.8, 10), (53, 9.5), (50.1, 9), (47.3, 8.5), (44.4, 8), (41.6, 7.5),
                            (38.7, 7), (35.9, 6.5), (33, 6), (30.2, 5.5), (27.3, 5), (24.5, 4.5),
                            (21.6, 4), (18.8, 3.5), (15.9, 3), (13.1, 2.5), (10.2, 2), (7.3, 1.5),
                            (4.5, 1)], 0.5)
PAT_HS_ADV_DIPLOMA = pat_high([(53.3, 5), (39.4, 4), (25.5, 3), (11.5, 2)], 1)
PAT_HS_CA_RATE = pat_low([(5, 5), (7, 4.5), (9, 4), (11, 3.5), (13, 3), (15, 2.5),
                          (17, 2), (19, 1.5), (21, 1), (23, 0.5)], 0)
PAT_HS_CA_REDUCTION = pat_high([(20, 2.5), (15.5, 2), (11, 1.5), (6.5, 1), (2, 0.5)], 0)
PAT_HS_CREDIT9 = pat_high([(99.7, 5), (92.4, 4), (85.1, 3), (77.8, 2)], 1)


def ca_detail(current, prior, rate_pat, reduction_pat, incentive, max_pts):
    """Chronic absenteeism points and the path used."""
    base = rate_pat(current)
    if prior is None or prior <= 0:
        return base, "rate"
    rate_points = base
    inc = truncate_tenth(current) <= prior * 0.9
    if inc:
        rate_points = min(max_pts, base + incentive)
    red = truncate_tenth((prior - current) / prior * 100.0)
    red_points = reduction_pat(red) if red > 0 else 0.0
    if red_points > rate_points:
        return red_points, f"reduction rate {red}%"
    return rate_points, ("rate + incentive" if inc else "rate")


# ==================================================================
# Level specifications
# ==================================================================

@dataclass
class MeasureDef:
    key: str
    label: str
    component: str
    max_points: float
    scorer: Callable[[float], float]
    default: float = 0.0
    vmin: float = 0.0
    vmax: float = 100.0
    step: float = 0.1
    help: str = ""
    is_ca: bool = False
    reduction_pat: Optional[Callable] = None
    incentive: float = 0.0


@dataclass
class LevelSpec:
    name: str
    star_cuts: list                       # [(stars, lower_bound)] descending
    measures: list                        # list[MeasureDef] in display order
    required_for_rating: list
    component_order: list
    ca_default_prior: float = 0.0

    @property
    def indicator_weights(self):
        w = {}
        for m in self.measures:
            w[m.component] = w.get(m.component, 0) + m.max_points
        return {c: w[c] for c in self.component_order}


def _ca(label, max_pts, rate_pat, reduction_pat, incentive, default):
    return MeasureDef("chronic_absenteeism", label, "Student Engagement", max_pts, rate_pat,
                      default=default, vmin=0, vmax=100, step=0.1, is_ca=True,
                      reduction_pat=reduction_pat, incentive=incentive,
                      help="Lower is better.")


ELEMENTARY = LevelSpec(
    name="Elementary",
    star_cuts=[(5, 84.0), (4, 67.0), (3, 50.0), (2, 27.0), (1, 0.0)],     # Table 1
    component_order=["Academic Achievement", "Student Growth", "English Language Proficiency",
                     "Closing Opportunity Gaps", "Student Engagement"],
    required_for_rating=["pooled_proficiency", "math_mgp", "ela_mgp", "math_agp", "ela_agp"],
    ca_default_prior=13.0,
    measures=[
        MeasureDef("pooled_proficiency", "Pooled Proficiency", "Academic Achievement", 20, PAT_ES_POOLED, default=45),
        MeasureDef("rbg3", "Read by Grade 3", "Academic Achievement", 5, PAT_ES_RBG3, default=50),
        MeasureDef("math_mgp", "Math MGP", "Student Growth", 10, PAT_MGP, default=50, vmin=1, vmax=99, step=1.0),
        MeasureDef("ela_mgp", "ELA MGP", "Student Growth", 10, PAT_MGP, default=50, vmin=1, vmax=99, step=1.0),
        MeasureDef("math_agp", "Met Math AGP Target", "Student Growth", 7.5, PAT_ES_AGP_MATH, default=40),
        MeasureDef("ela_agp", "Met ELA AGP Target", "Student Growth", 7.5, PAT_ES_AGP_ELA, default=50),
        MeasureDef("wida", "Met EL AGP Target", "English Language Proficiency", 10, PAT_ES_WIDA, default=45,
                   help="Uncheck Reported if too few ELs to report."),
        MeasureDef("math_gap", "Prior Non-Proficient Met Math AGP Target", "Closing Opportunity Gaps", 10, PAT_ES_GAP_MATH, default=30),
        MeasureDef("ela_gap", "Prior Non-Proficient Met ELA AGP Target", "Closing Opportunity Gaps", 10, PAT_ES_GAP_ELA, default=40),
        _ca("Chronic Absenteeism", 10, CA_RATE_10, PAT_ES_CA_REDUCTION, 1.0, default=12),
    ],
)

MIDDLE = LevelSpec(
    name="Middle",
    star_cuts=[(5, 80.0), (4, 70.0), (3, 50.0), (2, 29.0), (1, 0.0)],     # Table 2
    component_order=["Academic Achievement", "Student Growth", "English Language Proficiency",
                     "Closing Opportunity Gaps", "Student Engagement"],
    required_for_rating=["pooled_proficiency", "math_mgp", "ela_mgp", "math_agp", "ela_agp"],
    ca_default_prior=42.5,
    measures=[
        MeasureDef("pooled_proficiency", "Pooled Proficiency", "Academic Achievement", 25, PAT_MS_POOLED, default=26.2),
        MeasureDef("math_mgp", "Math MGP", "Student Growth", 10, PAT_MGP, default=56, vmin=1, vmax=99, step=1.0),
        MeasureDef("ela_mgp", "ELA MGP", "Student Growth", 10, PAT_MGP, default=51, vmin=1, vmax=99, step=1.0),
        MeasureDef("math_agp", "Met Math AGP Target", "Student Growth", 5, PAT_MS_AGP_MATH, default=21),
        MeasureDef("ela_agp", "Met ELA AGP Target", "Student Growth", 5, PAT_MS_AGP_ELA, default=39.9),
        MeasureDef("wida", "Met EL AGP Target", "English Language Proficiency", 10, PAT_MS_WIDA, default=37.5,
                   help="Uncheck Reported if too few ELs to report."),
        MeasureDef("math_gap", "Prior Non-Proficient Met Math AGP Target", "Closing Opportunity Gaps", 10, PAT_MS_GAP_MATH, default=11.7),
        MeasureDef("ela_gap", "Prior Non-Proficient Met ELA AGP Target", "Closing Opportunity Gaps", 10, PAT_MS_GAP_ELA, default=26.6),
        _ca("Chronic Absenteeism", 10, CA_RATE_10, PAT_MS_CA_REDUCTION, 1.0, default=28.5),
        MeasureDef("alp", "Academic Learning Plans", "Student Engagement", 2, PAT_ALP, default=95,
                   help="Reports often show '>95' - enter 95 (>=95 earns full points)."),
        MeasureDef("credit8", "8th Grade Credit Requirements", "Student Engagement", 3, PAT_CREDIT8, default=81.8),
    ],
)

HIGH = LevelSpec(
    name="High",
    star_cuts=[(5, 82.0), (4, 70.0), (3, 50.0), (2, 27.0), (1, 0.0)],     # Table 3
    component_order=["Academic Achievement", "Graduation Rates", "English Language Proficiency",
                     "College and Career Readiness", "Student Engagement"],
    required_for_rating=["math_prof", "ela_prof", "acgr4"],
    ca_default_prior=16.0,
    measures=[
        MeasureDef("math_prof", "Math Proficiency", "Academic Achievement", 10, PAT_HS_MATH, default=30),
        MeasureDef("ela_prof", "ELA Proficiency", "Academic Achievement", 10, PAT_HS_ELA, default=45),
        MeasureDef("science_prof", "Science Proficiency", "Academic Achievement", 5, PAT_HS_SCIENCE, default=35),
        MeasureDef("acgr4", "4-Year ACGR", "Graduation Rates", 25, PAT_HS_ACGR4, default=82),
        MeasureDef("acgr5", "5-Year ACGR", "Graduation Rates", 5, PAT_HS_ACGR5, default=85),
        MeasureDef("wida", "Met EL AGP Target", "English Language Proficiency", 10, PAT_HS_WIDA, default=12,
                   help="Uncheck Reported if too few ELs to report."),
        MeasureDef("ccr_participation", "Post-Secondary Preparation Participation", "College and Career Readiness", 10, PAT_HS_CCR_PART, default=60),
        MeasureDef("ccr_completion", "Post-Secondary Preparation Completion", "College and Career Readiness", 10, PAT_HS_CCR_COMP, default=35),
        MeasureDef("advanced_diploma", "Advanced/CCR Diploma", "College and Career Readiness", 5, PAT_HS_ADV_DIPLOMA, default=30),
        _ca("Chronic Absenteeism", 5, PAT_HS_CA_RATE, PAT_HS_CA_REDUCTION, 0.5, default=14),
        MeasureDef("credit9", "9th Grade Credit Sufficiency", "Student Engagement", 5, PAT_HS_CREDIT9, default=90),
    ],
)

LEVELS = {"Elementary": ELEMENTARY, "Middle": MIDDLE, "High": HIGH}


# ==================================================================
# Computation
# ==================================================================

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


@dataclass
class Result:
    level: str
    index: float
    stars: int
    rated: bool
    missing_required: list
    earned: float
    possible: float
    by_component: dict
    measures: list
    next_star: Optional[int]
    points_to_next: Optional[float]


def stars_from(index, star_cuts):
    for stars, lower in star_cuts:
        if index >= lower:
            return stars
    return 1


def compute(level_key: str, values: dict, prior_ca: Optional[float] = None) -> Result:
    spec = LEVELS[level_key]
    measures = []
    for md in spec.measures:
        val = values.get(md.key)
        applies = val is not None
        note = ""
        if not applies:
            earned = 0.0
        elif md.is_ca:
            earned, note = ca_detail(val, prior_ca, md.scorer, md.reduction_pat, md.incentive, md.max_points)
        else:
            earned = md.scorer(val)
        measures.append(Measure(md.key, md.label, md.component, md.max_points, val, earned, applies, note))

    applied = [m for m in measures if m.applies]
    earned = sum(m.earned for m in applied)
    possible = sum(m.max_points for m in applied)
    index = round(earned / possible * 100.0, 1) if possible else 0.0
    stars = stars_from(index, spec.star_cuts)

    present = {m.key for m in applied}
    missing = [k for k in spec.required_for_rating if k not in present]
    rated = not missing

    comp = {}
    for m in applied:
        c = comp.setdefault(m.component, {"earned": 0.0, "possible": 0.0})
        c["earned"] += m.earned
        c["possible"] += m.max_points

    higher = [(s, l) for s, l in spec.star_cuts if s > stars]
    next_star, pts_to_next = (None, None)
    if higher:
        next_star, lower = min(higher, key=lambda x: x[1])
        pts_to_next = round(lower - index, 1)

    return Result(level_key, index, stars, rated, missing, round(earned, 1), round(possible, 1),
                  comp, measures, next_star, pts_to_next)


# ==================================================================
# Self-tests
# ==================================================================

if __name__ == "__main__":
    ok = True

    # Weights sum to 100 at every level
    for k, spec in LEVELS.items():
        total = sum(m.max_points for m in spec.measures)
        flag = "OK " if abs(total - 100) < 1e-9 else "FAIL"
        if total != 100:
            ok = False
        print(f"{flag} {k} weights sum to {total}")

    # Regression: Carroll M Johnston STEM Academy (Middle), official 51.5 / 3 stars
    carroll = dict(pooled_proficiency=26.2, math_mgp=56, ela_mgp=51, math_agp=21, ela_agp=39.9,
                   wida=37.5, math_gap=11.7, ela_gap=26.6, alp=95, credit8=81.8, chronic_absenteeism=28.5)
    r = compute("Middle", carroll, prior_ca=42.5)
    match = abs(r.index - 51.5) < 1e-9 and r.stars == 3
    ok = ok and match
    print(f"{'OK ' if match else 'FAIL'} Middle/Carroll -> {r.index} / {r.stars} stars (official 51.5 / 3)")

    # ES & HS PAT spot-checks against the manual
    spot = [
        ("ES pooled 60 ->20", PAT_ES_POOLED(60), 20), ("ES RBG3 50 ->3", PAT_ES_RBG3(50), 3),
        ("ES AGP math 52 ->7.5", PAT_ES_AGP_MATH(52), 7.5), ("ES WIDA 45 ->6", PAT_ES_WIDA(45), 6),
        ("ES gap ela 40 ->6", PAT_ES_GAP_ELA(40), 6), ("ES CA-red 30 ->5", PAT_ES_CA_REDUCTION(30), 5),
        ("HS math 42.4 ->10", PAT_HS_MATH(42.4), 10), ("HS ela 26 ->2.5", PAT_HS_ELA(26), 2.5),
        ("HS sci 33.1 ->3", PAT_HS_SCIENCE(33.1), 3), ("HS ACGR4 89.4 ->25", PAT_HS_ACGR4(89.4), 25),
        ("HS ACGR5 67 ->1", PAT_HS_ACGR5(67), 1), ("HS WIDA 20 ->10", PAT_HS_WIDA(20), 10),
        ("HS CCR part 59 ->5", PAT_HS_CCR_PART(59), 5), ("HS CCR comp 33 ->6", PAT_HS_CCR_COMP(33), 6),
        ("HS adv dip 25.5 ->3", PAT_HS_ADV_DIPLOMA(25.5), 3), ("HS CA 14 ->2.5", PAT_HS_CA_RATE(14), 2.5),
        ("HS credit9 92.4 ->4", PAT_HS_CREDIT9(92.4), 4), ("ES stars 84 ->5", stars_from(84, ELEMENTARY.star_cuts), 5),
        ("HS stars 81.9 ->4", stars_from(81.9, HIGH.star_cuts), 4),
    ]
    for name, got, want in spot:
        good = abs(got - want) < 1e-9
        if not good:
            ok = False
        print(f"{'OK ' if good else 'FAIL'} {name}: {got} (want {want})")

    print("RESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
