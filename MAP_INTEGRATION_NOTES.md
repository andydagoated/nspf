# MAP Growth Integration Notes

## What it does
`map_ingest.py` + `pages/3_Interim_MAP_Projection.py` turn a per-student NWEA
MAP Growth export (CDF or Combined Report) into NSPF-shaped aggregate rates and
run them through the same unmodified `nspf_engine.compute()` as everything else.
Same architecture as iReady/IXL: canonical schema -> header auto-mapping (human-
confirmed) -> in-memory aggregation -> engine. No student data touches disk.

## How MAP columns map to NSPF measures
| NSPF measure | MAP source | Confidence |
|---|---|---|
| pooled_proficiency | Projected Proficiency Level (state linking study, `>= Level 3`) | HIGH |
| pooled_proficiency (fallback) | Achievement percentile `>=` user-set cut | LOW, labeled |
| math_mgp / ela_mgp | median Conditional Growth Percentile (CGP) | LOW (not state SGP) |
| math_agp / ela_agp | Met Projected Growth (Yes*/No* parsed leniently) | MEDIUM (NWEA projection, not AGP target) |
| math_gap / ela_gap | Met Projected Growth among prior-year non-proficient (merged column) | MEDIUM |

## MAP quirks handled
- **Course naming:** Reading -> ELA; Mathematics/Math K-12 -> MATH; Language
  Usage, Science, and anything unrecognized are dropped and counted
  (`n_dropped_other`), surfaced in the UI and PDF.
- **Multi-term files:** a CDF with Fall + Winter rows would double-count
  students; the module parses TermName ("Winter 2026-2027") and keeps only the
  most recent term, reporting what it did (`term_used`, `term_note`).
  Unparseable terms -> all rows kept, caller warned.
- **Retests:** deduped to one row per student per subject after term filtering.
- **Yes\*/No\* flags:** asterisks (NWEA's incomplete-data marker) ignored.
- **Growth-met fallback:** if the Met flag is absent but Observed and Projected
  Growth (RIT) are both mapped, met = observed >= projected.
- **Proficiency text variants:** "Level 3", "L3", "Meets Standard",
  "Not on Track", "Approaching" all parse; negations checked before positives.

## Deliberate limits
- Prior-year state achievement level is not in MAP exports; the gap measures
  only light up when a school maps a merged-in column.
- The percentile-cut fallback has no official basis; the UI says so and the
  LOW tag travels into the PDF.
- WIDA, engagement, HS-only measures: out of scope, entered manually or left
  unreported (engine then shows Not Rated (provisional) as designed).

## Tests
`python map_ingest.py` runs the synthetic smoke test + parser unit checks.
The end-to-end path (synthetic CDF -> rates -> compute) is exercised in CI-able
form; `nspf_engine.py` self-tests are untouched and still pass.
