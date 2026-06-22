from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0064_surveyuser_reminder_sent'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='registration_closed_intro',
            field=models.TextField(blank=True, default=''),
        ),
    ]
