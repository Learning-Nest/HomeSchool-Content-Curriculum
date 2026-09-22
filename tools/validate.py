"""Validate the taxonomy and every activity. Exit code 1 when anything is wrong (used by CI).

    python tools/validate.py
"""
from __future__ import annotations

import sys

from jsonschema import Draft202012Validator

from common import ROOT, load_all, read

SCORED = {"single_choice", "multi_choice", "numeric_input", "short_text", "sequence_order", "match_pairs"}


def main() -> int:
    data = load_all()
    problems: list[str] = []
    validator = Draft202012Validator(read("schemas/activity.schema.json"))
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
        for e in validator.iter_errors(a):
            problems.append(f"{where}: {'/'.join(map(str, e.path)) or '(root)'}: {e.message[:140]}")
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
