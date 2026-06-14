from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0061_email_signoff_richtext'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='thankyou_intro',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='campaign',
            name='thankyou_subject',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='campaign',
            name='show_details_thankyou',
            field=models.BooleanField(default=False),
        ),
    ]
