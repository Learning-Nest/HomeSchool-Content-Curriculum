# content-curriculum

The curriculum taxonomy (levels, subjects, interests, skills) and the launch set of activities, as plain JSON files
under version control so content changes go through the same review as code.

```
taxonomy/levels.json          5 levels, L1..L5
taxonomy/subjects.json        8 subjects
taxonomy/interests.json       interest tags used for recommendations
taxonomy/skills/<SUBJECT>.json  skills per subject, with prerequisites
activities/<SUBJECT>/<slug>.json  one activity per file, format v2 (exercises own their skills; see api-contracts/docs/activity-format-v2.md)
schemas/activity.schema.json     JSON Schema for format v1 (older documents; copy of api-contracts)
schemas/activity.v2.schema.json  JSON Schema for format v2 (copy of api-contracts/schemas/activity-content.v2.schema.json)
```

## Tools (Python 3.11+, no third-party dependencies except `jsonschema` for `validate.py`)

```
python tools/validate.py                 # check every activity + the taxonomy; exit 1 on any problem (CI runs this)
python tools/build_bundle.py --version 2026.09.1   # writes dist/bundle.json (taxonomy + activities in one file)
python tools/migrate_v2.py [--write]     # one-off v1 -> v2 rewrite of activities/ (dry run by default; already-v2 files are skipped)
python tools/import_bundle.py --api https://api.example.com --token <admin access token>   # dry run by default
```

`backend-api/scripts/sync_contracts.py` copies `dist/bundle.json` into `backend-api/seed/launch-bundle.json` (the
seed data used by `python -m app.cli seed` and by the local dev server) — run `build_bundle.py` first, then that script
from the `backend-api` checkout.

## Adding or changing an activity

1. Add or edit a file under `activities/<SUBJECT>/`. Use an existing activity as a template; the exercise types and their
   fields are documented in `api-contracts/docs/activity-format-v2.md`. Give every scored exercise its own `skills`; the
   activity's top-level `skills` must equal the skills of its scored exercises (the validator tells you the list).
2. Reference only skill codes that exist in `taxonomy/skills/`. A new skill goes in the matching subject's file, with
   its `prerequisites` (skill codes must already exist — no forward references, no cycles).
3. Run `python tools/validate.py`. Fix everything it reports.
4. Open a pull request. CI runs the same check.
5. Once merged, publish it: rebuild the bundle and import it with `--apply` (add `--publish` to publish immediately,
   otherwise it lands as a draft that a content admin reviews and publishes from the admin console).

## Source of truth

Once the admin editor exists, the database is the source of truth and this repository is seed content (plus a periodic
export). Until then, edit here and import.
