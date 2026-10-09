# How to create a new activity

This guide is for anyone who wants to add a learning activity to LearnNest. You do not need to know how the app or the
server works. You write one text file (JSON), check it with a tool, and publish it. Children then see it in the app's
Activity Library, with no new app version needed.

Time needed for your first activity: about an hour. After that, 15 to 30 minutes.

---

## 1. What is an activity?

An activity is one short lesson (5 to 20 minutes) for one child. It is made of **exercises** (called `steps` in the file),
shown one at a time. A good activity mixes:

* a short **instruction** that sets the scene,
* a few **questions** the app can mark by itself (choose, type a number, match, put in order),
* a **hands-on task** away from the screen (timer task, photo),
* a **reflection** at the end ("How did that feel?").

Questions the app can mark feed the child's progress: each one is linked to the **skill** it tests (for example
`MAT.SHAPE.2D` = "Names basic 2D shapes"). That is how the dashboard knows what a child can do.

---

## 2. The short version (7 steps)

1. Pick the **subject**, the **level** (L1 to L5) and the **skill(s)** you want to test (section 4).
2. Copy an existing activity as a starting point: `activities/<SUBJECT>/<some-activity>.json`.
3. Save it as a new file named after your slug: `activities/<SUBJECT>/<your-slug>.json`.
4. Edit the fields (sections 5 and 6).
5. Run `python tools/validate.py` and fix every message (section 8).
6. Build and import it (section 9). It arrives as a **draft**.
7. Open it in the admin console, check it, and publish it.

---

## 3. Where files live

```
content-curriculum/
  activities/
    MAT/  ENG/  SCI/  SOC/  ART/  PHY/  LIF/  LNG/     one folder per subject
      shape-hunt.json                                 one activity per file
  taxonomy/
    levels.json        L1..L5
    subjects.json      the 8 subjects
    interests.json     the 12 interest tags
    skills/MAT.json    skills of each subject (ENG.json, SCI.json ...)
  tools/               validate.py, build_bundle.py, import_bundle.py
```

The file name must be the activity's `slug` plus `.json`, and it must sit in the folder of its subject.

---

## 4. Decide these first

### Subject (3 letters)

| Code | Subject |
|---|---|
| MAT | Mathematics |
| ENG | English Language & Literacy |
| LNG | Home & Regional Languages |
| SCI | Science & Nature |
| SOC | Social & Environmental Studies |
| LIF | Life Skills & Independence |
| ART | Creative Arts & Music |
| PHY | Physical Development & Health |

### Level

| Code | Name | Roughly |
|---|---|---|
| L1 | Foundation 1 | age 4 to 5 |
| L2 | Foundation 2 | age 5 to 6 |
| L3 | Early primary 1 | |
| L4 | Early primary 2 | |
| L5 | Early primary 3 | |

`level_from` and `level_to` say which levels the activity suits. Use the same level for both unless it truly works
across levels. `level_from` must not be higher than `level_to`. The Library shows an activity to a child whose level
fits this range.

### Skills

Every question that is marked must name at least one skill. Skill codes look like `MAT.SHAPE.2D` (subject, area,
skill). **You may only use codes that already exist** in `taxonomy/skills/<SUBJECT>.json`. To see what exists for maths:

```powershell
python -c "import json; [print(s['code'], '-', s['level'], '-', s['name']) for s in json.load(open('taxonomy/skills/MAT.json'))]"
```

(Change `MAT` for another subject.) Pick skills at or near the activity's level. If the skill you need does not exist, see
section 10.

### Interests (optional)

Tags used to recommend activities. Use only these: `animals`, `space`, `dinosaurs`, `vehicles`, `cooking`, `music`,
`art`, `nature`, `sports`, `stories`, `building`, `dance`. An unknown tag fails validation.

### Slug

A short, unique name in lower case with hyphens: `shape-hunt`, `count-the-fruit`. Letters, digits and single hyphens
only. **A slug can never be changed after the activity exists**, so choose it carefully.

---

## 5. The fields of the file

```json
{
  "schema_version": 2,
  "slug": "count-the-fruit",
  "title": "Count the fruit",
  "subject": "MAT",
  "level_from": "L1",
  "level_to": "L1",
  "duration_min": 10,
  "materials": ["3 to 10 pieces of fruit or small toys"],
  "interests": ["cooking"],
  "summary": "Count fruit on the screen, then count real fruit at home.",
  "recurring": false,
  "skills": ["MAT.NUM.COUNT20"],
  "steps": [ ... ]
}
```

