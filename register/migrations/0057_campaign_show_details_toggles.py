from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0056_friendly_email_placeholders'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='show_details_qr',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='campaign',
            name='show_details_reminder',
            field=models.BooleanField(default=True),
        ),
    ]
