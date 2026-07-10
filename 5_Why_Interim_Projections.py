"""
Why Interim Projections? — what projected scores are for, and what they aren't.

Aimed at school leaders deciding whether a mid-year projected NSPF estimate is
worth their team's attention, and at anyone who needs to explain (to a board,
a coach, or a skeptical colleague) why the school runs interim projections at
all. Written to be honest about limits: a projection you over-trust is worse
than no projection.

This page is static reference content — it takes no uploads and stores nothing.
"""

from __future__ import annotations
import streamlit as st

st.set_page_config(page_title="Why Interim Projections?", layout="wide")

st.title("Why Interim Projections?")
st.caption(
    "What a projected NSPF estimate is good for, what it is not good for, and how to "
    "act on one without over-trusting it. The projection pages (iReady, IXL, MAP Growth) "
    "all feed the same official scoring engine \u2014 this page explains why that's useful "
    "in January even though the real rating doesn't arrive until fall."
)

st.divider()

# ----------------------------------------------------------------------
st.header("The core problem these pages solve")
st.markdown(
    """
The official NSPF rating is a **lagging indicator**. It scores last year's students on
last year's tests and arrives after those students have moved on. By the time a school
learns it missed a star band by 1.5 index points, every decision that could have changed
the outcome is months in the past.

Schools already sit on **leading indicators** \u2014 interim diagnostics (iReady, MAP Growth,
IXL) given in fall and winter to the students who are here right now. What's usually
missing is the translation: interim platforms report in their own vocabulary (RIT scores,
diagnostic tiers, growth percentiles), and nobody on staff has time to hand-convert that
into "so where would we land on the state framework?"

That translation is all these pages do. They aggregate an interim export into
NSPF-shaped rates and run the **same unmodified scoring engine** used for official-report
math elsewhere in this app. Nothing about the state's scoring is approximated \u2014 the
approximation lives entirely, and visibly, in the input rates.
"""
)

# ----------------------------------------------------------------------
st.header("Five things a projection is genuinely useful for")

st.markdown(
    """
**1. Finding out in January, not September.**
A projection turns "we hope growth is better this year" into "on winter data we project
an index around 52 \u2014 two points above the 3-star floor, eighteen below 4 stars." Even
with generous error bars, that locates the school on the map while there is still a
semester to act.

**2. Seeing which measures drive the score \u2014 and which are actually movable mid-year.**
The indicator breakdown shows where points are being earned and lost *by NSPF weight*,
which is often not where instinct says. Growth is the largest indicator for elementary
and middle schools; a school pouring energy into proficiency while its MGP sits in a low
band is optimizing the wrong line. And one high-leverage measure \u2014 **chronic
absenteeism** \u2014 is fully live mid-year: unlike test results, every week of improved
attendance directly changes the rate the state will eventually score, and the reduction
credit means improvement over last year earns points even if the rate is still high.

**3. Band-edge math for goal-setting.**
NSPF points move in bands (see *Point Attribution Table* in the Glossary). A projection
exposes when a measure sits just below a band boundary \u2014 an MGP of 47 versus 48, a
proficiency rate a point under the next cut \u2014 where a small real improvement buys
disproportionate index points. That's the difference between a vague goal ("improve
math") and a defensible one ("move 12 more students past their growth target, which is
one band, which is two index points").

**4. A common language for teams.**
An instructional coach thinks in diagnostic tiers; a board thinks in stars; a principal
has to speak both. A projection puts interim data into the vocabulary the school is
ultimately judged in, which makes mid-year conversations concrete: *this* winter number
maps to *that* fall consequence.

**5. Removing the surprise from the official release.**
A school that has watched a credible projection all year is never ambushed by its rating.
Leadership can prepare context, staff, and families in advance \u2014 in either direction.
"""
)

# ----------------------------------------------------------------------
st.header("What a projection is NOT")