| Field | Required | What to write |
|---|---|---|
| `schema_version` | yes | Always `2`. |
| `slug` | yes | Unique, permanent, see above. |
| `title` | yes | What parents and children see. Up to 120 characters. |
| `subject` | yes | One of the 8 codes. |
| `level_from`, `level_to` | yes | `L1` to `L5`. |
| `duration_min` | yes | Whole minutes, 1 to 180. Be honest: 10 to 20 is typical. |
| `skills` | yes | The skills of all marked questions, see the rule below. |
| `steps` | yes | 1 to 40 exercises. Aim for 5 to 8. |
| `summary` | no | One or two friendly sentences for parents (up to 400 characters). |
| `materials` | no | What the family needs, as a list of short phrases. Empty `[]` if nothing. |
| `interests` | no | Tags from the list above. |
| `recurring` | no | `true` if it is a habit to repeat (a weather diary), otherwise `false`. |
| `authoring` | no | Private notes for editors (`notes`, `educator_reviewed`, `reviewed_by`). Never shown to children. |

**The `skills` rule:** the top-level `skills` list must be exactly the set of skills used by the exercises that are
marked. You do not have to work this out yourself: run the validator, and if it differs it prints the correct list for
you to copy.

---

## 6. Exercises (the `steps`)

Every exercise has the same outer shape:

```json
{
  "id": "s2",
  "type": "numeric_input",
  "prompt": "How many apples? 🍎🍎🍎🍎",
  "config": { },
  "key": { "answer": 4, "tolerance": 0 },
  "scoring": { "mode": "auto" },
  "skills": [ { "code": "MAT.NUM.COUNT20", "weight": 1 } ],
  "feedback": { "hints": ["Point at each 🍎 once as you count."] }
}
```

| Part | What it is |
|---|---|
| `id` | A short unique name inside this activity: `s1`, `s2` ... Letters, digits, `-` or `_`. Answers are saved under this id, so **never reuse or renumber an id** after the activity is published. |
| `type` | The kind of exercise (table below). |
| `prompt` | The text the child sees. Short and friendly. |
| `config` | What the child sees besides the prompt: options, items, timer. Sent to the app. |
| `key` | The correct answer. **Never sent to the app**, so a child cannot see it. |
| `scoring` | `{"mode": "auto"}` if the app marks it, `{"mode": "none"}` if it is not marked. |
| `skills` | Which skills this question tests, with a `weight` from above 0 up to 1. Only for marked exercises. |
| `feedback` | `hints`: the first hint is shown if the child needs help. Other feedback fields are stored but not used yet. |
| `enabled` | Optional. `false` hides the exercise from children but keeps it in the file. |

### The exercise types

**Marked by the app (`"scoring": {"mode": "auto"}`)**

| type | The child... | `config` | `key` |
|---|---|---|---|
| `single_choice` | picks one answer | `options`: 2 to 8 items `{ "id": "o1", "label": "..." }` | `{ "correct": ["o2"] }` |
| `multi_choice` | picks all the right answers | `options` | `{ "correct": ["o1","o3"] }`; add `"partial_credit": true` in `scoring` to give part marks |
| `numeric_input` | types a number | none | `{ "answer": 4, "tolerance": 0 }` |
| `short_text` | types a short word | `{ "max_len": 20 }` | `{ "accepted": ["cat","kitten"] }` (not case sensitive; if empty the answer is not marked) |
| `sequence_order` | puts things in order | `items`: `{ "id": "i1", "label": "..." }` | `{ "correct_order": ["i1","i2","i3"] }` (every item exactly once) |
| `match_pairs` | joins left to right | `left` and `right` lists of `{id,label}` | `{ "pairs": [["l1","r1"],["l2","r2"]] }` |

`correct` is always a **list**, even for single choice.

**Not marked by the app (`"scoring": {"mode": "none"}`)**

| type | Use it for | `config` |
|---|---|---|
| `instruction` | Introducing the activity or a step ("Today we will...") | none |
| `media_prompt` | A picture with a caption (needs `caption` and `alt_text`) | `{ "caption": "...", "alt_text": "..." }` |
| `timer_task` | A hands-on task away from the screen | `{ "duration_sec": 300, "checklist": ["...", "..."] }` |
| `audio_record` | The child records their voice | `{ "max_seconds": 30, "consent_required": true }` |
| `photo_evidence` | A photo of real work | `{ "optional": true, "consent_required": true }` |
| `reflection` | "How was it?" with emoji | `{ "emoji_options": ["😊","😐","😢"] }` |
| `parent_checklist` | A parent rates what they saw (`"mode": "parent_rubric"`, needs a skill) | `{ "rating_options": [...] }` |

### Weights

