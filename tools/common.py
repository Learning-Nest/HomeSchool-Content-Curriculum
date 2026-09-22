"""Shared helpers for the content tools (standard library only, plus jsonschema for validate.py)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_all() -> dict:
    skills: list = []
    for f in sorted((ROOT / "taxonomy" / "skills").glob("*.json")):
        skills += json.loads(f.read_text(encoding="utf-8"))
    activities = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((ROOT / "activities").glob("*/*.json"))]
    return {
        "levels": read("taxonomy/levels.json"),
        "subjects": read("taxonomy/subjects.json"),
        "interests": read("taxonomy/interests.json"),
        "skills": skills,
        "activities": activities,
    }
