"""Template helpers for the PIKOM Django-admin index (templates/admin/index.html)."""
from django import template
from django.apps import apps

register = template.Library()

# Material Symbols icon per model; anything unlisted falls back to "table_view".
MODEL_ICONS = {
    "group": "groups",
    "user": "person",
    "booth": "storefront",
    "campaign": "calendar_month",
    "employer": "apartment",
    "eventsession": "co_present",
    "floormap": "map",
    "interviewbooking": "event_available",
    "interviewslot": "schedule",
    "job": "work",
    "jobbookmark": "bookmark",
    "sessionregistration": "how_to_reg",
    "survey": "assignment",
    "trainingprovider": "school",
    "university": "account_balance",
    "universityprogram": "menu_book",
    "voucherclaim": "redeem",
    "voucherpromotion": "local_offer",
}


@register.simple_tag
def model_icon(model):
    return MODEL_ICONS.get(model.get("object_name", "").lower(), "table_view")


@register.simple_tag
def model_count(app_label, model):
    """Row count for an admin index card; blank if the model can't be counted."""
    try:
        return apps.get_model(app_label, model["object_name"]).objects.count()
    except Exception:
        return ""
