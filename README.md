[README (5).md](https://github.com/user-attachments/files/29074402/README.5.md)
# NSPF Star-Rating Estimator (Elementary · Middle · High)

A web app that estimates a Nevada school's **Total Index Score (0–100)** and
**star rating (1–5)** from its measure values. It implements the **2024-25 NSPF
Manual (version 8-15-2025)** for all three school levels.

Pick a school level and the inputs change to match that level's indicators.
Fields are named and grouped to match the line items on an official **NSPF school
rating report**, so values read off a report map directly onto the tool.

> This is an estimate to support planning and self-assessment — not an official
> NDE rating. **Enter only aggregate, school-level numbers**, never individual
> student records. This matters especially once deployed at a public URL.

---

## Validated against a real report

The engine reproduces the published 2024-25 rating for **Carroll M Johnston STEM
Academy** (middle school, Clark County) exactly — all five indicators, the 51.5
total index, and the 3-star rating, including the chronic absenteeism reduction
path. Run the built-in check: `python nspf_engine.py`. Validate against published
elementary and high schools too before relying on those levels.

## What it implements

- **Three levels**: elementary, middle, high — each with its own indicators,
  weights, Point Attribution Tables (manual Tables 1–32), and star cut scores
  (Tables 1–3).
- **Index** = points earned ÷ points possible × 100 (§1.2.2).
- **Rates truncated to the tenth** before table lookup (§1.3).
- **Chronic absenteeism** takes the higher of the rate path (plus the incentive
  point) or the reduction-rate path when a prior-year rate is supplied.
- A school missing any rating-required measure is flagged **Not Rated** (§1.2).

**Deliberately out of scope** (need student-level data): n-size sufficiency and
multi-year pooling, CSI/TSI/ATSI designations, and participation penalties.

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit user interface (with the school-level selector) |
| `nspf_engine.py` | Scoring engine for all three levels (PATs + validation self-test) |
| `METHODOLOGY.md` | Plain-language methodology — rendered on the app page and linkable |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Standard Python/Streamlit ignores |

> **Upgrading from the middle-school-only version:** delete the old
> `nspf_middle_school.py` from your repo and add `nspf_engine.py`. The app now
> imports from `nspf_engine`.

The app shows a fidelity statement and renders `METHODOLOGY.md` directly on the
page, plus a shareable link set by the `METHODOLOGY_URL` constant near the top of
`app.py` (update it to your repo path).

---

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy via GitHub

Upload these files to a repo (at the root), then at **share.streamlit.io** create
a new app pointing at your repo, branch `main`, main file **`app.py`**.
