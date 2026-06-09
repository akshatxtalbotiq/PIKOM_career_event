from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0052_backfill_identity_field_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='campaign',
            name='event_time',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='campaign',
            name='venue',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='campaign',
            name='dress_code',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
        migrations.AddField(
            model_name='campaign',
            name='parking',
            field=models.CharField(blank=True, default='', max_length=200),
        ),
        migrations.AddField(
            model_name='campaign',
            name='agenda_url',
            field=models.URLField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='campaign',
            name='agenda_label',
            field=models.CharField(blank=True, default='Summit Agenda', max_length=80),
        ),
        migrations.AddField(
            model_name='campaign',
            name='extra_info',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='campaign',
            name='qr_email_intro',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='campaign',
            name='reminder_intro',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='campaign',
            name='email_signoff',
            field=models.CharField(blank=True, default='', max_length=160),
        ),
    ]
