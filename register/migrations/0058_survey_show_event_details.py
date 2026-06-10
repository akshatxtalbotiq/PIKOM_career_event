from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0057_campaign_show_details_toggles'),
    ]

    operations = [
        migrations.AddField(
            model_name='survey',
            name='show_event_details',
            field=models.BooleanField(
                default=False,
                help_text="Show the campaign's event details block (date, time, venue, etc.) "
                          "at the top of the public registration form.",
            ),
        ),
    ]
