from django.db import migrations


# Parking and the agenda link were dedicated Campaign fields; they are now just
# rows in `extra_info`. Move any existing values into extra_info (prepended, so
# they keep the original date/time/venue/dress -> parking -> agenda ordering),
# then drop the columns.

PARKING_ICON = "\U0001F17F️"   # 🅿️
AGENDA_ICON = "\U0001F4DD"          # 📝


def forward(apps, schema_editor):
    Campaign = apps.get_model("register", "Campaign")
    for c in Campaign.objects.all():
        existing = list(c.extra_info or [])
        prepend = []
        if (getattr(c, "parking", "") or "").strip():
            prepend.append({"icon": PARKING_ICON, "label": "", "value": c.parking.strip(), "link": ""})
        agenda_url = (getattr(c, "agenda_url", "") or "").strip()
        agenda_label = (getattr(c, "agenda_label", "") or "").strip()
        if agenda_url or agenda_label:
            prepend.append({
                "icon": AGENDA_ICON,
                "label": "",
                "value": agenda_label or "Agenda",
                "link": agenda_url,
            })
        if prepend:
            c.extra_info = prepend + existing
            c.save(update_fields=["extra_info"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0054_backfill_pcioc2026_event_details'),
    ]

    operations = [
        migrations.RunPython(forward, noop),
        migrations.RemoveField(model_name='campaign', name='parking'),
        migrations.RemoveField(model_name='campaign', name='agenda_url'),
        migrations.RemoveField(model_name='campaign', name='agenda_label'),
    ]
