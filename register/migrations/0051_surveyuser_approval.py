from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('register', '0050_backfill_survey_slugs'),
    ]

    operations = [
        migrations.AddField(
            model_name='surveyuser',
            name='approval_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending review'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                ],
                default='pending',
                help_text='Vetting status. QR codes are only emailed to approved delegates.',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='surveyuser',
            name='approved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='surveyuser',
            name='approved_by',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='surveyuser_approvals',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
