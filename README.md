[README (4).md](https://github.com/user-attachments/files/29070087/README.4.md)
# NSPF Middle School Star-Rating Estimator

A web app that estimates a Nevada middle school's **Total Index Score (0–100)** and
**star rating (1–5)** from its measure values. It implements the **2024-25 NSPF
Manual (version 8-15-2025)**.

Input fields are named and grouped to match the line items on an official **NSPF
school rating report**, so values read off the report's front page map directly
onto the tool.

> This is an estimate to support planning and self-assessment — not an official
> NDE rating. **Enter only aggregate, school-level numbers**, never individual
> student records. This matters especially once deployed at a public URL.

---

## Validated against a real report

The engine reproduces the published 2024-25 rating for **Carroll M Johnston STEM
Academy** (Clark County) exactly — all five indicators, the 51.5 total index, and
the 3-star rating, including the chronic absenteeism *reduction-rate* path:

| Indicator | Engine | Official report |
|---|---|---|
| Academic Achievement | 6 / 25 | 6 / 25 |
| Student Growth | 16.5 / 30 | 16.5 / 30 |
| English Language Proficiency | 10 / 10 | 10 / 10 |
| Closing Opportunity Gaps | 10 / 20 | 10 / 20 |
| Student Engagement | 9 / 15 | 9 / 15 |
| **Total → stars** | **51.5 → ★★★** | **51.5 → ★★★** |

This check runs automatically: `python nspf_middle_school.py`. Validate against a
few more published schools before relying on the tool, and record the result.

---

## What it implements (faithful to the manual)

| Indicator | Weight | Measures (report labels) | Source |
|---|---|---|---|
| Academic Achievement | 25 | Pooled Proficiency | Table 11 |
| Student Growth | 30 | Math/ELA MGP (10 ea), Met Math/ELA AGP Target (5 ea) | Tables 12–13 |
| English Language Proficiency | 10 | Met EL AGP Target | Table 14 |
| Closing Opportunity Gaps | 20 | Prior Non-Proficient Met Math/ELA AGP Target | Table 15 |
| Student Engagement | 15 | Chronic Absenteeism (10), Academic Learning Plans (2), 8th Grade Credits (3) | Tables 16–19 |

- **Index** = points earned ÷ points possible × 100 (§1.2.2).
- **Rates truncated to the tenth** before table lookup (§1.3).
- **Star cuts** (Table 2): 5★ ≥80 · 4★ 70–79 · 3★ 50–69 · 2★ 29–49 · 1★ <29.
- **Chronic Absenteeism** takes the higher of the rate PAT (Table 16, plus the
  +1 incentive point for a 10%+ reduction) or the **reduction-rate PAT**
  (Table 17), when a prior-year rate is supplied. The reduction rate is the
  percent decrease over the prior year, as confirmed by NSPF school reports.
- A school missing any rating-required measure (pooled proficiency and all four
  growth measures) is flagged **Not Rated** (§1.2).

### Deliberately out of scope (need student-level data)

n-size sufficiency and multi-year pooling (§1.2.1, §3.2); CSI/TSI/ATSI school
designations (§7); and assessment participation penalties (§6).

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit user interface |
| `nspf_middle_school.py` | Scoring engine (Point Attribution Tables + validation self-test) |
| `METHODOLOGY.md` | Plain-language methodology — rendered on the app page and linkable |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Standard Python/Streamlit ignores |

The app shows a fidelity statement and renders `METHODOLOGY.md` directly on the
page (in an expander), plus a shareable link. The link target is set by the
`METHODOLOGY_URL` constant near the top of `app.py` — update it to your repo path
(default points at `METHODOLOGY.md` on the `main` branch).

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy via GitHub

Upload these files to a repo (at the root), then at **share.streamlit.io** create
a new app pointing at your repo, branch `main`, main file **`app.py`**.
