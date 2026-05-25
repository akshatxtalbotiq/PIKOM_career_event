"""Backfill SurveyUser.reg_no for rows created before the column existed."""
from django.db import migrations


def backfill(apps, schema_editor):
    SurveyUser = apps.get_model("register", "SurveyUser")
    for su in SurveyUser.objects.filter(reg_no__isnull=True).only("id"):
        SurveyUser.objects.filter(pk=su.pk).update(reg_no=f"REG{su.id:06d}")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0046_question_show_in_list_surveyuser_qr_sent_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
