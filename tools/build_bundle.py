"""Build dist/bundle.json (taxonomy + activities in one file) for the backend importer.

    python tools/build_bundle.py [--version 2026.09.1] [--out dist/bundle.json]
"""
from __future__ import annotations

import argparse
import json
from datetime import date

from common import ROOT, load_all


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default=date.today().strftime("%Y.%m.%d"))
    ap.add_argument("--out", default=str(ROOT / "dist" / "bundle.json"))
    args = ap.parse_args()
    bundle = {"version": args.version, **load_all()}
    out = __import__("pathlib").Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out} (version {args.version}: {len(bundle['skills'])} skills, {len(bundle['activities'])} activities)")


if __name__ == "__main__":
    main()
