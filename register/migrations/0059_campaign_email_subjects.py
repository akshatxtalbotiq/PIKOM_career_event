from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0058_survey_show_event_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='qr_email_subject',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='campaign',
            name='reminder_subject',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
    ]