st.error(
    "A projected score is **not an official NSPF rating** and must never be presented as "
    "one \u2014 not to a board, not to families, not to an authorizer, not in a grant "
    "application. Every projection page and PDF in this app carries that disclaimer for "
    "a reason."
)

st.markdown(
    """
Be equally clear-eyed about the quieter failure modes:

- **It is not a prediction with known accuracy.** The projection assumes interim results
  translate to end-of-year state results the way the platform's linking study (or proxy
  measure) says they do. Linking studies are decent on average and wrong for individual
  schools in individual years \u2014 especially when winter-to-spring instruction, testing
  conditions, or student rosters shift.
- **The growth measures are the weakest link.** The state's MGP comes from its official
  student growth percentile model. No interim platform reproduces that model; the pages
  substitute the platform's own growth metric and tag it **low confidence**. Treat
  projected growth points as a sketch, not a measurement.
- **It is not a teacher evaluation input.** These are school-level aggregates built on
  proxy measures. Using them to evaluate individual educators would be indefensible on
  both statistical and fairness grounds.
- **It is not a reason to teach to the interim.** The projection is only informative if
  the interim assessment stays an honest signal. Prepping students for the diagnostic
  inflates the projection and destroys the one thing it's for.
"""
)

# ----------------------------------------------------------------------
st.header("How to read the confidence tags")

st.markdown(
    """
Every projected rate carries a tag \u2014 the honesty mechanism of the whole feature:

- \U0001F7E2 **High** \u2014 built from the platform's state linking study (e.g., projected
  SBAC level). The strongest available mid-year proxy for the real measure.
- \U0001F7E1 **Medium** \u2014 built from a reasonable stand-in (e.g., "met projected growth"
  proxying the state AGP target). Directionally useful; don't bet a band boundary on it.
- \U0001F534 **Low** \u2014 built from something structurally different from the state's
  measure (platform growth percentiles standing in for state SGP; a user-set percentile
  cut standing in for a linking study). Include it to see a complete index, but treat
  those points as the widest error bars on the page.

A practical rule: when deciding *where the school stands*, weight the high-confidence
measures. When deciding *what to work on*, the low-confidence growth measures still
point at the right students \u2014 they're just unreliable about exactly how many points
the state will award for it.
"""
)

# ----------------------------------------------------------------------
st.header("A responsible mid-year routine")

st.markdown(
    """
1. **After each interim window (BOY, MOY):** export, upload, project. Ten minutes.
2. **Read the indicator breakdown before the headline.** The index grabs attention; the
   per-indicator earned/possible is where decisions live.
3. **Pick at most two levers.** Usually: the measure closest below a band boundary, and
   chronic absenteeism if it's scoring poorly (it's the one measure a school can move
   every single week).
4. **Write the goal in NSPF terms** \u2014 "X more students past growth targets = one band
   = Y index points" \u2014 so June-you can check whether it happened.
5. **Re-project at the next window and compare.** Direction of change between two
   projections on the same platform is more trustworthy than either projection's level.
6. **Keep it internal.** Share the PDF with leadership and coaches; it's built to be
   safe to share (aggregates only) \u2014 but *internal* is the operative word.
"""
)

# ----------------------------------------------------------------------
st.header("One honest caveat to leave in every conversation")

st.markdown(
    """
The gap between a winter projection and the fall rating is not an error in the tool \u2014
it *is the semester*. Students grow or don't, attendance improves or doesn't, spring
testing goes well or badly. A projection that differs from the eventual official score
by a few index points did its job: it described where the school stood in winter, in
time to do something about it.

If a projection ever needs to be *right* rather than *useful* \u2014 for a public claim, a
renewal document, a funder \u2014 stop. That's what the official rating is for, and the
official calculator on the main page reproduces it exactly, from official numbers.
"""
)

st.divider()
st.caption(
    "Static reference page \u2014 nothing here uploads, stores, or computes anything. "
    "For term definitions, see the Glossary. For the projections themselves, see the "
    "iReady, IXL, and MAP Growth pages in the sidebar."
)
