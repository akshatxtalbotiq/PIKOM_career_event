from django.db import migrations

# Current PIKOM CIO Conference 2026 values, previously hardcoded in the
# reminder/QR email templates. Backfilled so the live event's emails are
# unchanged once content is driven by Campaign fields. Only empty fields are
# filled, so any value already set by an operator is preserved.

EVENT = {
    "event_time": "8:30am – 5:30pm",
    "venue": "Ballroom 1, Level 1, KLGCC Convention Centre "
             "(formerly known as Sime Darby Convention Centre), KL",
    "dress_code": "Smart Casual or Business Attire",
    "parking": "Complimentary Parking (Venue & Mall)",
    "agenda_url": "https://pikom.org.my/2026/CIO/PCIOC2026_Programme.pdf",
    "agenda_label": "Summit Agenda",
    "email_signoff": "The PCIOC 2026 Organising Team",
}

EXTRA_INFO = [
    {
        "icon": "\U0001F389",
        "label": "Exciting Lucky Draw Prizes!",
        "value": "Don’t miss your chance to win some great prizes and receive "
                 "exclusive door gifts — just for attending!",
    },
]

REMINDER_INTRO = (
    '<p>Hi {{ name|default:"there" }},</p>'
    '<p>This is a friendly reminder that <strong>{{ title }}</strong> is coming up'
    '{% if event_date %} on {{ event_date }}{% endif %}. '
    'We look forward to seeing you there!</p>'
)

QR_INTRO = (
    '<p>Thanks for registering for <strong>{{ title }}</strong>'
    '{% if name %}, <strong>{{ name }}</strong>{% endif %}.</p>'
)


def backfill(apps, schema_editor):
    Campaign = apps.get_model("register", "Campaign")
    for c in Campaign.objects.filter(title__icontains="CIO Conference 2026"):
        changed = []
        for field, value in EVENT.items():
            if not (getattr(c, field) or "").strip():
                setattr(c, field, value)
                changed.append(field)
        if not c.extra_info:
            c.extra_info = EXTRA_INFO
            changed.append("extra_info")
        if not (c.reminder_intro or "").strip():
            c.reminder_intro = REMINDER_INTRO
            changed.append("reminder_intro")
        if not (c.qr_email_intro or "").strip():
            c.qr_email_intro = QR_INTRO
            changed.append("qr_email_intro")
        if changed:
            c.save(update_fields=changed)


def noop(apps, schema_editor):
    # Non-destructive: leaving backfilled content in place on reverse.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0053_campaign_event_email_fields'),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
