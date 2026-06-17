[README (2).md](https://github.com/user-attachments/files/29069182/README.2.md)
# NSPF Middle School Star-Rating Estimator

A web app that estimates a Nevada middle school's **NSPF index (0–100)** and
**star rating (1–5)** from its measure values. It implements the **2024-25 NSPF
Manual (version 8-15-2025)** published by the NDE Office of Assessment, Data, and
Accountability Management.

> This is an estimate to support planning and self-assessment — not an official
> NDE rating. **Enter only aggregate, school-level numbers** (proficiency rates,
> growth percentiles, absenteeism %), never individual student records. This
> matters especially once the app is deployed at a public URL.

---

## What it implements (faithful to the manual)

| Component | Weight | Source |
|---|---|---|
| Academic Achievement — pooled proficiency | 25 | Table 10, PAT Table 11 |
| Growth — Math/ELA MGP (10 each), Math/ELA AGP (5 each) | 30 | Tables 12–13 |
| English Learner Progress — WIDA AGP | 10 | Table 14 |
| Closing Opportunity Gaps — Math + ELA | 20 | Table 15 |
| Student Engagement — absenteeism (10), ALP (2), 8th-grade credits (3) | 15 | Tables 16, 18, 19 |

- **Index** = points earned ÷ points possible × 100 (manual §1.2.2).
- **Rates are truncated to the tenth** before table lookup (§1.3).
- **Star cuts** (Table 2): 5★ ≥80 · 4★ 70–79 · 3★ 50–69 · 2★ 29–49 · 1★ <29.
- A school missing any rating-required measure (pooled proficiency and all four
  growth measures) is flagged **Not Rated**, per §1.2.

### Deliberately out of scope (need student-level data)

n-size sufficiency and multi-year pooling (§1.2.1, §3.2); CSI/TSI/ATSI school
designations (§7); assessment participation penalties (§6); and the Chronic
Absenteeism Reduction PAT (Table 17), whose "reduction rate" formula is not given
explicitly in the manual. The Chronic Absenteeism Incentive Point (§5.1.5.1) **is**
implemented and activates only when a prior-year rate is supplied.

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit user interface |
| `nspf_middle_school.py` | The scoring engine (Point Attribution Tables, no UI) |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Standard Python/Streamlit ignores |

---

## Run it on your own computer

```bash
pip install -r requirements.txt
streamlit run app.py
```
It opens at `http://localhost:8501`.

## Run it via GitHub (free public app)

1. Upload these files to a GitHub repository (at the repo root).
2. Go to **share.streamlit.io**, sign in with GitHub, click **New app**.
3. Choose your repo, branch `main`, main file **`app.py`**, and **Deploy**.

---

## Validation gate

Even a faithful implementation should be checked against reality before anyone
relies on it. Pull several real Nevada middle schools' published 2024-25 measure
values, enter them, and confirm the app reproduces each school's published star
rating. Record the result (e.g., "matched 20 of 20") — that is the strongest
evidence of trustworthiness.

If a school does not match, likely culprits are the pooled-proficiency inputs
(the manual combines Math + ELA + Science into one rate) or a measure entered on
a different basis than the manual defines.
