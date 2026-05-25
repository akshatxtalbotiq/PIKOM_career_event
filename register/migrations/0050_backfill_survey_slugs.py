"""Generate a unique slug for every existing Survey from its title."""
from django.db import migrations
from django.utils.text import slugify


def backfill(apps, schema_editor):
    Survey = apps.get_model("register", "Survey")
    used = set(Survey.objects.exclude(slug__isnull=True).exclude(slug='').values_list('slug', flat=True))
    for s in Survey.objects.filter(slug__isnull=True).order_by('id'):
        base = slugify(s.title or '')[:70] or f"form-{s.id}"
        slug = base
        n = 2
        while slug in used:
            suffix = f"-{n}"
            slug = (base[:70 - len(suffix)] + suffix)
            n += 1
        used.add(slug)
        Survey.objects.filter(pk=s.pk).update(slug=slug)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("register", "0049_survey_slug"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
