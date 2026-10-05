"""Validate the taxonomy and every activity. Exit code 1 when anything is wrong (used by CI).

    python tools/validate.py
"""
from __future__ import annotations

import sys

from jsonschema import Draft202012Validator

from common import ROOT, load_all, read

SCORED = {"single_choice", "multi_choice", "numeric_input", "short_text", "sequence_order", "match_pairs"}


def evidence_steps(a: dict) -> list[dict]:
    """Enabled exercises that produce skill evidence: auto-scored (with a key) or rated by a parent."""
    out = []
    for st in a.get("steps", []):
        if st.get("enabled", True) is False:
            continue
        t = st.get("type")
        mode = (st.get("scoring") or {}).get("mode") or (
            "auto" if t in SCORED else "parent_rubric" if t == "parent_checklist" else "none"
        )
        if t == "parent_checklist" and mode != "none":
            out.append(st)
        elif t in SCORED and mode == "auto" and not (t == "short_text" and not (st.get("key") or {}).get("accepted")):
            out.append(st)
    return out


def check_v2(a: dict, skills: dict) -> list[str]:
    """Rules the JSON Schema cannot express (mirrors backend-api/app/services/content.py `_check_v2`)."""
    problems: list[str] = []
    steps = a.get("steps", [])
    if not any(st.get("enabled", True) for st in steps):
        problems.append("at least one exercise must be enabled")
    evidence = evidence_steps(a)
    for st in steps:
        sid, t = st.get("id"), st.get("type")
        cfg, key = st.get("config", {}), st.get("key", {})
        codes = [r["code"] for r in st.get("skills", [])]
        if len(codes) != len(set(codes)):
            problems.append(f"{sid}: skills lists a skill twice")
        for c in codes:
            if c not in skills:
                problems.append(f"{sid}: unknown skill {c}")
        mode = (st.get("scoring") or {}).get("mode")
        if mode == "auto" and t not in SCORED:
            problems.append(f"{sid}: scoring.mode 'auto' is not available for {t}")
        if mode == "parent_rubric" and t != "parent_checklist":
            problems.append(f"{sid}: scoring.mode 'parent_rubric' is only for parent_checklist")
        if st in evidence and not codes:
            problems.append(f"{sid}: a scored exercise needs at least one skill")
        if t in ("single_choice", "multi_choice"):
            opts = [o["id"] for o in cfg.get("options", [])]
            if len(opts) != len(set(opts)):
                problems.append(f"{sid}: option ids must be unique")
            if not set(key.get("correct", [])) <= set(opts):
                problems.append(f"{sid}: key.correct refers to an unknown option")
            if st in evidence and not key.get("correct"):
                problems.append(f"{sid}: a scored choice exercise needs key.correct")
        if t == "sequence_order":
            items = sorted(i["id"] for i in cfg.get("items", []))
            if sorted(key.get("correct_order", [])) != items:
                problems.append(f"{sid}: key.correct_order must list every item exactly once")
        if t == "match_pairs":
            left, right = {i["id"] for i in cfg.get("left", [])}, {i["id"] for i in cfg.get("right", [])}
            for p, q in key.get("pairs", []):
                if p not in left or q not in right:
                    problems.append(f"{sid}: pair {p},{q} refers to an unknown item")
    derived = list(dict.fromkeys(r["code"] for st in evidence for r in st.get("skills", [])))
    if not derived:
        problems.append("no exercise gives skill evidence")
    elif sorted(a.get("skills", [])) != sorted(derived):
        problems.append(f"skills {a.get('skills')} must equal the skills of its scored exercises {derived}")
    return problems


def main() -> int:
    data = load_all()
    problems: list[str] = []
    validator = Draft202012Validator(read("schemas/activity.schema.json"))
    validator_v2 = Draft202012Validator(read("schemas/activity.v2.schema.json"))
    levels = [x["code"] for x in data["levels"]]
    subjects = {x["code"] for x in data["subjects"]}
    interests = {x["code"] for x in data["interests"]}
    skills = {s["code"]: s for s in data["skills"]}

    if len(skills) != len(data["skills"]):
        problems.append("duplicate skill codes")
    for s in data["skills"]:
        if s["subject"] not in subjects or s["level"] not in levels:
            problems.append(f"skill {s['code']}: unknown subject or level")
        for p in s.get("prerequisites", []):
            if p not in skills:
                problems.append(f"skill {s['code']}: unknown prerequisite {p}")
            elif levels.index(skills[p]["level"]) > levels.index(s["level"]):
                problems.append(f"skill {s['code']}: prerequisite {p} is at a higher level")

    slugs: set[str] = set()
    for a in data["activities"]:
        where = f"activity {a.get('slug')}"
        v2 = a.get("schema_version") == 2
        for e in (validator_v2 if v2 else validator).iter_errors(a):
            problems.append(f"{where}: {'/'.join(map(str, e.path)) or '(root)'}: {e.message[:140]}")
        if v2:
            problems += [f"{where}: {p}" for p in check_v2(a, skills)]
        if a.get("slug") in slugs:
            problems.append(f"{where}: duplicate slug")
        slugs.add(a.get("slug"))
        if a.get("subject") not in subjects:
            problems.append(f"{where}: unknown subject")
        if a.get("level_from") in levels and a.get("level_to") in levels and levels.index(a["level_from"]) > levels.index(a["level_to"]):
            problems.append(f"{where}: level_from above level_to")
        for c in a.get("skills", []):
            if c not in skills:
                problems.append(f"{where}: unknown skill {c}")
        for i in a.get("interests", []):
            if i not in interests:
                problems.append(f"{where}: unknown interest {i}")
        ids = [st.get("id") for st in a.get("steps", [])]
        if len(ids) != len(set(ids)):
            problems.append(f"{where}: duplicate step ids")
        if v2:
            continue
        for st in a.get("steps", []):
            if st.get("type") in ("single_choice", "multi_choice"):
                opts = {o["id"] for o in st.get("options", [])}
                if not set(st.get("correct", [])) <= opts:
                    problems.append(f"{where}/{st.get('id')}: correct refers to an unknown option")
                if st.get("scored") is not False and not st.get("correct"):
                    problems.append(f"{where}/{st.get('id')}: scored choice step without correct")
            if st.get("type") == "parent_checklist" and st.get("skill_code") not in skills:
                problems.append(f"{where}/{st.get('id')}: unknown skill_code")
        if not any(st.get("type") in SCORED or st.get("type") == "parent_checklist" for st in a.get("steps", [])):
            problems.append(f"{where}: no step can produce skill evidence")

    if problems:
        print("\n".join(problems), file=sys.stderr)
        print(f"\n{len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"OK: {len(data['skills'])} skills, {len(data['activities'])} activities ({ROOT.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
