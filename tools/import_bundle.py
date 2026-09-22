"""Send dist/bundle.json to the admin API. Dry run by default: nothing is written until you pass --apply.

    python tools/import_bundle.py --api https://api.example.com --token <admin access token>            # dry run
    python tools/import_bundle.py --api ... --token ... --apply [--publish]

Get a token by signing in as a content admin (POST /v1/auth/login) or from the admin console.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

from common import ROOT


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", required=True)
    ap.add_argument("--token", default=os.getenv("ADMIN_TOKEN"))
    ap.add_argument("--bundle", default=str(ROOT / "dist" / "bundle.json"))
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--publish", action="store_true", help="publish imported activities immediately")
    args = ap.parse_args()
    if not args.token:
        print("Provide --token or ADMIN_TOKEN", file=sys.stderr)
        return 2
    bundle = json.load(open(args.bundle, encoding="utf-8"))
    bundle["dry_run"] = not args.apply
    bundle["auto_publish"] = bool(args.publish)
    req = urllib.request.Request(args.api.rstrip("/") + "/v1/admin/content/bundle", data=json.dumps(bundle).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {args.token}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            report = json.load(r)
    except urllib.error.HTTPError as e:
        print(e.read().decode(), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
