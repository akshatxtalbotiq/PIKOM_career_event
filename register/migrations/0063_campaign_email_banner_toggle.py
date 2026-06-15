from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0062_campaign_thankyou_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='show_banner_qr',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='campaign',
            name='show_banner_reminder',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='campaign',
            name='show_banner_thankyou',
            field=models.BooleanField(default=True),
        ),
    ]
