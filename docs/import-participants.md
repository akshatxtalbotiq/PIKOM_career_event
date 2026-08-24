# Importing participants from a spreadsheet

`register/management/commands/import_participants.py` loads an Excel export of
registrations-of-interest into an existing registration form. It writes to the
same two tables the public form writes to, and nothing else:

| Table | What goes in |
|---|---|
| `register_surveyuser` | one row per participant — `name`, `email`, `phone`, `organization`, `participant_type`, `approval_status`, `reg_no`, `created_at` |
| `register_answer` | one row per participant per non-identity question answered — `answer_text` for text questions, `selected_options` for choice questions |

`reg_no` is assigned as `REG%06d` from the new row's id, exactly as
`form_submit()` does, so imported and self-service registrations are
indistinguishable in the registrations list.

**No email is sent by the import.** Rows land as `pending`, so no QR codes or
confirmations go out until someone approves them in the UI.

## Target: campaign 8 → form 5

| | |
|---|---|
| Campaign | **8 — GBS Global Summit 2026** |
| Registration form | **5 — Delegate Registration** (`/event/gbs-global-summit-2026-delegate-registration/`) |
| Already on that form | 12 participants (all `@pikom.org.my` / `@gbsmalaysia.org.my`) |

`--campaign 8` finds form 5 on its own. None of the 56 spreadsheet emails
clash with the 12 already there, so nothing existing is touched.

## Column mapping

For `Event Registration of Interest_21Aug2026.xlsx` (63 rows):

| Spreadsheet column | Goes to |
|---|---|
| `Name` | `surveyuser.name` |
| `Email` | `surveyuser.email` |
| `Contact No.` | `surveyuser.phone` |
| `Organization` | `surveyuser.organization` |
| `Designation` | answer to **Job Title** (Q4, open text) |
| `Is your organisation a registered member of PIKOM or GBS Malaysia?` | answer to **Please select your Category: I am:** (Q7, single choice) |
| `Timestamp` | `surveyuser.created_at`, read as GMT+8 and stored as UTC |

Questions are matched by wording, ignoring case and line breaks, so Q7's
two-line text matches fine. Any other spreadsheet column is ignored. To map
more, edit `IDENTITY_COLUMNS` / `QUESTION_COLUMNS` at the top of the command —
that is the only place the mapping lives.

**Q8 "Personal Data" is left unanswered.** It is the PDPA consent checkbox, and
the spreadsheet has no consent column — these people filled in a different
form, so the import does not record a declaration they never made. Ticking it
for everyone would need `QUESTION_COLUMNS` extended deliberately.

### The category values need a decision

The form's Q7 offers *PIKOM Member*, *GBS Malaysia Member*, *Other PIKOM
Chapter Member*, *Attending by Invitation…*, *Non-Member (RM499 per person)*.
The spreadsheet uses four different labels:

| Spreadsheet answer | Rows | Imported as |
|---|---|---|
| `Yes, PIKOM member` | 27 | **PIKOM Member** (mapped automatically) |
| `Yes, GBS Malaysia member` | 8 | **GBS Malaysia Member** (mapped automatically) |
| `Member of both` | 7 | stored as-is unless you map it |
| `Not a member` | 14 | stored as-is unless you map it |

The last two have no clean equivalent, and *Non-Member* carries a RM499 fee, so
the command will not assume. It stores the original wording and prints a `?`
line telling you how many. To fold them into the form's own options, add:

```
--map "Member of both=GBS Malaysia Member" --map "Not a member=Non-Member (RM499 per person)"
```

An unmapped value still imports and still shows in the list; it just won't
match the form's choices if someone edits that entry later.

---

## Step 1 — Terminal, virtualenv, file in place

Open a terminal in the project root (next to `manage.py`) and activate the
virtualenv you use for `runserver`. Copy the `.xlsx` into the project root, or
note its full path.

`openpyxl==3.1.5` is already in `requirements.txt`. If the command says it is
missing: `pip install openpyxl==3.1.5`.

## Step 2 — Confirm the target form

```
python manage.py shell -c "from register.models import Campaign; c=Campaign.objects.get(pk=8); print(c.title); [print('  form', s.id, '|', s.title, '|', s.questions.count(), 'questions') for s in c.surveys.all()]"
```

Expected:

```
GBS Global Summit 2026
  form 5 | Delegate Registration | 8 questions
```

If it prints no form, create one first (**Registration Forms → + New
Registration Form**, *Assign to Campaign* = campaign 8). If it prints more than
one, use `--survey 5` instead of `--campaign 8`; the command lists the ids if
you forget.

## Step 3 — Dry run

```
python manage.py import_participants --file "Event Registration of Interest_21Aug2026.xlsx" --campaign 8 --dry-run
```

