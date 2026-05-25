"""
For every registration-form Survey that doesn't yet have identity_* questions,
create them from Survey.identity_field_config (visible entries only) and shift
existing custom-question numbers up so the identity questions come first.

After this migration, identity fields are first-class Question rows and the
identity_field_config JSON is effectively legacy.
"""
from django.db import migrations


DEFAULT_CONFIG = [
    {"key": "name",         "label": "Name",         "visible": True, "required": True},
    {"key": "email",        "label": "Email",        "visible": True, "required": True},
    {"key": "phone",        "label": "Phone",        "visible": True, "required": False},
    {"key": "organization", "label": "Organization", "visible": True, "required": False},
]

KEY_TO_TYPE = {
    "name":         "identity_name",
    "email":        "identity_email",
    "phone":        "identity_phone",
    "organization": "identity_organization",
}


def seed_identity_questions(apps, schema_editor):
    Survey = apps.get_model("register", "Survey")
    Question = apps.get_model("register", "Question")

    for survey in Survey.objects.filter(purpose="registration"):
        # Skip if any identity question already exists for this survey.
        if survey.questions.filter(question_type__in=KEY_TO_TYPE.values()).exists():
            continue

        config = survey.identity_field_config or DEFAULT_CONFIG
        visible_fields = [f for f in config if isinstance(f, dict) and f.get("visible", True)]
        if not visible_fields:
            continue

        shift = len(visible_fields)

        # Shift existing custom-question numbers down so the new identity rows
        # can occupy 1..shift. Use a temporary high offset to avoid colliding
        # with the unique-ish ordering during the update.
        existing = list(survey.questions.order_by("number"))
        if existing:
            for q in existing:
                q.number = q.number + 10000
                q.save(update_fields=["number"])
            for q in existing:
                q.number = q.number - 10000 + shift
                q.save(update_fields=["number"])

        for idx, f in enumerate(visible_fields, start=1):
            key = f.get("key")
            qtype = KEY_TO_TYPE.get(key)
            if not qtype:
                continue
            Question.objects.create(
                survey=survey,
                number=idx,
                text=(f.get("label") or key.title()),
                question_type=qtype,
                is_required=bool(f.get("required", False)),
            )


def noop_reverse(apps, schema_editor):
    # Reversing this migration is not meaningful — the identity_field_config
    # JSON is preserved on the Survey row, so a re-forward run will re-seed.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0043_alter_question_question_type"),
    ]

    operations = [
        migrations.RunPython(seed_identity_questions, noop_reverse),
    ]
