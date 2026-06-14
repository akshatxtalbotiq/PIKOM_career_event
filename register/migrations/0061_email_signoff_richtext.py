# Sign-off becomes sanitised rich-text HTML (multi-line, bold, coloured text),
# so the 160-char CharField is widened to a TextField. Existing plain-text
# values are kept as-is and still render (the email helper bolds them).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0060_campaign_theme_color"),
    ]

    operations = [
        migrations.AlterField(
            model_name="campaign",
            name="email_signoff",
            field=models.TextField(blank=True, default=""),
        ),
    ]
