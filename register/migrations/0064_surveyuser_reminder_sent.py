from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0063_campaign_email_banner_toggle'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyuser',
            name='reminder_sent',
            field=models.BooleanField(default=False),
        ),
    ]
