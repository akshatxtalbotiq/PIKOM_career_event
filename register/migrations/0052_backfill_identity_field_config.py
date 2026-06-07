"""Backfill identity_field_config on existing surveys.

JSONField defaults are only applied when a row is first created, so surveys
built before phone/organization were added to the default identity config have a
stored config missing those keys. That hid the fields from the registrations
list and the form builder. This migration merges each survey's stored config
with the full default set so every identity field is present (in canonical
order), with stored values preserved and any missing field falling back to its
default (visible) state.

The merge logic is inlined rather than imported from models so this migration
stays stable even if the model helper changes later.
"""
from django.db import migrations


# Canonical default identity fields. Kept in sync with
# register.models.default_identity_field_config at the time of writing.
DEFAULTS = [
    {"key": "name",         "label": "Name",         "visible": True, "required": True},
    {"key": "email",        "label": "Email",        "visible": True, "required": True},
    {"key": "phone",        "label": "Phone",        "visible": True, "required": False},
    {"key": "organization", "label": "Organization", "visible": True, "required": False},
]


def _merge(stored):
    by_key = {item.get("key"): item for item in (stored or []) if isinstance(item, dict)}
    merged = []
    seen = set()
    for d in DEFAULTS:
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


def backfill(apps, schema_editor):
    Survey = apps.get_model("register", "Survey")
    for s in Survey.objects.all().iterator():
        merged = _merge(s.identity_field_config)
        if merged != s.identity_field_config:
            Survey.objects.filter(pk=s.pk).update(identity_field_config=merged)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0051_surveyuser_approval"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
