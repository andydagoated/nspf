[README (1).md](https://github.com/user-attachments/files/29065741/README.1.md)
# NSPF Middle School Star-Rating Estimator

A small web app that estimates a Nevada middle school's **NSPF index (0–100)** and
**star rating (1–5)** from its indicator values. It is the deterministic scoring core
of a larger prediction pipeline: forecast the indicator inputs, then run them through
this engine.

> ⚠️ **Read this first.**
> Every weight, scoring rule, and star cut score in this app is an **illustrative
> placeholder**. Before relying on any result, replace them (in the sidebar, or in
> `nspf_middle_school.py`) with the official values from the **NDE NSPF technical
> guide** for your target year.
>
> **Never enter individual student data.** Use only aggregate, school-level numbers
> (proficiency rates, growth percentiles, absenteeism %). This keeps you clear of
> FERPA concerns — especially important once the app is on a public URL.

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit user interface |
| `nspf_middle_school.py` | The scoring engine (no UI, importable) |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Standard Python/Streamlit ignores |

---

## Run it on your own computer

1. Install Python 3 (from python.org) if you don't have it.
2. In a terminal, from this folder:
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. It opens in your browser at `http://localhost:8501`.

---

## Run it "in GitHub" (free public app via Streamlit Community Cloud)

1. Create a new repository on GitHub and upload these files (or push this folder).
2. Go to **share.streamlit.io**, sign in with GitHub, and click **New app**.
3. Pick your repository, branch `main`, and set the main file to **`app.py`**.
4. Click **Deploy**. After a minute you get a public URL anyone can use — no
   install required on their end.

Streamlit Cloud reads `requirements.txt` automatically to build the environment.

---

## Before you trust the output: the validation gate

The scoring formula is only as right as the numbers you put in the config. To check it:

1. Pull last year's **actual published indicator values** for several real Nevada
   middle schools from the Nevada Report Card / accountability portal.
2. Enter them in the app.
3. Confirm the app reproduces each school's **published star rating**.

If it doesn't match, your weights, rubrics, or cut scores are off — fix those before
building anything on top.

---

## What's next in the pipeline

- **Input forecasting:** map interim assessment + attendance-to-date data into
  projected end-of-year indicator values.
- **Monte Carlo:** turn noisy input ranges into a probability of landing in each
  star band, rather than a single point estimate.
