from django.db import migrations

# Earlier the backfilled QR/reminder intros contained Django template syntax
# ({{ title }}, {% if name %} ... {% endif %}). Organisers should never see code
# syntax, so the intros now use plain bracket placeholders ([Name], [Event],
# [Date]) handled by simple find-and-replace. Convert any intro that still holds
# template syntax to the friendly default. Bracket-only / hand-edited content is
# left untouched.

QR_FRIENDLY = (
    "<p>Hi [Name],</p>"
    "<p>Thanks for registering for [Event]. Please present the QR code below at check-in.</p>"
)
REMINDER_FRIENDLY = (
    "<p>Hi [Name],</p>"
    "<p>This is a friendly reminder that [Event] is coming up on [Date]. "
    "We look forward to seeing you there!</p>"
)


def _has_code(text):
    text = text or ""
    return "{{" in text or "{%" in text


def forward(apps, schema_editor):
    Campaign = apps.get_model("register", "Campaign")
    for c in Campaign.objects.all():
        changed = []
        if _has_code(c.qr_email_intro):
            c.qr_email_intro = QR_FRIENDLY
            changed.append("qr_email_intro")
        if _has_code(c.reminder_intro):
            c.reminder_intro = REMINDER_FRIENDLY
            changed.append("reminder_intro")
        if changed:
            c.save(update_fields=changed)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0055_move_parking_agenda_to_extra_info'),
    ]

    operations = [
        migrations.RunPython(forward, noop),
    ]
