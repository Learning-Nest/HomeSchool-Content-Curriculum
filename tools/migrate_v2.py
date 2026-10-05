"""One-off migration of activities/**/*.json from format v1 to format v2 (exercises own their skills).

    python tools/migrate_v2.py            # dry run: prints what would change, writes nothing
    python tools/migrate_v2.py --write    # rewrites the files in place (git shows the diff)

Mechanical rules (identical to backend-api/app/services/content.py `upgrade_step`):
  * `text`/`prompt` -> `prompt`; option lists and layout fields -> `config`; answer fields -> `key`;
    `hint` -> `feedback.hints[0]`; `scored: false` -> `scoring.mode: "none"`; `partial_credit`/`points` -> `scoring`.
  * A parent_checklist's `skill_code` -> `skills: [{code}]`.
  * An auto-scored exercise with no skills of its own gets ALL of the activity's skills (what v1 did at run time).
  * The activity's top-level `skills` is re-derived from the exercises.
Judgement calls live in OVERRIDES below, so a reviewer sees every choice in one place.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import ROOT

AUTO = {"single_choice", "multi_choice", "numeric_input", "short_text", "sequence_order", "match_pairs"}
CONFIG = {
    "media_prompt": ("caption", "alt_text"),
    "single_choice": ("options",),
    "multi_choice": ("options",),
    "short_text": ("max_len",),
    "sequence_order": ("items",),
    "match_pairs": ("left", "right"),
    "audio_record": ("max_seconds", "consent_required"),
    "photo_evidence": ("optional", "consent_required"),
    "timer_task": ("duration_sec", "checklist"),
    "parent_checklist": ("rating_options",),
    "reflection": ("emoji_options",),
}
KEY = {
    "single_choice": ("correct",),
    "multi_choice": ("correct",),
    "numeric_input": ("answer", "tolerance"),
    "short_text": ("accepted",),
    "sequence_order": ("correct_order",),
    "match_pairs": ("pairs",),
}

# slug -> {step id -> skills that exercise should credit}. Everything not listed follows the mechanical rule.
# These split activities where two scored exercises used to share both skills; they are proposals for an educator.
OVERRIDES: dict[str, dict[str, list[str]]] = {
    "story-retell-in-3-pictures": {"s2": ["ENG.COMP.RETELL"], "s3": ["ENG.COMP.WHAT"]},
    "kitchen-counting": {"s2": ["MAT.NUM.COUNT20"]},
}


def upgrade(a: dict) -> dict:
    over = OVERRIDES.get(a["slug"], {})
    steps = []
    for st in a["steps"]:
        t = st["type"]
        out: dict = {"id": st["id"], "type": t}
        prompt = st.get("text") if t == "instruction" else st.get("prompt")
        if prompt is not None:
            out["prompt"] = prompt
        for k in ("audio_ref", "media_ref"):
            if k in st:
                out[k] = st[k]
        cfg = {k: st[k] for k in CONFIG.get(t, ()) if k in st}
        if cfg:
            out["config"] = cfg
        key = {k: st[k] for k in KEY.get(t, ()) if k in st}
        if key:
            out["key"] = key
        auto = t in AUTO and st.get("scored") is not False and not (t == "short_text" and not st.get("accepted"))
        scoring = {"mode": "auto" if auto else ("parent_rubric" if t == "parent_checklist" else "none")}
        for k in ("points", "partial_credit"):
            if k in st:
                scoring[k] = st[k]
        out["scoring"] = scoring
        if st["id"] in over:
            codes = over[st["id"]]
        elif t == "parent_checklist":
            codes = [st["skill_code"]]
        elif "skills" in st:
            codes = list(st["skills"])
        elif auto:
            codes = list(a["skills"])
        else:
            codes = []
        if codes:
            out["skills"] = [{"code": c, "weight": 1} for c in codes]
        if st.get("hint"):
            out["feedback"] = {"hints": [st["hint"]]}
        steps.append(out)
    derived = list(dict.fromkeys(r["code"] for s in steps if s["scoring"]["mode"] != "none" for r in s.get("skills", [])))
    head = {k: v for k, v in a.items() if k not in ("steps", "skills")}
    return {"schema_version": 2, **head, "skills": derived, "steps": steps}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    files = sorted((ROOT / "activities").glob("*/*.json"))
    notes: list[str] = []
    for f in files:
        a = json.loads(f.read_text(encoding="utf-8"))
        if a.get("schema_version") == 2:
            print(f"skip   {f.relative_to(ROOT)} (already v2)")
            continue
        new = upgrade(a)
        lost = [c for c in a["skills"] if c not in new["skills"]]
        if lost:
            notes.append(f"{a['slug']}: no exercise credits {', '.join(lost)}; it drops from the activity's skills")
        if args.write:
            f.write_text(json.dumps(new, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{'wrote' if args.write else 'would '} {f.relative_to(ROOT)}  skills {a['skills']} -> {new['skills']}")
    for n in notes:
        print("NEEDS DECISION:", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
