"""
Glossary — plain-language definitions for every term used in this app.

Aimed at new users: teachers, school leaders, board members, and families who
are meeting NSPF terminology for the first time. Searchable, grouped by topic,
with a "why it matters" line wherever a term drives real decisions.

This page is static reference content — it takes no uploads and stores nothing.
"""

from __future__ import annotations
import streamlit as st

st.set_page_config(page_title="Glossary", layout="wide")

st.title("Glossary")
st.caption(
    "Plain-language definitions for the terms used across this app — the official NSPF "
    "vocabulary, the assessment platforms, and the projection tools. If a term you hit "
    "elsewhere in the app isn't here, that's a bug worth reporting."
)

search = st.text_input(
    "\U0001F50D Search the glossary",
    placeholder="Try: MGP, star rating, linking assumption, gap…",
)

# ----------------------------------------------------------------------
# Entries: (term, aka, definition, why_it_matters)
# Written for a reader with zero accountability background.
# ----------------------------------------------------------------------

GLOSSARY = {
    "The star rating system (NSPF basics)": [
        ("NSPF (Nevada School Performance Framework)", "the state rating system",
         "Nevada's official system for rating public schools, required by state law and the "
         "federal Every Student Succeeds Act. Schools earn points across several indicators; "
         "the points become an index score from 1\u2013100, which maps to a 1\u20135 star rating.",
         "Everything this app calculates is defined by the NSPF manual \u2014 the app reproduces "
         "the manual's math exactly."),
        ("Total Index Score", "the index",
         "Points earned divided by points possible, times 100. It's the single number "
         "(e.g., 88 out of 100) that determines a school's star rating.",
         "Small point losses in one indicator can move a school across a star boundary."),
        ("Star rating", None,
         "The 1\u20135 star label attached to the index score. For most schools: 5 stars at 80+, "
         "4 stars at 70\u201379.9, 3 stars at 50\u201369.9, 2 stars at 29\u201349.9, 1 star below 29.",
         "Stars are the public-facing summary \u2014 they affect reputation, enrollment, and "
         "(for charters) renewal conversations."),
        ("Indicator", "component",
         "A major scoring category. For middle schools: Academic Achievement (25 pts), Student "
         "Growth (30), English Language Proficiency (10), Closing Opportunity Gaps (20), and "
         "Student Engagement (15). Each indicator is made of individual measures.",
         "The weights tell you where the leverage is \u2014 growth is the single largest category "
         "for elementary and middle schools."),
        ("Measure", "line item",
         "One scored row inside an indicator \u2014 e.g., 'Math MGP' or 'Chronic Absenteeism.' "
         "Each measure's rate is looked up in a Point Attribution Table to award points.",
         "This app's inputs are named to match the measures on an official rating report, "
         "line for line."),
        ("Point Attribution Table", "PAT / scoring bands",
         "The official lookup table that converts a measure's rate into points. Rates fall "
         "into bands \u2014 e.g., a Math MGP of 46 lands in the band worth 4 of 10 points; an "
         "MGP in the 50s lands in a higher band.",
         "Because points move in bands, improving a rate just past a band boundary earns real "
         "index points \u2014 useful for goal-setting."),
        ("Truncation rule", None,
         "Before a rate is looked up in a scoring table, it's truncated (not rounded) to the "
         "tenth \u2014 62.79 becomes 62.7.",
         "A tiny technical rule, but reproducing official scores exactly requires it."),
        ("Not Rated (provisional)", None,
         "A school (or a projection) missing a required measure can't receive a complete "
         "rating. This app shows a provisional index built only from available measures and "
         "names what's missing.",
         "IXL-based projections are always provisional because MGP can't be derived from IXL."),
    ],

    "Proficiency terms": [
        ("Proficient", "meeting standards",
         "Scoring at Level 3 or Level 4 on the state assessment (SBAC for math and ELA). "
         "Levels 1\u20132 are below standard.",
         "Proficiency measures how many students are at grade level \u2014 a snapshot, not a "
         "trajectory."),
        ("Pooled Proficiency", None,
         "Total students proficient across the math, ELA, and science assessments combined, "
         "divided by total tests taken \u2014 one blended percentage.",
         "It's the entire Academic Achievement indicator (25 points) for elementary and "
         "middle schools."),
        ("SBAC (Smarter Balanced Assessment)", "the state test",
         "Nevada's end-of-year state assessment for math and ELA in grades 3\u20138. Results "
         "arrive after the school year ends.",
         "Every proficiency and growth measure in NSPF traces back to SBAC results."),
        ("Achievement level", "Levels 1\u20134",
         "The four performance bands on SBAC: Level 1 (minimal), Level 2 (approaching), "
         "Level 3 (meets standard), Level 4 (exceeds standard).",
         "\u2018Prior-year achievement level\u2019 determines who counts in the gap-closing "
         "population (Levels 1\u20132)."),
        ("MIP (Measure of Interim Progress)", None,
         "State-set improvement targets for each student group, shown on official reports "
         "next to each group's actual rate.",
         "Context on official reports \u2014 not an input to the score calculation itself."),
        ("95% participation requirement", "participation flag / penalty",
         "At least 95% of students overall and in each subgroup must take the state math and "
         "ELA assessments. Repeated misses lead to point deductions.",
         "A school can lose Achievement points without any change in actual performance."),
    ],

    "Growth terms (the heart of the system)": [
        ("SGP (Student Growth Percentile)", None,
         "One student's growth compared with their 'academic peers' \u2014 students statewide "
         "with the same test-score history. An SGP of 70 means the student grew more than 70% "
         "of students who started in the same place. 35\u201365 is considered typical.",
         "Growth is peer-relative: a student far below grade level can post huge growth, and "
         "a high scorer can post tiny growth."),
        ("MGP (Median Growth Percentile)", None,
         "A school's SGPs lined up from lowest to highest \u2014 the middle one. It answers: "
         "did the typical student here grow faster or slower than similar students statewide? "
         "50 is average.",
         "MGP is driven by the middle of the distribution, and it resets every year \u2014 "
         "schools can't coast on last year's growth."),
        ("AGP (Adequate Growth Percentile)", "growth-to-target",
         "Each student's personal target: the growth they need this year to reach \u2014 or stay "
         "at \u2014 proficiency within three years. The school measure is the percentage of "
         "students who met their individual target.",
         "MGP asks 'how fast?'; AGP asks 'fast enough to reach the destination?' A school can "
         "do fine on one and poorly on the other."),
        ("Closing Opportunity Gaps", "gap-closing",
         "The AGP question asked only of students who were NOT proficient last year: what "
         "share of them grew enough to be on track to proficiency?",
         "These students have the steepest targets in the building \u2014 this indicator "
         "measures whether a school accelerates its struggling students."),
        ("ELPA / WIDA", "English Language Proficiency indicator",
         "The share of English Learners meeting their growth targets on WIDA, the state's "
         "English language proficiency assessment.",
         "A full 10-point indicator \u2014 and one where strong EL support shows up directly "
         "in the rating."),
    ],

    "Engagement terms": [
        ("Chronic Absenteeism", "CA",
         "The share of students missing 10% or more of school days for any reason \u2014 "
         "excused, unexcused, or disciplinary. Lower is better.",
         "Schools can earn points two ways: a low rate, or a big reduction from last year "
         "(reducing CA by 10%+ earns a bonus incentive point). The app takes whichever path "
         "scores higher when you provide the prior-year rate."),
        ("Academic Learning Plans", "ALP",
         "The share of students with an academic learning plan on file, as state law requires.",
         "A small compliance-style measure \u2014 typically full points, but worth confirming."),
        ("8th Grade Credit Requirements", "credit8",
         "The share of 8th graders completing the units required for promotion to high school.",
         "Middle-school-only measure inside Student Engagement."),
    ],

    "Assessment platforms": [
        ("IXL", None,
         "A practice and diagnostic platform. Its Real-Time Diagnostic reports a level on "
         "IXL's own scale, where roughly 100 points equals one grade level (a level of 700 "
         "\u2248 working at the start of 7th grade).",
         "IXL levels are NOT state test scores \u2014 the IXL projection page uses explicit, "
         "adjustable assumptions to bridge that gap, and says so everywhere."),
        ("iReady", None,
         "A diagnostic platform whose exports include a vendor-computed 'Probable SBAC Level' "
         "\u2014 iReady's own projection of where a student would land on the state test.",
         "That built-in projection is why the iReady page carries higher confidence than the "
         "IXL page."),
        ("BOY / MOY / EOY", "beginning / middle / end of year",
         "The three typical diagnostic windows: Beginning-, Middle-, and End-of-Year.",
         "Growth proxies need at least two snapshots \u2014 usually BOY plus the current one."),
        ("Diagnostic", "interim assessment",
         "A periodic assessment (IXL, iReady, MAP, etc.) taken during the year, unlike the "
         "state test taken once at the end.",
         "Diagnostics are the early-warning system \u2014 the whole point of the projection "
         "pages is turning them into a directional NSPF estimate while there's time to act."),
    ],

    "Terms specific to this app's projection pages": [
        ("Projection", "estimate / interim projection",
         "A directional estimate of where the school's rating is heading, built from mid-year "
         "diagnostic data. It is NOT an official score and is labeled that way on every screen "
         "and export.",
         "The state tells you in September what happened; a projection tells you in January "
         "what's happening \u2014 while you can still change it."),
        ("Linking assumption", None,
         "An explicit, user-adjustable rule connecting a platform's scale to an NSPF-shaped "
         "measure \u2014 e.g., 'an IXL level at or above grade\u00d7100 counts as projected "
         "proficient.' No published IXL\u2192SBAC conversion exists, so the app makes the "
         "assumption visible instead of hiding it.",
         "Every linking assumption you set is stamped onto the exported PDF, so the "
         "methodology travels with the numbers."),
        ("Proxy measure", None,
         "A stand-in built from available data when the official measure can't be computed "
         "\u2014 e.g., the IXL growth-target proxy imitates the state's AGP concept using "
         "expected point gains.",
         "Proxies are useful for direction and dangerous for precision \u2014 which is what "
         "the confidence badges are for."),
        ("Confidence badge (High / Medium / Low)", None,
         "Every projected measure is tagged: High \u2248 direct count of vendor projections; "
         "Medium \u2248 rests on a linking assumption; Low \u2248 a proxy, or data the platform "
         "can't truly provide.",
         "Read the badges before the numbers. A projected index built mostly on Low-confidence "
         "measures should start conversations, not conclusions."),
        ("Minimum N (n-size)", "small-group suppression",
         "Rates computed from fewer than 10 students are statistically unstable. Official "
         "reports suppress them; this app flags them as 'directional only.'",
         "Also a privacy protection \u2014 tiny groups can make individual students "
         "identifiable."),
        ("Session-only data handling", "\u2018nothing is saved\u2019",
         "Uploaded files are processed in memory for your browser session and never written "
         "to disk or a database. Closing the tab, refreshing, or clicking 'Clear uploaded "
         "data' removes everything.",
         "You can use student-level exports without creating a stored copy anywhere \u2014 "
         "and exported PDFs contain only school-level aggregates."),
    ],
}


