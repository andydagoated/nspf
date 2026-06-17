# How the NSPF Star Rating Is Calculated
### Methodology for the Middle School Rating Estimator

**Purpose.** This document explains, in plain terms, how this tool arrives at a
school's Nevada School Performance Framework (NSPF) index and star rating. It is
written so that any reader — a board member, an authorizer, or a school leader —
can follow the method and check the result independently.

---

## What this tool is

The tool reproduces the official scoring formula published by the Nevada
Department of Education (NDE). You give it a middle school's indicator values —
proficiency rates, growth percentiles, attendance, and so on — and it applies the
same point weights and cut scores NDE uses to produce an estimated index (0–100)
and a star rating (1–5).

It is a transparent calculator, not a predictive model and not an official source:

- It uses no artificial intelligence, no machine learning, and no hidden logic.
  The result is plain arithmetic that anyone can reproduce by hand.
- It does not generate or guess a school's underlying numbers. You supply those;
  the tool only converts them into a rating.
- It is not an official NDE rating. NDE produces the authoritative determination.
  This tool estimates what that rating would be for a given set of inputs.

---

## Where the rules come from

Every weight and cut score used here is taken from the **NDE NSPF Technical Guide
for school year [confirm year: ________ ]**. Using NDE's own published values is
what makes the estimate comparable to the official rating — the tool is not
inventing a scoring system, it is mirroring the established one.

---

## The calculation, step by step

1. **Score each measure.** Each measure (for example, ELA proficiency) has a
   maximum number of points set by NDE, and a rule that converts the school's raw
   value into points earned — somewhere between zero and that maximum.
2. **Total the points.** Add up the points earned across all measures, and
   separately add up the points possible.
3. **Compute the index.** Divide points earned by points possible and multiply by
   100. This is the index, on a 0–100 scale.
4. **Assign the stars.** Compare the index to the star cut scores to land on a
   rating from one to five stars.

Because the index is "points earned out of points possible," a measure a school
cannot report — for example, an English learner measure at a school with too few
English learners to meet minimum reporting thresholds — is removed from both the
earned and the possible totals rather than counted as a zero. This keeps small
schools from being penalized for data they are not required to report.

---

## Components and weights

The measures roll up into five components. The point weights below reflect the
values currently configured in the tool.

> **Before distributing this document, confirm every figure in the two tables
> below matches the official NDE Technical Guide for the year cited above.**

| Component | What it measures | Maximum points |
|---|---|---|
| Academic Achievement | ELA, math, and science proficiency | 30 |
| Student Growth | ELA and math growth percentiles and adequate-growth rates | 30 |
| Closing Opportunity Gaps | performance of the lowest-performing students | 20 |
| English Learner Progress | progress toward English proficiency | 10 |
| Student Engagement | chronic absenteeism and school climate | 10 |
| **Total** | | **100** |

Star cut scores applied to the 0–100 index:

| Rating | Index range |
|---|---|
| ★★★★★ | 82 and above |
| ★★★★ | 65 – 81 |
| ★★★ | 50 – 64 |
| ★★ | 27 – 49 |
| ★ | below 27 |

---

## A worked example

Consider a school with these results. Its ELA proficiency is 48%, and the rule for
that measure awards the same share of its 10 points — so 48% of 10 is **4.8
points**. Math proficiency at 35% earns 3.5 points; science at 40% earns 4.0.
Every other measure is scored the same way. Rolling the measures up into their
components gives:

| Component | Points earned | Points possible |
|---|---|---|
| Academic Achievement | 12.3 | 30 |
| Student Growth | 13.4 | 30 |
| Closing Opportunity Gaps | 9.2 | 20 |
| English Learner Progress | 5.5 | 10 |
| Student Engagement | 5.5 | 10 |
| **Total** | **45.9** | **100** |

Earned divided by possible, times 100, is an index of **45.9**. Because 45.9 falls
in the 27-to-49 range, this school lands at **2 stars** — and it is 4.1 points
short of the 50 it would need to reach 3 stars. A reader can take the component
numbers above, add them, divide by 100, and confirm both the index and the rating.
Nothing is hidden.

---

## Why the result can be trusted

**Transparency.** Every number that drives a result is visible, and the math is
checkable by hand. There is no proprietary model and no judgment call inside the
calculation — only the published weights and the arithmetic above.

**Fidelity to the official framework.** The tool reproduces NDE's own scoring
method and cites the exact technical guide and year as the source of every weight
and cut score. The estimate is built to match the standard, not to substitute a
different one.

**Validation against real ratings.** The strongest assurance is that the tool
reproduces star ratings NDE has already published (see the next section).

---

## Validation status

[Operator to complete before relying on results:]

> This tool was tested against **[ number ]** Nevada middle schools using their
> published [year] indicator values. It reproduced the official NDE star rating
> for **[ number ] of [ number ]** of them.

Running this check is what turns "the formula is correct" into "the tool matches
reality." Until it is complete, the tool computes correctly but should not be
described as accuracy-tested.

---

## Limitations and appropriate use

- The estimate is only as good as the values entered. The tool converts inputs
  into a rating; it does not verify that the inputs are correct.
- For small schools, measures may be suppressed under minimum reporting rules,
  which changes how the index is composed.
- NDE periodically revises the framework. Confirm the tool is configured for the
  same year you are estimating.
- This is an estimate to support planning and self-assessment. It is not a
  substitute for NDE's official determination.

---

## How to verify it yourself

You do not have to take the tool's word for anything. Two checks are available to
any reader. First, take the component points from any result, add them, divide by
the points possible, multiply by 100, and confirm the index and star band match.
Second, enter a school whose official rating is already published and confirm the
tool returns the same rating.

---

*Source: NDE NSPF Technical Guide, school year [________]. Prepared by [________].
Version [____], dated [________].*
