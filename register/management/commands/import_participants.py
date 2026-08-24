"""Import participants from an Excel export into a registration form.

Rows land in exactly two tables, the same two the public form writes to:

    register_surveyuser  — one row per participant (identity fields)
    register_answer      — one row per non-identity question answered

Usage (see docs/import-participants.md for the full walkthrough):

    python manage.py import_participants \
        --file "Event Registration of Interest_21Aug2026.xlsx" \
        --campaign 8 --dry-run

Nothing is written until you drop --dry-run.
"""

from datetime import datetime, timedelta, timezone as dt_timezone
import re

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction

from register.models import Answer, Campaign, Question, Survey, SurveyUser


# ── Column mapping ───────────────────────────────────────────────────────────
# Spreadsheet header -> SurveyUser field. These are the identity fields; they
# live on the participant row itself, not in register_answer.
IDENTITY_COLUMNS = {
    "Name": "name",
    "Email": "email",
    "Contact No.": "phone",
    "Organization": "organization",
}

# Spreadsheet header -> a question on the form. Each becomes one register_answer
# row per participant. `text` is matched against the question wording on the
# form, case- and whitespace-insensitively (so a question whose text spans two
# lines still matches). `values` renames spreadsheet answers to the form's
# choices; anything not listed is stored unchanged and reported at the end.
#
# Verified against campaign 8 "GBS Global Summit 2026", form 5
# "Delegate Registration".
QUESTION_COLUMNS = [
    {
        "column": "Designation",
        "text": "Job Title",
        "type": Question.TYPE_TEXT,
        "list_label": "Job Title",
        "show_in_list": True,
    },
    {
        "column": "Is your organisation a registered member of PIKOM or GBS Malaysia?",
        "text": "Please select your Category: I am:",
        "type": Question.TYPE_RADIO,
        "list_label": "Member Status",
        "show_in_list": True,
        "choices": [
            "PIKOM Member",
            "GBS Malaysia Member",
            "Other PIKOM Chapter Member",
            "Attending by Invitation * (Partners, Associations, Academia, GLCs, Ministries)",
            "Non-Member (RM499 per person)",
        ],
        # The two unambiguous ones. "Member of both" and "Not a member" have no
        # clean equivalent on the form (and "Non-Member" carries a fee), so they
        # are left as the registrant wrote them unless you say otherwise with
        # --map "Member of both=GBS Malaysia Member".
        "values": {
            "Yes, PIKOM member": "PIKOM Member",
            "Yes, GBS Malaysia member": "GBS Malaysia Member",
        },
    },
]

# Column holding the submission time. Optional — see --ignore-timestamp.
TIMESTAMP_COLUMN = "Timestamp"

# Field lengths from register.models, so we truncate instead of blowing up.
MAX_LENGTHS = {"name": 500, "email": 254, "phone": 50, "organization": 500}


