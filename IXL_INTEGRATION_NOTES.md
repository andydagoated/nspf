# IXL Projection Feature — Integration Notes

## What's new (3 files, 0 changes to existing code)

| File | Purpose |
|---|---|
| `ixl_ingest.py` | IXL export → NSPF-shaped rates. Mirrors `iready_ingest.py`'s contract exactly (same `ProjectedRate`/`ProjectionResult` containers, imported from it), so pages treat both paths identically. |
| `pages/2_Interim_IXL_Projection.py` | Streamlit page: upload → column mapping → **linking assumptions** → rates with confidence badges → same unmodified `nspf_engine.compute()` → PDF export → clear-data. |
| `synthetic_ixl_demo.csv` | 150 fake students (IDs are `DEMO-####`) shaped like an IXL export, calibrated to echo a "strong proficiency / weak math growth / strong ELA growth" profile — useful for live demos with zero real data. |

`nspf_engine.py`, `iready_ingest.py`, and the existing page are untouched.

## To commit

```bash
git add ixl_ingest.py pages/2_Interim_IXL_Projection.py synthetic_ixl_demo.csv
git commit -m "Add IXL diagnostic projection page with explicit linking assumptions"
git push
```

No new dependencies — uses the same requirements.txt (pandas, streamlit, openpyxl, fpdf2).

## The design decision that matters (be ready to explain it)

iReady exports a vendor-computed "Probable SBAC Level." **IXL doesn't**, and no
published IXL→SBAC concordance exists for Nevada. Rather than fake an
equivalence, the IXL path exposes three adjustable linking assumptions in the UI
(and stamps them into the exported PDF):

1. **Proficiency proxy** — projected proficient ⇔ IXL level ≥ grade×100 + offset
   (default offset 0; slider ±100). Schools with historical IXL-vs-SBAC data can
   calibrate the offset.
2. **Growth-target proxy** — expected gain prorated from 100 pts/year; students
   below grade level at BOY get a steeper catch-up target (close the deficit
   within 3 years) — an analog of the state's AGP concept, clearly labeled as a
   proxy, LOW confidence.
3. **MGP: honestly not derivable.** IXL has no peer-normed growth percentile.
   The page reports it as unavailable and the engine's existing logic flags the
   projection as provisional — no fabricated numbers.

Gap-closing upgrades itself automatically: if the upload maps a prior-year SBAC
level column, the gap population is the real one (prior < 3, MEDIUM confidence);
otherwise it falls back to "below grade level at BOY" (proxy, LOW confidence)
and says so.

## Guardrails preserved

- No student-level data written to disk anywhere; aggregation happens in memory
  and the DataFrame is deleted immediately after (`del canonical_df, raw_df`).
- PROJECTED/INTERIM disclaimers on screen and in the PDF; the PDF additionally
  records the exact linking assumptions used, so methodology travels with it.
- Same "Clear uploaded data" button and session-only storage as the iReady page.

## Before wider rollout

Same protocol as the iReady page: worth a Selena sign-off, since the linking
assumptions are a methodology choice CSAN's name would sit behind. The
assumption-disclosure design (sliders + PDF stamp) was built to make that
conversation easy.

## Tests run

- Module smoke test (`python ixl_ingest.py`) with synthetic data ✔
- End-to-end: mapping → aggregation → `compute("Middle", …)` returns a
  provisional index with MGP correctly listed as missing ✔
- Edge cases: no-BOY upload (growth measures gracefully unavailable),
  math-only upload, garbage values in numeric columns, xlsx round-trip ✔
- Streamlit boot: app and new page both return HTTP 200 headless ✔
