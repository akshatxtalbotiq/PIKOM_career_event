import uuid
from django.db import migrations, models


def backfill_registration_codes(apps, schema_editor):
    SurveyUser = apps.get_model('register', 'SurveyUser')
    for su in SurveyUser.objects.all().only('id'):
        SurveyUser.objects.filter(pk=su.pk).update(registration_code=uuid.uuid4())


class Migration(migrations.Migration):

    dependencies = [
        ('register', '0037_submission_consent'),
    ]

    operations = [
        # 1. Add the new fields. registration_code is nullable + non-unique at first
        #    so the table can be altered without colliding on existing rows.
        migrations.AddField(
            model_name='surveyuser',
            name='registration_code',
            field=models.UUIDField(null=True, unique=False),
        ),
        migrations.AddField(
            model_name='surveyuser',
            name='is_checked_in',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='surveyuser',
            name='remarks',
            field=models.TextField(blank=True, null=True),
        ),
        # 2. Backfill a unique UUID for every existing row.
        migrations.RunPython(backfill_registration_codes, migrations.RunPython.noop),
        # 3. Tighten the column to the final shape: non-null, unique, default=uuid4.
        migrations.AlterField(
            model_name='surveyuser',
            name='registration_code',
            field=models.UUIDField(default=uuid.uuid4, unique=True),
        ),
    ]