def clean(value):
    """Excel cells arrive as str/int/float/None with stray NBSPs and padding."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    text = str(value)
    text = text.replace("\xa0", " ").replace("​", "")
    return re.sub(r"\s+", " ", text).strip()


class Command(BaseCommand):
    help = "Import participants from an .xlsx export into register_surveyuser and register_answer."

    def add_arguments(self, parser):
        parser.add_argument("--file", required=True, help="Path to the .xlsx file.")
        parser.add_argument("--sheet", default=None, help="Worksheet name (default: the first sheet).")
        parser.add_argument(
            "--campaign", type=int, default=None,
            help="Campaign id. The command uses that campaign's registration form.",
        )
        parser.add_argument(
            "--survey", type=int, default=None,
            help="Registration form (Survey) id. Use this instead of --campaign, "
                 "or alongside it when a campaign has more than one form.",
        )
        parser.add_argument(
            "--participant-type", default=SurveyUser.PARTICIPANT_TYPE_DELEGATE,
            choices=[c[0] for c in SurveyUser.PARTICIPANT_TYPE_CHOICES],
            help="Participant type given to every imported row (default: Delegate).",
        )
        parser.add_argument(
            "--status", default=SurveyUser.STATUS_PENDING,
            choices=[c[0] for c in SurveyUser.STATUS_CHOICES],
            help="Approval status for imported rows (default: pending, same as a public submission).",
        )
        parser.add_argument(
            "--on-duplicate", default="skip", choices=["skip", "import"],
            help="What to do with an email already on this form, or repeated inside the file "
                 "(default: skip).",
        )
        parser.add_argument(
            "--create-questions", action="store_true",
            help="Create any question column missing from the form instead of failing.",
        )
        parser.add_argument(
            "--tz-offset", default="+08:00",
            help="Timezone of the Timestamp column when it carries no offset (default: +08:00).",
        )
        parser.add_argument(
            "--ignore-timestamp", action="store_true",
            help="Let created_at default to now instead of the spreadsheet Timestamp.",
        )
        parser.add_argument(
            "--allow-invalid-email", action="store_true",
            help="Import rows whose email fails validation instead of reporting them.",
        )
        parser.add_argument(
            "--map", action="append", default=[], metavar="FROM=TO",
            help="Rewrite a choice answer, e.g. --map \"Member of both=GBS Malaysia Member\". "
                 "Repeatable. Applied to every choice column.",
        )
        parser.add_argument("--limit", type=int, default=None, help="Only process the first N data rows.")
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Do everything, report, then roll back. Nothing is saved.",
        )

    # ── helpers ──────────────────────────────────────────────────────────────
    def resolve_survey(self, campaign_id, survey_id):
        if survey_id:
            try:
                survey = Survey.objects.get(pk=survey_id)
            except Survey.DoesNotExist:
                raise CommandError(f"No registration form (Survey) with id {survey_id}.")
            if campaign_id and survey.fkcampaign_id != campaign_id:
                raise CommandError(
                    f"Form {survey_id} ('{survey.title}') belongs to campaign "
                    f"{survey.fkcampaign_id}, not {campaign_id}. Drop --campaign or fix the id."
                )
            return survey

        if not campaign_id:
            raise CommandError("Give either --campaign or --survey.")

        try:
            campaign = Campaign.objects.get(pk=campaign_id)
        except Campaign.DoesNotExist:
            raise CommandError(f"No campaign with id {campaign_id}.")

        forms = list(
            campaign.surveys.filter(purpose=Survey.PURPOSE_REGISTRATION).order_by("-created_at")
        )
        if not forms:
            raise CommandError(
                f"Campaign {campaign_id} ('{campaign.title}') has no registration form yet, and "
                "participants must hang off one.\n"
                "Create it first: Registration Forms -> + New Registration Form -> "
                f"Assign to Campaign = '{campaign.title}'. Then re-run this command."
            )
        if len(forms) > 1:
            listing = "\n".join(f"    --survey {f.id}   {f.title}" for f in forms)
            raise CommandError(
                f"Campaign {campaign_id} has {len(forms)} registration forms. "
                f"Pick one:\n{listing}"
            )
        return forms[0]

    def resolve_questions(self, survey, create_missing):
        """Map each question column to a Question row on this form."""
        existing = {}
        for q in survey.questions.exclude(question_type__in=Question.IDENTITY_TYPES.keys()):
            existing.setdefault(clean(re.sub(r"<[^>]+>", "", q.text)).lower(), q)

        resolved, missing = [], []
        next_number = (survey.questions.order_by("-number").values_list("number", flat=True).first() or 0) + 1

        for spec in QUESTION_COLUMNS:
            question = existing.get(clean(spec["text"]).lower())
            if question is None:
                if not create_missing:
                    missing.append(spec["text"])
                    continue
                question = Question.objects.create(
                    survey=survey,
                    number=next_number,
                    text=spec["text"],
                    question_type=spec["type"],
                    choices=spec.get("choices"),
                    is_required=False,
                    show_in_list=spec.get("show_in_list", False),
                    list_column_label=spec.get("list_label", "")[:60],
                )
                next_number += 1
                self.stdout.write(self.style.WARNING(
                    f"  created question #{question.number}: {spec['text'][:60]}"
                ))
            elif question.question_type != spec["type"]:
                self.stdout.write(self.style.WARNING(
                    f"  note: '{spec['text'][:40]}' is {question.question_type} on the form, "
                    f"the importer expected {spec['type']} — writing it as {question.question_type}."
                ))
            resolved.append((spec, question))

        if missing:
            raise CommandError(
                "These columns have no matching question on the form:\n"
                + "".join(f"    - {m}\n" for m in missing)
                + "Add them in Form Builder (the wording must match), or re-run with --create-questions."
            )
        return resolved

    def parse_timestamp(self, raw, offset_minutes):
        """'2026/08/05 9:53:28 AM GMT+8' (or a real Excel datetime) -> aware datetime."""
        if isinstance(raw, datetime):
            naive = raw
            tz = dt_timezone(timedelta(minutes=offset_minutes))
            return naive.replace(tzinfo=tz) if naive.tzinfo is None else naive

        text = clean(raw)
        if not text:
            return None

        tz = dt_timezone(timedelta(minutes=offset_minutes))
        gmt = re.search(r"GMT\s*([+-])\s*(\d{1,2})(?::?(\d{2}))?$", text, re.I)
        if gmt:
            sign = 1 if gmt.group(1) == "+" else -1
            mins = int(gmt.group(2)) * 60 + int(gmt.group(3) or 0)
            tz = dt_timezone(timedelta(minutes=sign * mins))
            text = text[: gmt.start()].strip()

        for fmt in ("%Y/%m/%d %I:%M:%S %p", "%Y/%m/%d %H:%M:%S",
                    "%d/%m/%Y %I:%M:%S %p", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).replace(tzinfo=tz)
            except ValueError:
                continue
        return None

    @staticmethod
    def parse_offset(value):
        m = re.fullmatch(r"([+-])(\d{1,2}):?(\d{2})?", (value or "").strip())
        if not m:
            raise CommandError(f"--tz-offset must look like +08:00, got '{value}'.")
        sign = 1 if m.group(1) == "+" else -1
        return sign * (int(m.group(2)) * 60 + int(m.group(3) or 0))

    # ── main ─────────────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        try:
            import openpyxl
        except ImportError:
            raise CommandError("openpyxl is required: pip install openpyxl==3.1.5")

        offset_minutes = self.parse_offset(options["tz_offset"])

        cli_values = {}
        for pair in options["map"]:
            if "=" not in pair:
                raise CommandError(f'--map needs FROM=TO, got "{pair}"')
            source, target = pair.split("=", 1)
            cli_values[clean(source).lower()] = clean(target)

        try:
            workbook = openpyxl.load_workbook(options["file"], data_only=True, read_only=True)
        except FileNotFoundError:
            raise CommandError(f"File not found: {options['file']}")
        sheet = workbook[options["sheet"]] if options["sheet"] else workbook.worksheets[0]

        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            raise CommandError("The sheet is empty.")

        header = {clean(cell): idx for idx, cell in enumerate(rows[0]) if clean(cell)}
        required = list(IDENTITY_COLUMNS) + [spec["column"] for spec in QUESTION_COLUMNS]
        absent = [name for name in required if name not in header]
        if absent:
            raise CommandError(
                "The sheet is missing these columns:\n"
                + "".join(f"    - {a}\n" for a in absent)
                + "Found: " + ", ".join(header) + "\n"
                "Fix the header row, or edit IDENTITY_COLUMNS / QUESTION_COLUMNS in this command."
            )

        data_rows = rows[1:]
        if options["limit"]:
            data_rows = data_rows[: options["limit"]]

        survey = self.resolve_survey(options["campaign"], options["survey"])
        campaign = survey.fkcampaign
        self.stdout.write(
            f"Form   : #{survey.id} {survey.title}\n"
            f"Campaign: #{getattr(campaign, 'id', '-')} {getattr(campaign, 'title', '(none)')}\n"
            f"Sheet  : {sheet.title} ({len(data_rows)} data rows)\n"
        )

        created, skipped, failed = [], [], []
        answers_written = 0
        unmatched = {}

        try:
            with transaction.atomic():
                question_map = self.resolve_questions(survey, options["create_questions"])

                seen_emails = {
                    (e or "").strip().lower()
                    for e in SurveyUser.objects.filter(survey=survey).values_list("email", flat=True)
                    if e
                }

                for offset, row in enumerate(data_rows, start=2):  # row 1 is the header
                    def cell(column):
                        index = header[column]
                        return row[index] if index < len(row) else None

                    if not any(clean(value) for value in row):
                        continue  # blank spacer row

                    identity = {
                        field: clean(cell(column))[: MAX_LENGTHS[field]]
                        for column, field in IDENTITY_COLUMNS.items()
                    }

                    if not identity["name"]:
                        failed.append((offset, "no name"))
                        continue

                    email_key = identity["email"].lower()
                    if not email_key:
                        failed.append((offset, "no email"))
                        continue
                    try:
                        validate_email(identity["email"])
                    except ValidationError:
                        if not options["allow_invalid_email"]:
                            failed.append((offset, f"invalid email '{identity['email']}'"))
                            continue

                    if email_key in seen_emails and options["on_duplicate"] == "skip":
                        skipped.append((offset, identity["name"], identity["email"]))
                        continue

                    participant = SurveyUser.objects.create(
                        survey=survey,
                        name=identity["name"],
                        email=identity["email"],
                        phone=identity["phone"],
                        organization=identity["organization"],
                        participant_type=options["participant_type"],
                        approval_status=options["status"],
                    )
                    # Same reference-number scheme the public form uses.
                    participant.reg_no = f"REG{participant.id:06d}"
                    participant.save(update_fields=["reg_no"])

                    if options["status"] == SurveyUser.STATUS_APPROVED:
                        SurveyUser.objects.filter(pk=participant.pk).update(
                            approved_at=participant.created_at
                        )

                    # created_at is auto_now_add, so the spreadsheet time has to
                    # be written with an UPDATE rather than on create().
                    if not options["ignore_timestamp"] and TIMESTAMP_COLUMN in header:
                        stamp = self.parse_timestamp(cell(TIMESTAMP_COLUMN), offset_minutes)
                        if stamp:
                            SurveyUser.objects.filter(pk=participant.pk).update(created_at=stamp)
                        else:
                            self.stdout.write(self.style.WARNING(
                                f"  row {offset}: unreadable timestamp "
                                f"'{clean(cell(TIMESTAMP_COLUMN))}' — left as now()"
                            ))

                    for spec, question in question_map:
                        value = clean(cell(spec["column"]))
                        if not value:
                            continue
                        # Spreadsheet wording -> the form's own choice labels.
                        lookup = {clean(k).lower(): v for k, v in (spec.get("values") or {}).items()}
                        lookup.update(cli_values)
                        value = lookup.get(value.lower(), value)

                        payload = {"survey": survey, "question": question, "user": participant}
                        if question.question_type in (Question.TYPE_RADIO, Question.TYPE_SELECT):
                            payload["selected_options"] = [value]
                            choices = question.choices or spec.get("choices") or []
                            if choices and value not in choices:
                                unmatched[value] = unmatched.get(value, 0) + 1
                        elif question.question_type == Question.TYPE_CHECKBOX:
                            payload["selected_options"] = [
                                part.strip() for part in re.split(r"[;,]", value) if part.strip()
                            ]
                        else:
                            payload["answer_text"] = value
                        Answer.objects.create(**payload)
                        answers_written += 1

                    seen_emails.add(email_key)
                    created.append((offset, participant.reg_no, identity["name"], identity["email"]))

                if options["dry_run"]:
                    transaction.set_rollback(True)
        except Exception:
            raise

        # ── report ───────────────────────────────────────────────────────────
        for _, reg_no, name, email in created:
            self.stdout.write(f"  + {reg_no}  {name} <{email}>")
        for offset, name, email in skipped:
            self.stdout.write(self.style.WARNING(f"  ~ row {offset} duplicate email, skipped: {name} <{email}>"))
        for offset, reason in failed:
            self.stdout.write(self.style.ERROR(f"  ! row {offset} {reason}"))

        self.stdout.write("")
        for value, count in sorted(unmatched.items(), key=lambda kv: -kv[1]):
            self.stdout.write(self.style.WARNING(
                f"  ? {count} row(s) answered '{value}', which is not one of the form's choices — "
                f"stored as-is. Use --map \"{value}=<one of the form's options>\" to change that."
            ))
        self.stdout.write(
            f"participants: {len(created)} created, {len(skipped)} skipped, {len(failed)} failed\n"
            f"answers     : {answers_written} rows"
        )
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN — everything above was rolled back."))
        else:
            self.stdout.write(self.style.SUCCESS("Import committed."))

        if failed:
            raise CommandError(f"{len(failed)} row(s) could not be imported — see the ! lines above.")
