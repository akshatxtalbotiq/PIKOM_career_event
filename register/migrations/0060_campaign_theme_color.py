# Per-event theme colour: hex accent used on the public registration form and
# in registrant emails. Default is the green (#198754) the emails already used.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0059_campaign_email_subjects"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="theme_color",
            field=models.CharField(blank=True, default="#198754", max_length=7),
        ),
    ]
