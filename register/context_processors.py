from django.conf import settings


def feature_flags(request):
    return {"show_legacy_golf_tools": settings.SHOW_LEGACY_GOLF_TOOLS}