Everything runs inside a transaction that is then rolled back, so this is safe
to repeat as often as you like. Expect:

```
Form   : #5 Delegate Registration
Campaign: #8 GBS Global Summit 2026
Sheet  : Event Registration of Interest (63 data rows)
  + REG0000xx  Rose Allarde <rose@net2source.my>
  ... 56 of these ...
  ~ row 16 duplicate email, skipped: ...   (7 of these)
  ? 14 row(s) answered 'Not a member', ...
  ? 7 row(s) answered 'Member of both', ...
participants: 56 created, 7 skipped, 0 failed
answers     : 112 rows
DRY RUN — everything above was rolled back.
```

## Step 4 — Read the report

| Line | Meaning |
|---|---|
| `+ REG0000xx  Name <email>` | will be created |
| `~ row 16 duplicate email, skipped` | that email already exists on the form, or appeared earlier in the file |
| `? 14 row(s) answered '…'` | choice value that isn't one of the form's options; add `--map` if you want it folded in |
| `! row 12 no email` | cannot be imported — fix the sheet, or use the matching flag |

**This file has 7 repeat submissions** — the same email twice, people who
submitted the form again. The default keeps the first and skips the rest, which
is why 63 rows become 56 participants. `--on-duplicate import` loads all 63.

If any `!` line appears, the command exits non-zero and the whole import is
rolled back. It is all-or-nothing; you can never end up with half a file
loaded.

## Step 5 — Back up, then run it

```
mysqldump -u root -p picom > picom_before_import.sql

python manage.py import_participants --file "Event Registration of Interest_21Aug2026.xlsx" --campaign 8 \
    --map "Member of both=GBS Malaysia Member" \
    --map "Not a member=Non-Member (RM499 per person)"
```

Drop the `--map` flags if you would rather keep the original wording. Add
`--limit 3` for a cautious first pass — the remaining rows import on the next
run, since the three already loaded are then skipped as duplicates.

## Step 6 — Check the result

UI: **Campaigns → the eye icon on GBS Global Summit 2026**. The count goes from
12 to 68. Imported rows show their `REG…` number, *Pending* status, and Job
Title / Member Status as list columns.

Shell:

```
python manage.py shell -c "from register.models import *; s=Survey.objects.get(pk=5); print(s.survey_users.count(), 'participants'); print(Answer.objects.filter(survey=s).count(), 'answers')"
```

---

## Options

| Flag | Default | What it does |
|---|---|---|
| `--file` | required | Path to the `.xlsx`. |
| `--campaign` | — | Campaign id; uses that campaign's registration form. |
| `--survey` | — | Target the form directly by id. |
| `--sheet` | first sheet | Worksheet name. |
| `--dry-run` | off | Do everything, report, roll back. |
| `--map FROM=TO` | — | Rewrite a choice answer. Repeatable. |
| `--on-duplicate` | `skip` | `skip` or `import` rows whose email already exists. |
| `--status` | `pending` | `pending`, `approved` or `rejected` for imported rows. |
| `--participant-type` | `Delegate` | Organizer / Delegate / Sponsor / Exhibitor / Speaker. |
| `--create-questions` | off | Create a question column missing from the form instead of failing. Not needed for form 5. |
| `--ignore-timestamp` | off | Use *now* for `created_at` instead of the Timestamp column. |
| `--tz-offset` | `+08:00` | Timezone for timestamps with no offset of their own. |
| `--allow-invalid-email` | off | Import rows whose email fails validation. |
| `--limit N` | — | Only process the first N data rows. |

## Undoing an import

`Answer.user` is `on_delete=SET_NULL`, so deleting participants first would
leave orphaned answer rows. Delete the answers first:

```
python manage.py shell
```

```python
from register.models import Answer, SurveyUser

rows = SurveyUser.objects.filter(survey_id=5, reg_no__gte="REG000xxx", reg_no__lte="REG000yyy")
print(rows.count())                      # sanity-check before deleting
Answer.objects.filter(user__in=rows).delete()
rows.delete()
```

Use the first and last `REG…` numbers the run printed. Restoring
`picom_before_import.sql` is the blunt alternative.

## Notes on this data set

- **Phone numbers are inconsistent at source** — some carry the `60` country
  code, some do not (`178783743` vs `60124746605`). The import stores them as
  they are rather than guessing; normalise in the spreadsheet first if you want
  them uniform.
- **Designation and Organization** arrive with trailing and non-breaking spaces
  from the form export; the import trims and collapses whitespace.
- **Timestamps** are read as GMT+8 (as exported) and stored in UTC, matching
  `settings.TIME_ZONE`, so the list shows the original submission time.
- Every imported row gets `participant_type = Delegate`. Change with
  `--participant-type`, or edit individuals in the UI afterwards.
