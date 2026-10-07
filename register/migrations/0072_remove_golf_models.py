from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("register", "0071_golfevent_golfform_golfquestion_golfregistration_and_more"),
    ]

    operations = [
        migrations.DeleteModel(name="GolfAnswer"),
        migrations.DeleteModel(name="GolfPlayer"),
        migrations.DeleteModel(name="GolfSelection"),
        migrations.DeleteModel(name="GolfEventTeam"),
        migrations.DeleteModel(name="GolfSizeImage"),
        migrations.DeleteModel(name="GolfQuestion"),
        migrations.DeleteModel(name="GolfRegistration"),
        migrations.DeleteModel(name="GolfSponsorItem"),
        migrations.DeleteModel(name="GolfForm"),
        migrations.DeleteModel(name="GolfEvent"),
    ]
