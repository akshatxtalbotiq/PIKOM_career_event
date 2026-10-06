from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0067_alter_question_question_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="campaign",
            name="organizer_name",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="campaign",
            name="organizer_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AddField(
            model_name="campaign",
            name="organizer_phone",
            field=models.CharField(blank=True, default="", max_length=80),
        ),
        migrations.AddField(
            model_name="campaign",
            name="banner",
            field=models.ImageField(blank=True, null=True, upload_to="event_banners/"),
        ),
    ]
