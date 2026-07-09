from django.db import migrations, models


PARTICIPANT_TYPE_CHOICES = [
    ("Organizer", "Organizer"),
    ("Delegate", "Delegate"),
    ("Sponsor", "Sponsor"),
    ("Exhibitor", "Exhibitor"),
    ("Speaker", "Speaker"),
]

DEFAULT_IDENTITY_CONFIG = [
    {"key": "name", "label": "Name", "visible": True, "required": True},
    {"key": "participant_type", "label": "Participant Type", "visible": True, "required": True},
    {"key": "email", "label": "Email", "visible": True, "required": True},
    {"key": "phone", "label": "Phone", "visible": True, "required": False},
    {"key": "organization", "label": "Organization", "visible": True, "required": False},
]


def _merge_identity_config(stored):
    by_key = {item.get("key"): item for item in (stored or []) if isinstance(item, dict)}
    merged = []
    seen = set()
    for d in DEFAULT_IDENTITY_CONFIG:
        k = d["key"]
        s = by_key.get(k)
        if s:
            merged.append({
                "key": k,
                "label": s.get("label") or d["label"],
                "visible": s.get("visible", d["visible"]),
                "required": s.get("required", d["required"]),
            })
        else:
            merged.append(dict(d))
        seen.add(k)

    for item in (stored or []):
        if isinstance(item, dict) and item.get("key") not in seen:
            merged.append(item)
            seen.add(item.get("key"))
    return merged


def backfill_participant_type_identity(apps, schema_editor):
    Survey = apps.get_model("register", "Survey")
    Question = apps.get_model("register", "Question")

    for survey in Survey.objects.filter(purpose="registration").iterator():
        merged_cfg = _merge_identity_config(survey.identity_field_config)
        if merged_cfg != survey.identity_field_config:
            Survey.objects.filter(pk=survey.pk).update(identity_field_config=merged_cfg)

        # Add the new participant-type identity question for existing forms.
        if survey.questions.filter(question_type="identity_participant_type").exists():
            continue

        existing = list(survey.questions.order_by("number", "id"))
        insert_at = 2  # after Name by default
        name_q = next((q for q in existing if q.question_type == "identity_name"), None)
        if name_q:
            insert_at = (name_q.number or 1) + 1
        elif existing:
            insert_at = (existing[0].number or 1)

        # Shift all questions at/after insert_at to preserve order.
        for q in reversed(existing):
            if (q.number or 0) >= insert_at:
                q.number = (q.number or 0) + 1
                q.save(update_fields=["number"])

        Question.objects.create(
            survey=survey,
            number=insert_at,
            text="Participant Type",
            question_type="identity_participant_type",
            is_required=True,
            choices=[c[0] for c in PARTICIPANT_TYPE_CHOICES],
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0065_campaign_registration_closed_intro"),
    ]

    operations = [
        migrations.AddField(
            model_name="surveyuser",
            name="participant_type",
            field=models.CharField(
                choices=PARTICIPANT_TYPE_CHOICES,
                default="Delegate",
                max_length=32,
            ),
        ),
        migrations.RunPython(backfill_participant_type_identity, noop_reverse),
    ]
