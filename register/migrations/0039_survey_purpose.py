from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0038_surveyuser_checkin_fields'),
    ]

    operations = [
        # Add the column with default='feedback' so every pre-existing Survey
        # (e.g. the PIKOM Talent Gap survey) is correctly categorized as a
        # post-event survey rather than a registration form.
        migrations.AddField(
            model_name='survey',
            name='purpose',
            field=models.CharField(
                choices=[
                    ('registration', 'Registration Form'),
                    ('feedback', 'Post-event Survey'),
                ],
                default='feedback',
                max_length=20,
            ),
        ),
        # Flip the default to 'registration' for newly created rows going
        # forward — most new forms will be event-registration forms.
        migrations.AlterField(
            model_name='survey',
            name='purpose',
            field=models.CharField(
                choices=[
                    ('registration', 'Registration Form'),
                    ('feedback', 'Post-event Survey'),
                ],
                default='registration',
                max_length=20,
            ),
        ),
    ]
