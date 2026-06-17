## How the middle school star rating is calculated

This estimator reproduces the scoring method in the **2024-25 NSPF Manual
(version 8-15-2025)** published by the NDE Office of Assessment, Data, and
Accountability Management. It is written so any reader can follow the method and
check the result independently.

### What this tool is

It is a transparent calculator that applies the official NSPF weights and scoring
tables to a school's measure values. It uses **no artificial intelligence and no
hidden logic** — the result is plain arithmetic anyone can reproduce by hand. It
does not generate a school's underlying numbers (you supply those), and it is
**not an official NDE rating**; NDE produces the authoritative determination.

### Where the rules come from

Every weight, scoring table, and cut score is taken directly from the 2024-25
manual: indicator weights from Table 10, the star cut scores from Table 2, and
the Point Attribution Tables (PATs) from Tables 11–19. Rates are truncated to the
tenth before table lookup (§1.3), and the index is computed exactly as §1.2.2
defines it.

### The calculation, step by step

1. **Score each measure.** Each measure's rate is looked up in its official Point
   Attribution Table to award points (for example, a pooled proficiency rate of
   26.2% earns 6 of 25 points on Table 11).
2. **Total the points** earned and the points possible across all measures.
3. **Compute the index:** points earned ÷ points possible × 100.
4. **Assign the stars** by comparing the index to the cut scores.

A measure a school cannot report (suppressed by minimum-N rules) drops out of both
the earned and the possible totals. A school missing any rating-required measure
(pooled proficiency and all four growth measures) is flagged **Not Rated** per §1.2.

### Components and weights (Table 10)

| Indicator | Points | Measures (as labeled on the report) |
|---|---|---|
| Academic Achievement | 25 | Pooled Proficiency |
| Student Growth | 30 | Math/ELA MGP (10 each), Met Math/ELA AGP Target (5 each) |
| English Language Proficiency | 10 | Met EL AGP Target |
| Closing Opportunity Gaps | 20 | Prior Non-Proficient Met Math/ELA AGP Target (10 each) |
| Student Engagement | 15 | Chronic Absenteeism (10), Academic Learning Plans (2), 8th Grade Credits (3) |

### Star cut scores (Table 2)

| Rating | Total Index Score |
|---|---|
| 5 stars | 80 and above |
| 4 stars | 70 – 79 |
| 3 stars | 50 – 69 |
| 2 stars | 29 – 49 |
| 1 star | below 29 |

### Chronic absenteeism

Absenteeism is scored on the rate table (Table 16). When a prior-year rate is
supplied, the tool also applies the +1 incentive point for a 10%-or-greater
reduction (§5.1.5.1) and the reduction-rate alternative (Table 17), and awards
whichever path is higher — the same logic shown on school rating reports.

### Validated against a published report

The engine reproduces the published 2024-25 rating for **Carroll M Johnston STEM
Academy** (Clark County) exactly:

| Indicator | This tool | Official report |
|---|---|---|
| Academic Achievement | 6 / 25 | 6 / 25 |
| Student Growth | 16.5 / 30 | 16.5 / 30 |
| English Language Proficiency | 10 / 10 | 10 / 10 |
| Closing Opportunity Gaps | 10 / 20 | 10 / 20 |
| Student Engagement | 9 / 15 | 9 / 15 |
| **Total → rating** | **51.5 → ★★★** | **51.5 → ★★★** |

### Why the result can be trusted

- **Transparency** — every number that drives a result is visible, and the math
  is checkable by hand.
- **Fidelity** — the tool reproduces NDE's published method and cites the exact
  manual tables, rather than substituting a different scoring system.
- **Validation** — it reproduces a real, already-published star rating exactly.

### Limitations and appropriate use

The estimate is only as good as the values entered; the tool does not verify them.
For small schools, measures may be suppressed under minimum reporting rules, which
changes how the index is composed. The tool deliberately does not compute n-size
pooling, the CSI/TSI/ATSI school designations, or assessment participation
penalties, because those require student-level data the tool does not take. This
is an estimate for planning and self-assessment, not a substitute for NDE's
official determination.

### Verify it yourself

Take any result, add the component points, divide by the points possible, multiply
by 100, and confirm the index and star band. Or enter a school whose official
rating is already published and confirm the tool returns the same rating.

*Source: NDE NSPF Manual, school year 2024-25 (version 8-15-2025).*