def matches(entry, q: str) -> bool:
    term, aka, definition, why = entry
    hay = " ".join(filter(None, [term, aka or "", definition, why or ""])).lower()
    return all(word in hay for word in q.lower().split())


q = (search or "").strip()
total_shown = 0

for section, entries in GLOSSARY.items():
    visible = [e for e in entries if not q or matches(e, q)]
    if not visible:
        continue
    st.subheader(section)
    for term, aka, definition, why in visible:
        title = f"**{term}**" + (f"  \u00b7  _{aka}_" if aka else "")
        with st.expander(term + (f"  ({aka})" if aka else ""), expanded=bool(q)):
            st.markdown(definition)
            if why:
                st.markdown(f"**Why it matters:** {why}")
    total_shown += len(visible)

if q and total_shown == 0:
    st.info(
        f"No matches for **{q}**. Try a shorter word (e.g., 'growth' instead of "
        "'growth percentile'), or browse the sections above with the search box empty."
    )

st.divider()
st.caption(
    "Definitions paraphrase the 2024-25 NSPF Manual in plain language and simplify some "
    "technical details \u2014 for the authoritative wording, see the manual and the "
    "METHODOLOGY document on the main page. Platform descriptions (IXL, iReady) refer to "
    "how their exports are used by this app, not to the vendors' full products."
)