`weight` says how much an answer counts for a skill. Use `1` normally. Use `0.5` when a question only partly tests a
skill (for example a counting question that also involves shapes: counting weight 1, shape weight 0.5). A question can
list several skills; it never counts for a skill it does not list.

### Writing for children

* One idea per exercise. Prompts under about 15 words.
* Emoji make good option labels for young children (🔵 🟦 🔺 🍎). Check that every emoji looks clear on a phone.
* Put one hands-on exercise in every activity where you can: it is what makes homeschooling different from a screen.
* Give a hint to every marked question. Hints should help the child think, not give the answer.
* Wrong answers (distractors) should be plausible but clearly wrong to a child who has learned the skill.
* End with a reflection. It costs nothing and children like it.

---

## 7. A complete small example

This file is valid. Save it as `activities/MAT/count-the-fruit.json`, or use it as a template.

```json
{
  "schema_version": 2,
  "slug": "count-the-fruit",
  "title": "Count the fruit",
  "subject": "MAT",
  "level_from": "L1",
  "level_to": "L1",
  "duration_min": 10,
  "materials": ["3 to 10 pieces of fruit or small toys"],
  "interests": ["cooking"],
  "summary": "Count fruit on the screen, then count real fruit at home.",
  "recurring": false,
  "skills": ["MAT.NUM.COUNT20"],
  "steps": [
    {
      "id": "s1",
      "type": "instruction",
      "prompt": "Today we are counting fruit! Touch each one as you count.",
      "scoring": { "mode": "none" }
    },
    {
      "id": "s2",
      "type": "numeric_input",
      "prompt": "How many apples? 🍎🍎🍎🍎",
      "key": { "answer": 4, "tolerance": 0 },
      "scoring": { "mode": "auto" },
      "skills": [ { "code": "MAT.NUM.COUNT20", "weight": 1 } ],
      "feedback": { "hints": ["Point at each 🍎 once as you count."] }
    },
    {
      "id": "s3",
      "type": "single_choice",
      "prompt": "Which group has 3 bananas?",
      "config": {
        "options": [
          { "id": "o1", "label": "🍌🍌" },
          { "id": "o2", "label": "🍌🍌🍌" },
          { "id": "o3", "label": "🍌🍌🍌🍌🍌" }
        ]
      },
      "key": { "correct": ["o2"] },
      "scoring": { "mode": "auto" },
      "skills": [ { "code": "MAT.NUM.COUNT20", "weight": 1 } ],
      "feedback": { "hints": ["Count each group out loud."] }
    },
    {
      "id": "s4",
      "type": "timer_task",
      "prompt": "Now count real fruit at home!",
      "config": {
        "duration_sec": 180,
        "checklist": ["Put some fruit on the table", "Count them out loud", "Tell a grown-up how many"]
      },
      "scoring": { "mode": "none" }
    },
    {
      "id": "s5",
      "type": "reflection",
      "prompt": "How did counting feel?",
      "config": { "emoji_options": ["😊", "😐", "😢"] },
      "scoring": { "mode": "none" }
    }
  ]
}
```

What to notice: only `s2` and `s3` are marked, so only they have `skills`, a `key` and `"mode": "auto"`. The top-level
`skills` equals the skills those two exercises use. The other three have `"mode": "none"` and no key.

A larger real example is `activities/MAT/shape-hunt.json`, which uses eight exercises and six different types.

---

## 8. Check it

From the `content-curriculum` folder:

```powershell
pip install -U jsonschema        # once
python tools/validate.py
```

You want to see a line like `OK: 51 skills, 16 activities`. If not, each message names the activity (and exercise) and
the problem. The common ones:

| Message | What to do |
|---|---|
| `unknown skill X` | The code does not exist, or is mistyped. Look it up in `taxonomy/skills/`. |
| `unknown interest X` | Use only the 12 interest tags in section 4. |
| `unknown subject` | Use a code from the subject table. |
| `level_from above level_to` | Swap them. |
| `skills [...] must equal the skills of its scored exercises [...]` | Copy the second list into the top-level `skills`. |
| `a scored exercise needs at least one skill` | Add a `skills` list to that exercise. |
| `scoring.mode 'auto' is not available for <type>` | That type cannot be marked by the app. Use `"mode": "none"`. |
| `key.correct refers to an unknown option` | A `correct` id does not match any option `id`. |
| `a scored choice exercise needs key.correct` | Add the `key`. |
| `key.correct_order must list every item exactly once` | List all item ids, none twice. |
| `pair ... refers to an unknown item` | Check the ids in `pairs` against `left` and `right`. |
| `duplicate slug` / `duplicate step ids` | Every slug and every exercise id must be unique. |
| `no exercise gives skill evidence` | At least one exercise must be marked, with a skill. |
| a long schema message with `steps/3` | A field is missing or the wrong shape in the exercise at that position (counting from 0). |

