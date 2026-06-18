## How the NSPF star rating is calculated

This estimator reproduces the scoring method in the **2024-25 NSPF Manual
(version 8-15-2025)** for all three school levels — **elementary, middle, and
high** — published by the NDE Office of Assessment, Data, and Accountability
Management. It is written so any reader can follow the method and check the
result independently.

### What this tool is

A transparent calculator that applies the official NSPF weights and scoring
tables to a school's measure values. It uses **no artificial intelligence and no
hidden logic** — the result is plain arithmetic anyone can reproduce by hand. You
supply the school's numbers; the tool only converts them into a rating. It is
**not an official NDE rating**; NDE produces the authoritative determination.

### Where the rules come from

Every weight, scoring table, and cut score comes directly from the 2024-25
manual — Tables 1–9 (elementary), 10–19 (middle), and 20–32 (high). Rates are
truncated to the tenth before table lookup (§1.3), and the index is computed
exactly as §1.2.2 defines it.

### The calculation, step by step

1. **Score each measure** by looking its rate up in the official Point Attribution
   Table to award points.
2. **Total** the points earned and the points possible.
3. **Compute the index:** points earned ÷ points possible × 100.
4. **Assign the stars** by comparing the index to the level's cut scores.

A measure suppressed by minimum-N rules drops out of both totals. A school missing
any rating-required measure is flagged **Not Rated** (§1.2).

### Indicators and weights by level (each totals 100)

**Elementary** — Academic Achievement 25 (Pooled Proficiency 20, Read by Grade 3 5);
Student Growth 35 (Math/ELA MGP 10 each, Math/ELA AGP 7.5 each); English Language
Proficiency 10; Closing Opportunity Gaps 20 (Math/ELA 10 each); Student Engagement
10 (Chronic Absenteeism).

**Middle** — Academic Achievement 25 (Pooled Proficiency); Student Growth 30
(Math/ELA MGP 10 each, Math/ELA AGP 5 each); English Language Proficiency 10;
Closing Opportunity Gaps 20 (Math/ELA 10 each); Student Engagement 15 (Chronic
Absenteeism 10, Academic Learning Plans 2, 8th-Grade Credits 3).

**High** — Academic Achievement 25 (Math 10, ELA 10, Science 5); Graduation Rates
30 (4-Year ACGR 25, 5-Year ACGR 5); English Language Proficiency 10; College &
Career Readiness 25 (Post-Secondary Participation 10, Completion 10, Advanced/CCR
Diploma 5); Student Engagement 10 (Chronic Absenteeism 5, 9th-Grade Credit
Sufficiency 5).

### Star cut scores (Tables 1–3)

| Rating | Elementary | Middle | High |
|---|---|---|---|
| 5 stars | ≥84 | ≥80 | ≥82 |
| 4 stars | 67–83 | 70–79 | 70–81 |
| 3 stars | 50–66 | 50–69 | 50–69 |
| 2 stars | 27–49 | 29–49 | 27–49 |
| 1 star | <27 | <29 | <27 |

### Chronic absenteeism

Scored on the level's rate table. When a prior-year rate is supplied, the tool
also applies the incentive point for a 10%+ reduction and the reduction-rate
alternative, awarding whichever path is higher — the same logic shown on school
rating reports. The reduction rate is the percent decrease over the prior year.
(Incentive amounts and reduction tables differ by level.)

### Validated against a published report

The engine reproduces the published 2024-25 rating for **Carroll M Johnston STEM
Academy** (middle school, Clark County) exactly — all five indicators, the 51.5
total index, and the 3-star rating, including the chronic absenteeism
reduction-rate path (a 32.9% reduction earning 5 points). This check runs
automatically via `python nspf_engine.py`. Validate against published elementary
and high schools as well before relying on those levels.

### Why the result can be trusted

- **Transparency** — every number that drives a result is visible and checkable by hand.
- **Fidelity** — the tool reproduces NDE's published method and cites the exact manual tables.
- **Validation** — it reproduces a real, already-published star rating exactly.

### Limitations and appropriate use

The estimate is only as good as the values entered; the tool does not verify them.
For small schools, measures may be suppressed under minimum reporting rules. The
tool deliberately does not compute n-size pooling, the CSI/TSI/ATSI designations,
or assessment participation penalties, which require student-level data the tool
does not take. This is an estimate for planning and self-assessment, not a
substitute for NDE's official determination.

*Source: NDE NSPF Manual, school year 2024-25 (version 8-15-2025).*
