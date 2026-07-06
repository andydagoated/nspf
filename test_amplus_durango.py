"""
Regression test: Amplus Academy - Durango Campus (Middle), 2024-25.
Source of expected values: the school's published Nevada School Rating report.

Run:  python test_amplus_durango.py
Exits non-zero on any mismatch, so it can sit in CI next to the other
official-report regression tests.
"""

from nspf_engine import compute

VALUES = {
    "pooled_proficiency": 62.7,
    "math_mgp": 46,
    "ela_mgp": 63,
    "math_agp": 48.2,
    "ela_agp": 73.9,
    "wida": 39.3,
    "math_gap": 13.6,
    "ela_gap": 49.0,
    "chronic_absenteeism": 6.5,   # prior-year 10.3 -> -36.8% change -> +1 incentive
    "alp": 95.1,                  # published as ">95"
    "credit8": 95.1,              # published as ">95"
}

EXPECTED_INDEX = 88.0
EXPECTED_STARS = 5
EXPECTED_COMPONENTS = {
    "Academic Achievement": 25.0,
    "Student Growth": 23.0,
    "English Language Proficiency": 10.0,
    "Closing Opportunity Gaps": 15.0,
    "Student Engagement": 15.0,
}
EXPECTED_MEASURES = {
    "pooled_proficiency": 25.0,
    "math_mgp": 4.0,
    "ela_mgp": 9.0,
    "math_agp": 5.0,
    "ela_agp": 5.0,
    "wida": 10.0,
    "math_gap": 5.0,
    "ela_gap": 10.0,
    "chronic_absenteeism": 10.0,  # 9 by rate + 1 incentive
    "alp": 2.0,
    "credit8": 3.0,
}


def main() -> int:
    r = compute("Middle", VALUES, prior_ca=10.3)
    failures = []

    if r.index != EXPECTED_INDEX:
        failures.append(f"index: got {r.index}, expected {EXPECTED_INDEX}")
    if r.stars != EXPECTED_STARS:
        failures.append(f"stars: got {r.stars}, expected {EXPECTED_STARS}")

    for comp, exp in EXPECTED_COMPONENTS.items():
        got = r.by_component.get(comp, {}).get("earned")
        if got != exp:
            failures.append(f"{comp}: got {got}, expected {exp}")

    earned_by_key = {m.key: m.earned for m in r.measures if m.applies}
    for key, exp in EXPECTED_MEASURES.items():
        got = earned_by_key.get(key)
        if got != exp:
            failures.append(f"measure {key}: got {got}, expected {exp}")

    if failures:
        print("FAIL — Amplus Durango regression:")
        for f in failures:
            print("  -", f)
        return 1

    print(f"PASS — Amplus Durango (Middle) reproduces exactly: "
          f"index {r.index}, {r.stars} stars, all components and measures match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