If the problems are all in files you did not touch, someone else's activities are failing. Fix those, or move them out
of `activities/`, before you continue: the build refuses to run on an invalid set.

---

## 9. Publish it

You need an **admin account** (role content admin or super admin) and the address of the API. For the dev environment:
`https://ca-hs-dev-api.wonderfulgrass-00be683d.centralindia.azurecontainerapps.io`.

**a) Build the bundle** (every activity plus the taxonomy in one file). Use a new version label each time, for example
the date and a counter:

```powershell
python tools/build_bundle.py --version 2026.10.2
```

**b) Get a token.** Sign in with your admin account. The password is typed at a prompt, so it is not saved anywhere:

```powershell
$api = "https://ca-hs-dev-api.wonderfulgrass-00be683d.centralindia.azurecontainerapps.io"
$pw  = Read-Host "Admin password" -AsSecureString
$plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($pw))
$body = @{ email = "YOUR-ADMIN-EMAIL"; password = $plain } | ConvertTo-Json
$env:ADMIN_TOKEN = (Invoke-RestMethod -Method Post "$api/v1/auth/login" -ContentType "application/json" -Body $body).access_token
```

The token lasts about 15 minutes. If the next step says "unauthenticated", repeat this step.

**c) Dry run.** Shows what would happen and writes nothing:

```powershell
python tools/import_bundle.py --api $api
```

Read the report. Your new activity should appear under "created" and the others under "unchanged".

**d) Import for real:**

```powershell
python tools/import_bundle.py --api $api --apply
```

The new activity arrives as a **draft**. Open the admin console, find it under Activities, check the preview, and set
its status to **published**. (Adding `--publish` publishes new activities straight away, skipping that check.)

**e) Look at it in the app.** Open the Activity Library for a child at the right level. If it is not there, see the
checklist in section 11.

### Keep the repository in step

Commit the new JSON file, open a pull request and merge it, so the repository and the live content agree.

### Pictures

Activity files in this repository cannot contain pictures yet (the checker rejects an `image` field). Pictures for
exercises, options and match items are added in the educator editor, which uploads and resizes them. Create the
activity from the file first, then open it in the editor to add pictures.

### Fixing an activity after publishing

* Imports only **add**: they never change or delete an activity that already exists. To fix a published activity, edit
  it in the admin console (this creates a new version; children already mid-activity finish on the old one), or ask a
  developer.
* To remove an activity, set its status to **archived** in the admin console. It disappears from the Library.
* The slug and each exercise `id` cannot change.

---

## 10. Adding a new skill

Only if no existing skill fits. Add an entry to `taxonomy/skills/<SUBJECT>.json`:

```json
{
  "code": "MAT.SHAPE.3D",
  "subject": "MAT",
  "level": "L2",
  "name": "Names basic 3D shapes",
  "prerequisites": ["MAT.SHAPE.2D"],
  "typical_evidence": ["activity"]
}
```

Rules: the code starts with the subject, is unique, and is never changed once used. `prerequisites` lists skills that
should come first; they must already exist, sit at the same or a lower level, and never form a loop. Run the
validator, then build and import as above. New skills are added; old ones are never deleted.

---

## 11. If the activity does not show up in the app

Work down this list:

1. Was it imported with `--apply` (not just the dry run)?
2. Is its status **published**? Drafts are invisible to families.
3. Does the child's level fall between `level_from` and `level_to`?
4. Is the app pointed at the same environment you imported into (dev, nonprod or prod)?
5. Close and reopen the Library screen so it reloads. A new app version is not needed.

---

## 12. Before you submit: checklist

- [ ] File is in `activities/<SUBJECT>/` and named `<slug>.json`.
- [ ] `python tools/validate.py` prints OK.
- [ ] Every marked question has a hint, a key, `"mode": "auto"` and at least one skill.
- [ ] At least one exercise is marked, so the activity produces progress.
- [ ] There is a hands-on task or a reflection (ideally both).
- [ ] Duration and materials are realistic for a parent at home.
- [ ] Wording is friendly, short and correct. Answers are right.
- [ ] A second person has played through it on a phone.

---

## Where to read more

* `api-contracts/docs/activity-format-v2.md` is the technical reference: every rule the server applies.
* `content-curriculum/README.md` lists the tools.
* The official schema is `api-contracts/schemas/activity-content.v2.schema.json`.
