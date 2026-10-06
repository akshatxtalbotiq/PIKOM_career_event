import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0068_campaign_event_profile"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("session_type", models.CharField(choices=[("panel", "Panel"), ("live", "Live session"), ("speaking", "Speaking session"), ("employer", "Employer presentation"), ("university", "University presentation"), ("other", "Other")], default="other", max_length=32)),
                ("event_date", models.DateField()),
                ("start_time", models.TimeField()),
                ("end_time", models.TimeField()),
                ("location", models.CharField(blank=True, default="", max_length=255)),
                ("capacity", models.PositiveIntegerField(blank=True, null=True)),
                ("speaker_name", models.CharField(blank=True, default="", max_length=255)),
                ("speaker_info", models.TextField(blank=True, default="")),
                ("status", models.CharField(choices=[("scheduled", "Scheduled"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="scheduled", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="event_sessions", to="register.campaign")),
            ],
            options={"ordering": ["event_date", "start_time", "title"]},
        ),
        migrations.CreateModel(
            name="FloorMap",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("version", models.CharField(blank=True, default="", max_length=40)),
                ("image", models.ImageField(upload_to="floor_maps/")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("inactive", "Inactive")], default="draft", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("campaign", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="floor_maps", to="register.campaign")),
            ],
            options={"ordering": ["-created_at", "name"]},
        ),
        migrations.CreateModel(
            name="Booth",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.CharField(max_length=40)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                ("x_percent", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("y_percent", models.DecimalField(decimal_places=2, default=0, max_digits=6)),
                ("width_percent", models.DecimalField(decimal_places=2, default=5, max_digits=6)),
                ("height_percent", models.DecimalField(decimal_places=2, default=5, max_digits=6)),
                ("category", models.CharField(blank=True, default="", max_length=100)),
                ("organization_name", models.CharField(blank=True, default="", max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("floor_map", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="booths", to="register.floormap")),
            ],
            options={
                "ordering": ["number", "name"],
                "constraints": [
                    models.UniqueConstraint(fields=("floor_map", "number"), name="unique_booth_number_per_floor_map"),
                    models.CheckConstraint(condition=models.Q(("height_percent__gt", 0), ("height_percent__lte", 100), ("width_percent__gt", 0), ("width_percent__lte", 100), ("x_percent__gte", 0), ("x_percent__lte", 100), ("y_percent__gte", 0), ("y_percent__lte", 100)), name="booth_position_and_size_percentages_valid"),
                ],
            },
        ),
        migrations.CreateModel(
            name="SessionRegistration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("booked", "Booked"), ("cancelled", "Cancelled")], default="booked", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("attendee", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="session_registrations", to="register.surveyuser")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="registrations", to="register.eventsession")),
            ],
            options={
                "ordering": ["created_at"],
                "constraints": [models.UniqueConstraint(fields=("session", "attendee"), name="unique_session_attendee_registration")],
            },
        ),
    ]
