"""Golf Event: tournaments, participant / sponsor form builders and entries.

Kept in its own module so `views.py` stays navigable. The email / rich-text
helpers are reused from `views.py` (they duck-type on `.pic_email`,
`.email_signoff`, `.theme` — all of which GolfEvent provides), so wording and
look stay identical to the campaign emails.
"""

import json
import os
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.defaultfilters import date as _date_filter
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags
from django.utils.text import slugify
from email.utils import formataddr
import re

from picom import settings

from .models import (
    GolfAnswer,
    GolfEvent,
    GolfEventTeam,
    GolfForm,
    GolfPlayer,
    GolfQuestion,
    GolfRegistration,
    GolfSelection,
    GolfSponsorItem,
    default_golf_player_field_config,
    default_golf_salutations,
    default_golf_tshirt_sizes,
    GOLF_PLAYER_FIELD_KEYS,
)
from .views import (
    _email_base_url,
    _reply_to_header,
    _render_intro,
    _render_subject,
    _sanitize_intro,
    _signoff_html,
)


# ---------------------------------------------------------------------------
# Access control + small helpers
# ---------------------------------------------------------------------------

def _can_manage_golf_event(request, event):
    """Superusers, or members of the event team, may manage a golf event."""
    if request.user.is_superuser:
        return True
    if not event:
        return False
    return GolfEventTeam.objects.filter(event=event, user=request.user).exists()


def _golf_events_for_user(request, active_only=False):
    qs = GolfEvent.objects.all()
    if active_only:
        qs = qs.filter(is_active=True)
    if not request.user.is_superuser:
        qs = qs.filter(event_teams__user=request.user)
    return qs.distinct()


def _golf_forms_for_user(request, kind):
    if request.user.is_superuser:
        qs = GolfForm.objects.filter(kind=kind)
    else:
        qs = GolfForm.objects.filter(kind=kind, fkevent__event_teams__user=request.user).distinct()
    return qs.select_related("fkevent").order_by("-created_at")


def _can_manage_golf_form(request, form):
    """A form is manageable by superusers and by the team of its event.
    A form not yet attached to an event is superuser-only."""
    if request.user.is_superuser:
        return True
    if not form or not form.fkevent:
        return False
    return GolfEventTeam.objects.filter(event=form.fkevent, user=request.user).exists()


def _golf_unique_slug(title, exclude_id=None):
    """Unique GolfForm slug derived from `title`, with a numeric suffix when the
    base slug is taken."""
    base = slugify(title or "")[:70] or "golf-form"
    slug = base
    n = 2
    qs = GolfForm.objects.all()
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    while qs.filter(slug=slug).exists():
        suffix = f"-{n}"
        slug = base[:70 - len(suffix)] + suffix
        n += 1
    return slug


def _resolve_golf_form(identifier, kind=None):
    """Look a GolfForm up by slug first, then by its UUID form_code so links
    already shared keep working."""
    qs = GolfForm.objects.all()
    if kind:
        qs = qs.filter(kind=kind)
    form = qs.filter(slug=identifier).first()
    if form:
        return form
    try:
        return qs.get(form_code=identifier)
    except (ValueError, ValidationError, GolfForm.DoesNotExist):
        raise Http404("Form not found")


def _golf_open(form):
    """A form accepts entries only while the form itself is active AND (when
    attached) its golf event is active."""
    if not form.is_active:
        return False
    if form.fkevent and not form.fkevent.is_active:
        return False
    return True


def _decimal_or_none(raw):
    """Parse a money value from a form/JSON payload. Returns None for blank or
    unparseable input so 'not set' stays distinguishable from zero."""
    if raw is None:
        return None
    txt = str(raw).strip().replace(",", "")
    if txt == "":
        return None
    try:
        value = Decimal(txt)
    except (InvalidOperation, ValueError):
        return None
    if value < 0:
        return None
    return value.quantize(Decimal("0.01"))


def _sponsor_items_for_event(event, addons_only=False):
    """Sponsor items belonging to a golf event, across all of its sponsor forms.
    `addons_only` narrows to the items flagged for the participant page."""
    if not event:
        return GolfSponsorItem.objects.none()
    qs = GolfSponsorItem.objects.filter(
        form__fkevent=event,
        form__kind=GolfForm.KIND_SPONSOR,
        is_active=True,
    )
    if addons_only:
        qs = qs.filter(show_in_participant=True)
    return qs.select_related("form").order_by("number", "id")


def _annotate_availability(items):
    """Attach `taken` to each item once, so templates don't fire a query per card.

    An item is closed for selection when EITHER an organiser switched it off by
    hand (`is_available = False`) OR it is a once-only item that some entry has
    already claimed. Everything downstream — the public pages, the builder's
    add-on mirror, and submit-time validation — reads this one flag, so both
    routes to "unavailable" behave identically."""
    items = list(items)
    once_ids = [i.id for i in items if i.once_only]
    claimed_ids = set()
    if once_ids:
        claimed_ids = set(
            GolfSelection.objects.filter(item_id__in=once_ids)
            .values_list("item_id", flat=True)
        )
    for i in items:
        i.claimed = i.id in claimed_ids          # closed automatically
        i.closed_by_organiser = not i.is_available
        i.taken = i.claimed or i.closed_by_organiser
    return items


# ===========================================================================
# Golf Event  (Menu: Golf Event > Event)
# ===========================================================================

@login_required
def golf_event_list(request):
    current_user = request.user
    events = list(_golf_events_for_user(request))

    users = User.objects.all()
    user_data = [
        {
            "id": u.id,
            "email": u.email,
            "name": (u.get_full_name() or u.username) + ((" (" + u.email + ")") if u.email else ""),
        }
        for u in users
    ]

    # Attach each event's forms so the row can link straight to the builder,
    # the public page and the entries list — no URL pasting by hand.
    for e in events:
        e.participant_form = (
            e.forms.filter(kind=GolfForm.KIND_PARTICIPANT).order_by("-created_at").first()
        )
        e.sponsor_form = (
            e.forms.filter(kind=GolfForm.KIND_SPONSOR).order_by("-created_at").first()
        )

    return render(request, "register/golf_event_list.html", {
        "user": current_user,
        "events": events,
        "users": user_data,
    })


@login_required
def save_golf_event(request):
    """Create or update a golf event (posted from the list-page modal)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    event_id = request.POST.get("id")
    title = (request.POST.get("title") or "").strip()
    start_date = parse_datetime(request.POST.get("start_date") or "")
    end_date = parse_datetime(request.POST.get("end_date") or "")
    is_active = request.POST.get("is_active") == "true"
    pic_email = (request.POST.get("pic_email") or "").strip()
    selected_users = request.POST.getlist("users[]")

    theme_color = (request.POST.get("theme_color") or "").strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", theme_color):
        theme_color = GolfEvent.THEME_DEFAULT

    if not title:
        return JsonResponse({"success": False, "error": "Event title is required."}, status=400)
    if not start_date or not end_date:
        return JsonResponse({"success": False, "error": "Start and end dates are required."}, status=400)

    if event_id:
        event = get_object_or_404(GolfEvent, id=event_id)
        if not _can_manage_golf_event(request, event):
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        event.title = title
        event.start_date = start_date
        event.end_date = end_date
        event.is_active = is_active
        event.pic_email = pic_email
        event.theme_color = theme_color
        event.save()
    else:
        if not request.user.is_superuser:
            return JsonResponse(
                {"success": False, "error": "Only administrators can create a golf event."},
                status=403,
            )
        event = GolfEvent.objects.create(
            title=title,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            pic_email=pic_email,
            theme_color=theme_color,
        )

    GolfEventTeam.objects.filter(event=event).delete()
    for uid in selected_users:
        user = User.objects.filter(id=uid).first()
        if user:
            GolfEventTeam.objects.create(event=event, user=user)

    return JsonResponse({"success": True, "id": event.id})


@login_required
def get_golf_event(request, id):
    event = get_object_or_404(GolfEvent, id=id)
    if not _can_manage_golf_event(request, event):
        return JsonResponse({"error": "Permission denied"}, status=403)

    users = User.objects.all()
    user_data = [
        {
            "id": u.id,
            "email": u.email,
            "name": (u.get_full_name() or u.username) + ((" (" + u.email + ")") if u.email else ""),
        }
        for u in users
    ]
    return JsonResponse({
        "id": event.id,
        "title": event.title,
        "start_date": event.start_date.isoformat() if event.start_date else "",
        "end_date": event.end_date.isoformat() if event.end_date else "",
        "active": event.is_active,
        "pic_email": event.pic_email,
        "theme_color": event.theme,
        "users": user_data,
        "selected_users": [t.user_id for t in event.event_teams.all()],
    })


@login_required
def delete_golf_event(request, id):
    """Delete a golf event. Cascades to its forms, items and entries."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)
    event = get_object_or_404(GolfEvent, id=id)
    if not request.user.is_superuser:
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    event.delete()
    return JsonResponse({"success": True})


# ===========================================================================
# Form lists  (Golf Event > Registration Form / Sponsor Form)
# ===========================================================================

def _golf_form_list(request, kind, page_meta):
    events = _golf_events_for_user(request, active_only=True).order_by("-start_date")
    event_list = [{"id": str(e.id), "title": e.title} for e in events]
    forms = _golf_forms_for_user(request, kind)

    return render(request, "register/golf_form_list.html", dict(
        page_meta,
        user=request.user,
        forms=forms,
        events=event_list,
        list_kind=kind,
        auto_open_event_id=request.GET.get("for_event") or "",
    ))


@login_required
def golf_participant_form_list(request):
    return _golf_form_list(request, GolfForm.KIND_PARTICIPANT, {
        "list_title": "Golf Event Registration Forms",
        "list_subtitle": "Forms that flights fill in to register for a golf event",
        "new_button_label": "New Registration Form",
        "modal_title": "Add New Golf Registration Form",
    })


@login_required
def golf_sponsor_form_list(request):
    return _golf_form_list(request, GolfForm.KIND_SPONSOR, {
        "list_title": "Golf Event Sponsor Forms",
        "list_subtitle": "Forms that sponsors fill in to take up sponsorship items",
        "new_button_label": "New Sponsor Form",
        "modal_title": "Add New Golf Sponsor Form",
    })


@login_required
def save_golf_form(request):
    """Create or update a golf form (posted from the list-page modal)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request"}, status=400)

    form_id = request.POST.get("id")
    title = (request.POST.get("title") or "").strip()
    description = request.POST.get("description") or ""
    start_date = parse_datetime(request.POST.get("start_date") or "")
    end_date = parse_datetime(request.POST.get("end_date") or "")
    is_active = request.POST.get("is_active") == "true"
    event_id = request.POST.get("event_id")
    raw_slug = (request.POST.get("slug") or "").strip()

    kind = request.POST.get("kind") or GolfForm.KIND_PARTICIPANT
    if kind not in {c[0] for c in GolfForm.KIND_CHOICES}:
        kind = GolfForm.KIND_PARTICIPANT

    if not title:
        return JsonResponse({"success": False, "error": "Form title is required."}, status=400)

    event = get_object_or_404(GolfEvent, id=event_id) if event_id else None
    if not request.user.is_superuser and (event is None or not _can_manage_golf_event(request, event)):
        return JsonResponse(
            {"success": False, "error": "You can only create or assign forms within your own golf events."},
            status=403,
        )

    if form_id:
        form = get_object_or_404(GolfForm, id=form_id)
        if not _can_manage_golf_form(request, form):
            return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
        form.title = title
        form.description = description
        form.start_date = start_date
        form.end_date = end_date
        form.is_active = is_active
        form.fkevent = event
        if raw_slug:
            new_slug = slugify(raw_slug)[:80]
            if new_slug and new_slug != form.slug:
                if GolfForm.objects.filter(slug=new_slug).exclude(id=form.id).exists():
                    return JsonResponse(
                        {"success": False, "error": f"URL '{new_slug}' is already used by another form."},
                        status=400,
                    )
                form.slug = new_slug
        elif not form.slug:
            form.slug = _golf_unique_slug(title, exclude_id=form.id)
        form.save()
    else:
        if raw_slug:
            slug = slugify(raw_slug)[:80] or _golf_unique_slug(title)
            if GolfForm.objects.filter(slug=slug).exists():
                return JsonResponse(
                    {"success": False, "error": f"URL '{slug}' is already used by another form."},
                    status=400,
                )
        else:
            slug = _golf_unique_slug(title)
        form = GolfForm.objects.create(
            kind=kind,
            title=title,
            slug=slug,
            description=description,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active,
            fkevent=event,
            player_field_config=default_golf_player_field_config(),
            salutation_options=default_golf_salutations(),
            tshirt_sizes=default_golf_tshirt_sizes(),
        )

    return JsonResponse({"success": True, "id": form.id})


@login_required
def get_golf_form(request, id):
    form = get_object_or_404(GolfForm, id=id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"error": "Permission denied"}, status=403)
    return JsonResponse({
        "id": form.id,
        "kind": form.kind,
        "title": form.title,
        "slug": form.slug or "",
        "description": form.description or "",
        "start_date": form.start_date.isoformat() if form.start_date else "",
        "end_date": form.end_date.isoformat() if form.end_date else "",
        "active": form.is_active,
        "event_id": str(form.fkevent.id) if form.fkevent else None,
    })


@login_required
def delete_golf_form(request, id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)
    form = get_object_or_404(GolfForm, id=id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)
    form.delete()
    return JsonResponse({"success": True})


@login_required
def clone_golf_form(request, id):
    """Clone a golf form with its questions and sponsor items. Entries are NOT
    copied, and cloned once-only items start out available again."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    source = get_object_or_404(GolfForm, id=id)
    if not _can_manage_golf_form(request, source):
        return JsonResponse({"success": False, "error": "Permission denied"}, status=403)

    title = (request.POST.get("title") or "").strip() or f"Copy of {source.title}"
    event_id = request.POST.get("event_id")
    event = get_object_or_404(GolfEvent, id=event_id) if event_id else None
    if event and not _can_manage_golf_event(request, event):
        return JsonResponse({"success": False, "error": "Permission denied for that event"}, status=403)

    with transaction.atomic():
        clone = GolfForm.objects.create(
            kind=source.kind,
            title=title,
            slug=_golf_unique_slug(title),
            description=source.description,
            fkevent=event,
            start_date=source.start_date,
            end_date=source.end_date,
            is_active=source.is_active,
            show_event_details=source.show_event_details,
            note=source.note,
            player_slots=source.player_slots,
            required_players=source.required_players,
            package_label=source.package_label,
            package_price=source.package_price,
            currency=source.currency,
            player_field_config=source.player_field_config,
            salutation_options=source.salutation_options,
            tshirt_sizes=source.tshirt_sizes,
        )

        if source.banner:
            try:
                source.banner.open("rb")
                clone.banner.save(
                    os.path.basename(source.banner.name),
                    ContentFile(source.banner.read()),
                    save=True,
                )
            except FileNotFoundError:
                pass
            finally:
                source.banner.close()

        GolfQuestion.objects.bulk_create([
            GolfQuestion(
                form=clone,
                number=q.number,
                text=q.text,
                help_text=q.help_text,
                question_type=q.question_type,
                choices=q.choices,
                allow_other=q.allow_other,
                max_checks=q.max_checks,
                is_required=q.is_required,
                show_in_list=q.show_in_list,
                list_column_label=q.list_column_label,
            )
            for q in source.questions.all()
        ])

        for item in source.sponsor_items.all():
            new_item = GolfSponsorItem(
                form=clone,
                number=item.number,
                name=item.name,
                price=item.price,
                special_price=item.special_price,
                description=item.description,
                once_only=item.once_only,
                show_in_participant=item.show_in_participant,
                is_available=item.is_available,
                is_active=item.is_active,
            )
            new_item.save()
            for field in ("image", "logo"):
                src_file = getattr(item, field)
                if not src_file:
                    continue
                try:
                    src_file.open("rb")
                    getattr(new_item, field).save(
                        os.path.basename(src_file.name),
                        ContentFile(src_file.read()),
                        save=True,
                    )
                except FileNotFoundError:
                    pass
                finally:
                    src_file.close()

    return JsonResponse({"success": True, "id": clone.id})


# ===========================================================================
# Form builder
# ===========================================================================

@login_required
def golf_form_builder(request, form_id):
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return HttpResponse(status=403)

    public_url = request.build_absolute_uri(f"/golf/{form.public_ident}/")

    context = {
        "user": request.user,
        "form": form,
        "event": form.fkevent,
        "public_url": public_url,
        "questions": form.questions.all().order_by("number"),
        "question_types": GolfQuestion.QUESTION_TYPES,
        "player_fields": form.player_fields,
        "list_url": (
            "golf_participant_form_list" if form.is_participant else "golf_sponsor_form_list"
        ),
    }

    if form.is_sponsor:
        context["sponsor_items"] = _annotate_availability(form.sponsor_items.all())
    else:
        # Add-ons offered on this participant page come from the event's
        # sponsor form(s) — shown read-only here so the organiser can see what
        # participants will be offered.
        context["addon_items"] = _annotate_availability(
            _sponsor_items_for_event(form.fkevent, addons_only=True)
        )

    return render(request, "register/golf_form_builder.html", context)


@login_required
def golf_form_preview(request, form_id):
    """Owner-only preview: renders the public page exactly as entrants see it,
    flagged so the submit handler is a no-op."""
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return HttpResponse(status=403)
    return render(request, "register/golf_form_public.html",
                  _golf_public_context(form, preview_mode=True))


@login_required
def golf_upload_banner(request, form_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    banner = request.FILES.get("banner")
    if not banner:
        return JsonResponse({"success": False, "message": "No file uploaded"}, status=400)
    if banner.size > 5 * 1024 * 1024:
        return JsonResponse({"success": False, "message": "Banner must be under 5 MB"}, status=400)
    if not (banner.content_type or "").startswith("image/"):
        return JsonResponse({"success": False, "message": "File must be an image"}, status=400)
    form.banner = banner
    form.save(update_fields=["banner"])
    return JsonResponse({"success": True, "url": form.banner.url})


@login_required
def golf_delete_banner(request, form_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    if form.banner:
        form.banner.delete(save=False)
        form.banner = None
        form.save(update_fields=["banner"])
    return JsonResponse({"success": True})


@login_required
def save_golf_player_config(request, form_id):
    """Save the order / visibility / required state / labels of the fixed
    player identity fields on a participant form."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    config = data.get("config")
    if not isinstance(config, list):
        return JsonResponse({"success": False, "message": "config must be a list"}, status=400)

    allowed = set(GOLF_PLAYER_FIELD_KEYS)
    defaults = {f["key"]: f for f in default_golf_player_field_config()}
    cleaned, seen = [], set()
    for item in config:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        if key not in allowed or key in seen:
            continue
        seen.add(key)
        cleaned.append({
            "key": key,
            "label": (item.get("label") or defaults[key]["label"]).strip()[:100],
            "visible": bool(item.get("visible", True)),
            "required": bool(item.get("required", False)),
        })
    # Name always stays visible and required — an entry with a nameless player
    # is not usable, and it is the only field the entries list can key on.
    for row in cleaned:
        if row["key"] == "name":
            row["visible"] = True
            row["required"] = True
    # Force-include anything the payload omitted, at its default state.
    for key in GOLF_PLAYER_FIELD_KEYS:
        if key not in seen:
            cleaned.append(dict(defaults[key]))

    form.player_field_config = cleaned
    form.save(update_fields=["player_field_config"])
    return JsonResponse({"success": True, "config": cleaned})


@login_required
def save_golf_form_settings(request, form_id):
    """Save the builder's form-level settings: player slots, package price,
    salutation / T-shirt option lists and the note shown before Submit."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    fields = ["note"]
    form.note = _sanitize_intro(data.get("note"))

    if "show_event_details" in data:
        form.show_event_details = bool(data.get("show_event_details"))
        fields.append("show_event_details")

    if form.is_participant:
        try:
            slots = int(data.get("player_slots") or form.player_slots)
        except (TypeError, ValueError):
            slots = form.player_slots
        slots = max(1, min(slots, 12))

        try:
            required = int(data.get("required_players") or 0)
        except (TypeError, ValueError):
            required = form.required_players
        required = max(0, min(required, slots))

        form.player_slots = slots
        form.required_players = required
        form.package_label = (data.get("package_label") or "").strip()[:200] or "Participation Package"
        form.package_price = _decimal_or_none(data.get("package_price"))
        form.currency = (data.get("currency") or "RM").strip()[:8] or "RM"

        salutations = [
            s.strip()[:50] for s in (data.get("salutation_options") or [])
            if isinstance(s, str) and s.strip()
        ]
        form.salutation_options = salutations or default_golf_salutations()

        sizes = [
            s.strip()[:10] for s in (data.get("tshirt_sizes") or [])
            if isinstance(s, str) and s.strip()
        ]
        form.tshirt_sizes = sizes or default_golf_tshirt_sizes()

        fields += [
            "player_slots", "required_players", "package_label", "package_price",
            "currency", "salutation_options", "tshirt_sizes",
        ]
    else:
        form.currency = (data.get("currency") or "RM").strip()[:8] or "RM"
        fields.append("currency")

    form.save(update_fields=fields)
    return JsonResponse({
        "success": True,
        "note": form.note,
        "player_slots": form.player_slots,
        "required_players": form.required_players,
        "package_price": str(form.package_price) if form.package_price is not None else "",
    })


@login_required
def save_golf_event_details(request, event_id):
    """Save the event facts shown on the public pages and in the emails."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    event = get_object_or_404(GolfEvent, id=event_id)
    if not _can_manage_golf_event(request, event):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    event.event_time = (data.get("event_time") or "").strip()[:120]
    event.venue = (data.get("venue") or "").strip()
    event.dress_code = (data.get("dress_code") or "").strip()[:120]

    cleaned = []
    rows = data.get("extra_info")
    if isinstance(rows, list):
        for item in rows:
            if not isinstance(item, dict):
                continue
            row = {
                "icon": (item.get("icon") or "").strip()[:8],
                "label": (item.get("label") or "").strip()[:120],
                "value": (item.get("value") or "").strip()[:500],
                "link": (item.get("link") or "").strip()[:500],
            }
            if row["label"] or row["value"] or row["link"]:
                cleaned.append(row)
    event.extra_info = cleaned
    event.save(update_fields=["event_time", "venue", "dress_code", "extra_info"])

    # Per-form toggle, edited on the same builder card.
    form_id = data.get("form_id")
    if form_id and "show_on_form" in data:
        GolfForm.objects.filter(id=form_id, fkevent=event).update(
            show_event_details=bool(data.get("show_on_form"))
        )

    return JsonResponse({"success": True, "extra_info": cleaned})


@login_required
def save_golf_email_content(request, event_id):
    """Save the confirmation-email wording, sign-off and closed-page copy."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    event = get_object_or_404(GolfEvent, id=event_id)
    if not _can_manage_golf_event(request, event):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    event.confirmation_intro = _sanitize_intro(data.get("confirmation_intro"))
    event.registration_closed_intro = _sanitize_intro(data.get("registration_closed_intro"))
    event.email_signoff = _sanitize_intro(data.get("email_signoff"))
    event.confirmation_subject = " ".join((data.get("confirmation_subject") or "").split())[:200]
    event.show_details_confirmation = bool(data.get("show_details_confirmation", True))
    event.show_banner_confirmation = bool(data.get("show_banner_confirmation", True))
    event.save(update_fields=[
        "confirmation_intro", "registration_closed_intro", "email_signoff",
        "confirmation_subject", "show_details_confirmation", "show_banner_confirmation",
    ])
    return JsonResponse({"success": True, "confirmation_intro": event.confirmation_intro})


# ---------------------------------------------------------------------------
# Builder: custom questions
# ---------------------------------------------------------------------------

@login_required
def save_golf_question(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    qid = data.get("id")
    form_id = data.get("form_id")
    text = (data.get("text") or "").strip()
    if not text:
        return JsonResponse({"success": False, "message": "Question text is required"}, status=400)

    question_type = data.get("question_type") or GolfQuestion.TYPE_TEXT
    if question_type not in {c[0] for c in GolfQuestion.QUESTION_TYPES}:
        return JsonResponse({"success": False, "message": "Invalid question type"}, status=400)

    question = get_object_or_404(GolfQuestion, id=qid) if qid else None
    form = question.form if question else get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)

    is_required = bool(data.get("is_required", False))
    allow_other = bool(data.get("allow_other", False))
    show_in_list = bool(data.get("show_in_list", False))
    list_column_label = (data.get("list_column_label") or "").strip()[:60]
    choices = data.get("choices") or []
    max_checks = data.get("max_checks") or None

    needs_choices = question_type in (
        GolfQuestion.TYPE_RADIO, GolfQuestion.TYPE_CHECKBOX, GolfQuestion.TYPE_SELECT
    )
    if needs_choices:
        choices = [c.strip() for c in choices if isinstance(c, str) and c.strip()]
        if not choices:
            return JsonResponse(
                {"success": False, "message": "At least one choice is required"}, status=400
            )
    else:
        choices = None
        allow_other = False

    if max_checks not in (None, ""):
        try:
            max_checks = int(max_checks)
            if max_checks <= 0:
                max_checks = None
        except (TypeError, ValueError):
            max_checks = None
    else:
        max_checks = None

    if question:
        question.text = text
        question.help_text = (data.get("help_text") or "").strip()
        question.question_type = question_type
        question.is_required = is_required
        question.allow_other = allow_other
        question.max_checks = max_checks if question_type == GolfQuestion.TYPE_CHECKBOX else None
        question.choices = choices
        question.show_in_list = show_in_list
        question.list_column_label = list_column_label
        question.save()
    else:
        next_number = (form.questions.aggregate(m=Max("number"))["m"] or 0) + 1
        question = GolfQuestion.objects.create(
            form=form,
            number=next_number,
            text=text,
            help_text=(data.get("help_text") or "").strip(),
            question_type=question_type,
            is_required=is_required,
            allow_other=allow_other,
            max_checks=max_checks if question_type == GolfQuestion.TYPE_CHECKBOX else None,
            choices=choices,
            show_in_list=show_in_list,
            list_column_label=list_column_label,
        )

    return JsonResponse({"success": True, "id": question.id, "number": question.number})


@login_required
def get_golf_question(request, question_id):
    question = get_object_or_404(GolfQuestion, id=question_id)
    if not _can_manage_golf_form(request, question.form):
        return JsonResponse({"error": "Permission denied"}, status=403)
    return JsonResponse({
        "id": question.id,
        "form_id": question.form_id,
        "number": question.number,
        "text": question.text,
        "help_text": question.help_text,
        "question_type": question.question_type,
        "is_required": question.is_required,
        "allow_other": question.allow_other,
        "max_checks": question.max_checks,
        "choices": question.choices or [],
        "show_in_list": question.show_in_list,
        "list_column_label": question.list_column_label or "",
    })


@login_required
def delete_golf_question(request, question_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    question = get_object_or_404(GolfQuestion, id=question_id)
    if not _can_manage_golf_form(request, question.form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    form = question.form
    question.delete()
    for idx, q in enumerate(form.questions.order_by("number"), start=1):
        if q.number != idx:
            q.number = idx
            q.save(update_fields=["number"])
    return JsonResponse({"success": True})


@login_required
def reorder_golf_questions(request, form_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    with transaction.atomic():
        for idx, qid in enumerate(data.get("order") or [], start=1):
            GolfQuestion.objects.filter(id=qid, form=form).update(number=idx)
    return JsonResponse({"success": True})


# ---------------------------------------------------------------------------
# Builder: sponsor items
# ---------------------------------------------------------------------------

@login_required
def save_golf_sponsor_item(request):
    """Create or update a sponsor item. Multipart, because the item image and
    the corner logo are uploaded on the same modal."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)

    item_id = request.POST.get("id")
    form_id = request.POST.get("form_id")

    item = get_object_or_404(GolfSponsorItem, id=item_id) if item_id else None
    form = item.form if item else get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    if not form.is_sponsor:
        return JsonResponse(
            {"success": False, "message": "Sponsor items can only be added to a sponsor form."},
            status=400,
        )

    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"success": False, "message": "Item name is required"}, status=400)

    price = _decimal_or_none(request.POST.get("price"))
    if price is None:
        return JsonResponse({"success": False, "message": "A valid item price is required"}, status=400)

    special_price = _decimal_or_none(request.POST.get("special_price"))
    show_in_participant = request.POST.get("show_in_participant") == "true"
    once_only = request.POST.get("once_only") == "true"
    is_active = request.POST.get("is_active", "true") == "true"
    # Defaults to available, so an older client that omits the field can never
    # accidentally close an item.
    is_available = request.POST.get("is_available", "true") == "true"
    description = _sanitize_intro(request.POST.get("description"))

    # The participant page only ever shows the special price, so an item
    # offered there must have one. The special price is deliberately NOT
    # constrained relative to the item price — it may be higher or lower.
    if show_in_participant and special_price is None:
        return JsonResponse(
            {"success": False,
             "message": "Item special price is required when the item is shown on the participant page."},
            status=400,
        )

    if item is None:
        next_number = (form.sponsor_items.aggregate(m=Max("number"))["m"] or 0) + 1
        item = GolfSponsorItem(form=form, number=next_number)

    item.name = name
    item.price = price
    item.special_price = special_price
    item.description = description
    item.once_only = once_only
    item.show_in_participant = show_in_participant
    item.is_available = is_available
    item.is_active = is_active

    if request.POST.get("remove_image") == "true" and item.image:
        item.image.delete(save=False)
        item.image = None
    if request.POST.get("remove_logo") == "true" and item.logo:
        item.logo.delete(save=False)
        item.logo = None

    image = request.FILES.get("image")
    logo = request.FILES.get("logo")
    for f, label in ((image, "Item image"), (logo, "Logo")):
        if f and f.size > 5 * 1024 * 1024:
            return JsonResponse({"success": False, "message": f"{label} must be under 5 MB"}, status=400)
        if f and not (f.content_type or "").startswith("image/"):
            return JsonResponse({"success": False, "message": f"{label} must be an image"}, status=400)
    if image:
        item.image = image
    if logo:
        item.logo = logo

    item.save()
    return JsonResponse({"success": True, "id": item.id, "number": item.number})


@login_required
def get_golf_sponsor_item(request, item_id):
    item = get_object_or_404(GolfSponsorItem, id=item_id)
    if not _can_manage_golf_form(request, item.form):
        return JsonResponse({"error": "Permission denied"}, status=403)
    return JsonResponse({
        "id": item.id,
        "form_id": item.form_id,
        "number": item.number,
        "name": item.name,
        "price": str(item.price),
        "special_price": str(item.special_price) if item.special_price is not None else "",
        "description": item.description or "",
        "image_url": item.image.url if item.image else "",
        "logo_url": item.logo.url if item.logo else "",
        "once_only": item.once_only,
        "show_in_participant": item.show_in_participant,
        "is_available": item.is_available,
        "is_active": item.is_active,
        "claimed": item.is_taken,
        "sold_out": item.is_sold_out,
    })


@login_required
def set_golf_item_availability(request, item_id):
    """Flip a sponsor item's availability from the builder's item list, without
    opening the edit modal."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    item = get_object_or_404(GolfSponsorItem, id=item_id)
    if not _can_manage_golf_form(request, item.form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    item.is_available = bool(data.get("available"))
    item.save(update_fields=["is_available"])
    return JsonResponse({
        "success": True,
        "is_available": item.is_available,
        # A once-only item that has already been claimed stays closed regardless,
        # so the UI can explain why switching it back on changed nothing.
        "claimed": item.is_taken,
        "sold_out": item.is_sold_out,
    })


@login_required
def delete_golf_sponsor_item(request, item_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    item = get_object_or_404(GolfSponsorItem, id=item_id)
    if not _can_manage_golf_form(request, item.form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    form = item.form
    item.delete()
    for idx, i in enumerate(form.sponsor_items.order_by("number", "id"), start=1):
        if i.number != idx:
            i.number = idx
            i.save(update_fields=["number"])
    return JsonResponse({"success": True})


@login_required
def reorder_golf_sponsor_items(request, form_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    with transaction.atomic():
        for idx, iid in enumerate(data.get("order") or [], start=1):
            GolfSponsorItem.objects.filter(id=iid, form=form).update(number=idx)
    return JsonResponse({"success": True})


# ===========================================================================
# Public pages
# ===========================================================================

# Labels for the billing block; the two form kinds ask for different things.
PARTICIPANT_BILLING_LABELS = [
    ("billing_company", "Company Full Name (as per ROS/ROC)", "text", True),
    ("billing_reg_no", "Business Reg. No.", "text", True),
    ("billing_address", "Company Full Address", "textarea", True),
    ("billing_email", "Contact person (e-Invoice) email", "email", True),
]

SPONSOR_BILLING_LABELS = [
    ("billing_company", "Organisation", "text", True),
    ("billing_address", "Billing Address", "textarea", True),
    ("billing_contact_person", "Contact Person (for payment)", "text", True),
    ("billing_designation", "Designation", "text", True),
    ("billing_contact_number", "Contact Number", "text", True),
    ("billing_email", "Email Address", "email", True),
]

CONTACT_LABELS = [
    ("contact_person", "Contact Person", "text", True),
    ("contact_designation", "Designation", "text", True),
    ("contact_number", "Contact Number (Mobile)", "text", True),
    ("contact_email", "Email Add.", "email", True),
]


def _billing_spec(form):
    return SPONSOR_BILLING_LABELS if form.is_sponsor else PARTICIPANT_BILLING_LABELS


def _golf_public_context(form, preview_mode=False, closed=False):
    """Shared context for the public page, its preview, and re-renders after a
    validation error."""
    event = form.fkevent
    closed_message = ""
    if closed:
        title = (event.title if event else form.title) or ""
        date = event.end_date.strftime("%A, %d %B %Y") if (event and event.end_date) else ""
        raw = (event.registration_closed_intro if event else "") or ""
        closed_message = raw.replace("[Event]", title).replace("[Date]", date)

    ctx = {
        "form": form,
        "event": event,
        "preview_mode": preview_mode,
        "registration_closed": closed,
        "registration_closed_message": closed_message,
        "questions": list(form.questions.all().order_by("number")),
        "contact_spec": CONTACT_LABELS,
        "billing_spec": _billing_spec(form),
        "currency": form.currency or "RM",
    }

    if form.is_participant:
        fmap = form.player_field_map()
        ctx["player_slots"] = list(range(1, (form.player_slots or 4) + 1))
        ctx["required_players"] = form.required_players or 0
        ctx["player_fields"] = [f for f in form.player_fields if f.get("visible")]
        ctx["field_map"] = fmap
        ctx["salutations"] = form.salutation_options or default_golf_salutations()
        ctx["tshirt_sizes"] = form.tshirt_sizes or default_golf_tshirt_sizes()
        ctx["package_price"] = form.package_price
        ctx["package_label"] = form.package_label or "Participation Package"
        ctx["items"] = _annotate_availability(_sponsor_items_for_event(event, addons_only=True))
        ctx["items_are_addons"] = True
    else:
        ctx["items"] = _annotate_availability(form.sponsor_items.filter(is_active=True))
        ctx["items_are_addons"] = False
        ctx["package_price"] = None

    return ctx


def golf_form_public(request, form_ident):
    """Public entry page. Serves both the participant and the sponsor form —
    the template branches on `form.kind`."""
    form = _resolve_golf_form(form_ident)
    closed = not _golf_open(form)
    return render(request, "register/golf_form_public.html",
                  _golf_public_context(form, closed=closed))


def _player_payload(request, slot, form):
    """Pull one player's posted values out of POST."""
    def val(field):
        return (request.POST.get(f"p{slot}_{field}") or "").strip()

    return {
        "salutation": val("salutation")[:50],
        "salutation_other": val("salutation_other")[:100],
        "name": val("name")[:255],
        "handicap": val("handicap")[:50],
        "is_tgcc_member": request.POST.get(f"p{slot}_tgcc_member") == "yes",
        "tgcc_membership_no": val("tgcc_membership_no")[:100],
        "organisation": val("organisation")[:255],
        "designation": val("designation")[:255],
        "mobile": val("mobile")[:100],
        "email": val("email")[:254],
        "tshirt_size": val("tshirt_size")[:10],
    }


def _player_is_blank(payload):
    """True when nothing was typed into a player block (so an optional slot can
    be skipped entirely)."""
    for key, value in payload.items():
        if key == "is_tgcc_member":
            if value:
                return False
        elif str(value).strip():
            return False
    return True


# Player-config key -> the payload key(s) that satisfy its "required" rule.
_PLAYER_REQUIRED_SOURCES = {
    "salutation": ("salutation",),
    "name": ("name",),
    "handicap": ("handicap",),
    "tgcc_member": None,       # a No answer is a valid answer; never blocks
    "organisation": ("organisation",),
    "designation": ("designation",),
    "mobile": ("mobile",),
    "email": ("email",),
    "tshirt_size": ("tshirt_size",),
}


def _validate_players(request, form):
    """Validate the player blocks. Returns (players, errors) where `players` is
    a list of (slot, payload) for the slots that were actually filled in."""
    errors = []
    players = []
    slots = form.player_slots or 4
    required_upto = form.required_players or 0
    fmap = form.player_field_map()

    for slot in range(1, slots + 1):
        payload = _player_payload(request, slot, form)
        blank = _player_is_blank(payload)

        if blank:
            if slot <= required_upto:
                errors.append(f"Player {slot}: all details are required.")
            continue

        for key, cfg in fmap.items():
            if not cfg.get("visible") or not cfg.get("required"):
                continue
            sources = _PLAYER_REQUIRED_SOURCES.get(key)
            if not sources:
                continue
            if not any(str(payload.get(s) or "").strip() for s in sources):
                errors.append(f"Player {slot}: {cfg.get('label') or key} is required.")

        # "Others" salutation needs the free-text spelled out.
        if payload["salutation"] == GolfPlayer.SALUTATION_OTHER and not payload["salutation_other"]:
            errors.append(f"Player {slot}: please specify the salutation.")
        # A TGCC member must give the membership number.
        if payload["is_tgcc_member"] and not payload["tgcc_membership_no"]:
            errors.append(f"Player {slot}: TGCC membership number is required.")

        players.append((slot, payload))

    if len(players) < required_upto:
        errors.append(f"Please complete at least {required_upto} player(s).")

    return players, errors


def _validate_flat_fields(request, spec, prefix_label):
    """Validate the contact / billing blocks against their field spec."""
    values, errors = {}, []
    for key, label, _kind, required in spec:
        raw = (request.POST.get(key) or "").strip()
        values[key] = raw
        if required and not raw:
            errors.append(f"{prefix_label}: {label} is required.")
    return values, errors


def _validate_questions(request, questions):
    """Server-side enforcement of required custom questions (the browser form
    uses novalidate, and JS validation is bypassable)."""
    errors = []
    for q in questions:
        if not q.is_required:
            continue
        field = f"q_{q.id}"
        if q.question_type == GolfQuestion.TYPE_CHECKBOX:
            picked = [p for p in request.POST.getlist(field) if p.strip()]
            other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
            ok = bool(picked) or bool(other)
        elif q.question_type in (GolfQuestion.TYPE_RADIO, GolfQuestion.TYPE_SELECT):
            picked = (request.POST.get(field) or "").strip()
            other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
            ok = bool(picked) or bool(other)
        else:
            ok = bool((request.POST.get(field) or "").strip())
        if not ok:
            label = strip_tags(q.text or "").strip()
            errors.append(f"{label or 'Question'} is required.")
    return errors


def _validate_items(request, form, available_items):
    """Resolve the picked item ids against what is actually on offer.
    Returns (items, errors)."""
    errors = []
    picked_ids = set()
    for raw in request.POST.getlist("items"):
        try:
            picked_ids.add(int(raw))
        except (TypeError, ValueError):
            continue

    by_id = {i.id: i for i in available_items}
    items = []
    for iid in picked_ids:
        item = by_id.get(iid)
        if item is None:
            errors.append("One of the selected items is no longer available.")
            continue
        if getattr(item, "taken", False):
            errors.append(f"'{item.name}' has already been taken.")
            continue
        items.append(item)

    # A sponsor entry with nothing selected is meaningless; add-ons are optional.
    if form.is_sponsor and not items and not errors:
        errors.append("Please select at least one sponsorship item.")

    return items, errors


def golf_form_submit(request, form_id):
    """Single-page submission for both golf form kinds."""
    form = get_object_or_404(GolfForm, id=form_id)
    if request.method != "POST":
        return redirect("golf_form_public", form_ident=form.public_ident)
    if not _golf_open(form):
        return redirect("golf_form_public", form_ident=form.public_ident)

    questions = list(form.questions.all().order_by("number"))
    available_items = _annotate_availability(
        _sponsor_items_for_event(form.fkevent, addons_only=True)
        if form.is_participant else form.sponsor_items.filter(is_active=True)
    )

    errors = []
    players = []
    if form.is_participant:
        players, player_errors = _validate_players(request, form)
        errors += player_errors

    contact, contact_errors = _validate_flat_fields(request, CONTACT_LABELS, "Contact Details")
    billing, billing_errors = _validate_flat_fields(request, _billing_spec(form), "Billing Details")
    items, item_errors = _validate_items(request, form, available_items)
    errors += contact_errors + billing_errors + item_errors + _validate_questions(request, questions)

    if errors:
        for msg in errors[:12]:
            messages.error(request, msg)
        if len(errors) > 12:
            messages.error(request, f"…and {len(errors) - 12} more field(s) to complete.")
        return redirect("golf_form_public", form_ident=form.public_ident)

    with transaction.atomic():
        # Re-check once-only availability inside the transaction so two entries
        # submitted at the same moment can't both claim the same item.
        once_ids = [i.id for i in items if i.once_only]
        if once_ids:
            clash = set(
                GolfSelection.objects.select_for_update()
                .filter(item_id__in=once_ids)
                .values_list("item_id", flat=True)
            )
            if clash:
                names = ", ".join(i.name for i in items if i.id in clash)
                messages.error(request, f"Sorry — '{names}' was just taken. Please pick another item.")
                return redirect("golf_form_public", form_ident=form.public_ident)

        base_price = form.package_price if (form.is_participant and form.package_price) else Decimal("0")

        registration = GolfRegistration.objects.create(
            form=form,
            contact_person=contact.get("contact_person", "")[:255],
            contact_designation=contact.get("contact_designation", "")[:255],
            contact_number=contact.get("contact_number", "")[:100],
            contact_email=contact.get("contact_email", "")[:254],
            billing_company=billing.get("billing_company", "")[:255],
            billing_reg_no=billing.get("billing_reg_no", "")[:100],
            billing_address=billing.get("billing_address", ""),
            billing_email=billing.get("billing_email", "")[:254],
            billing_contact_person=billing.get("billing_contact_person", "")[:255],
            billing_designation=billing.get("billing_designation", "")[:255],
            billing_contact_number=billing.get("billing_contact_number", "")[:100],
            base_price=base_price,
            currency=form.currency or "RM",
        )
        prefix = "GLF" if form.is_participant else "GSP"
        registration.reg_no = f"{prefix}{registration.id:06d}"
        registration.save(update_fields=["reg_no"])

        for slot, payload in players:
            GolfPlayer.objects.create(registration=registration, slot=slot, **payload)

        for item in items:
            # Sponsor entries are charged the item price; participant add-ons are
            # charged the special price. See GolfSponsorItem.price_for().
            GolfSelection.objects.create(
                registration=registration,
                item=item,
                item_name=item.name[:255],
                unit_price=item.price_for(form),
                is_addon=form.is_participant,
            )

        registration.recalc_totals()

        for q in questions:
            field = f"q_{q.id}"
            if q.question_type in (GolfQuestion.TYPE_TEXT, GolfQuestion.TYPE_TEXTAREA):
                val = (request.POST.get(field) or "").strip()
                if val:
                    GolfAnswer.objects.create(
                        form=form, question=q, registration=registration, answer_text=val
                    )
            elif q.question_type in (GolfQuestion.TYPE_RADIO, GolfQuestion.TYPE_SELECT):
                picked = (request.POST.get(field) or "").strip()
                other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
                if picked:
                    GolfAnswer.objects.create(
                        form=form, question=q, registration=registration,
                        selected_options=[picked],
                        answer_text=other if (picked == "Other" and other) else None,
                    )
                elif other:
                    GolfAnswer.objects.create(
                        form=form, question=q, registration=registration,
                        selected_options=["Other"], answer_text=other,
                    )
            elif q.question_type == GolfQuestion.TYPE_CHECKBOX:
                picked = [p for p in request.POST.getlist(field) if p.strip()]
                other = (request.POST.get(f"{field}_other") or "").strip() if q.allow_other else ""
                if q.max_checks and len(picked) > q.max_checks:
                    picked = picked[: q.max_checks]
                if picked or other:
                    if other and "Other" not in picked:
                        picked.append("Other")
                    GolfAnswer.objects.create(
                        form=form, question=q, registration=registration,
                        selected_options=picked, answer_text=other or None,
                    )

    # Outside the transaction: a mail hiccup must never roll back a good entry.
    _send_golf_confirmation_email(registration, request=request)

    return redirect("golf_form_thankyou", form_ident=form.public_ident, reg_id=registration.id)


def golf_form_thankyou(request, form_ident, reg_id):
    form = _resolve_golf_form(form_ident)
    registration = get_object_or_404(GolfRegistration, pk=reg_id, form=form)
    return render(request, "register/golf_form_thankyou.html", {
        "form": form,
        "event": form.fkevent,
        "registration": registration,
        "selections": registration.selections.all(),
        "players": registration.players.all(),
    })


# ---------------------------------------------------------------------------
# Confirmation email
# ---------------------------------------------------------------------------

def _send_golf_confirmation_email(registration, request=None):
    """Send the "entry received" confirmation to the contact person. Best
    effort — any failure is logged, never raised."""
    to_addr = (registration.contact_email or "").strip()
    if not to_addr:
        return False

    form = registration.form
    event = form.fkevent
    base = _email_base_url(request)
    banner_url = (base + form.banner.url) if form.banner else ""
    event_date = event.end_date if event else None
    title = (event.title if event else form.title) or ""
    theme = event.theme if event else GolfEvent.THEME_DEFAULT

    tag_ctx = {
        "name": registration.contact_person or "",
        "reg_no": registration.reg_no or "",
        "event_date": _date_filter(event_date, "j F Y") if event_date else "",
        "title": title,
    }
    signoff_html = _signoff_html(event, title, theme)

    ctx = dict(tag_ctx)
    ctx.update({
        "form": form,
        # `campaign` is what register/email/_event_details_block.html reads; a
        # GolfEvent exposes the same attribute names.
        "campaign": event,
        "event": event,
        "registration": registration,
        "players": list(registration.players.all()),
        "selections": list(registration.selections.all()),
        "event_date": event_date,
        "event_date_str": tag_ctx["event_date"],
        "banner_url": banner_url,
        "signoff_html": signoff_html,
        "signoff": strip_tags(signoff_html.replace("</p>", " </p>").replace("<br", " <br")).strip(),
        "intro_html": _render_intro(
            (event.confirmation_intro if event else "") or "", tag_ctx, theme
        ),
        "show_details": bool(event.show_details_confirmation) if event else False,
        "show_banner": bool(event.show_banner_confirmation) if event else True,
        "is_sponsor": form.is_sponsor,
        "theme": theme,
        "theme_soft": event.theme_soft if event else "#e7f4ec",
    })

    default_subject = (
        f"Thank you for your sponsorship submission — {title}" if form.is_sponsor
        else f"Thank you for your registration — {title}"
    )
    subject = _render_subject(
        (event.confirmation_subject if event else "") or "", tag_ctx
    ) or default_subject

    try:
        html_content = render_to_string("register/email/email_golf_confirmation.html", ctx)
        email = EmailMultiAlternatives(
            subject=subject,
            body=strip_tags(html_content),
            from_email=formataddr((title or "Golf Event", settings.DEFAULT_FROM_EMAIL)),
            to=[to_addr],
            headers={"Reply-To": _reply_to_header(event)},
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        registration.confirmation_sent = True
        registration.save(update_fields=["confirmation_sent"])
        return True
    except Exception as e:  # pragma: no cover - mail backend dependent
        print(f"golf confirmation email failed for {to_addr}: {e}")
        return False


# ===========================================================================
# Entries list (admin)
# ===========================================================================

@login_required
def golf_submission_list(request, form_id):
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return HttpResponse(status=403)

    registrations = list(
        form.registrations
            .prefetch_related("players", "selections", "answers__question")
            .order_by("-submitted_at")
    )

    list_questions = list(form.questions.filter(show_in_list=True).order_by("number"))

    # Flatten the answers each row needs into the shape the template renders.
    for reg in registrations:
        by_question = {}
        for a in reg.answers.all():
            if a.selected_options:
                value = ", ".join(str(o) for o in a.selected_options)
                if a.answer_text and "Other" in a.selected_options:
                    value = value.replace("Other", a.answer_text)
            else:
                value = a.answer_text or ""
            by_question[a.question_id] = value
        reg.list_answers = [by_question.get(q.id, "") for q in list_questions]
        reg.player_count = len(reg.players.all())

    counts = {
        "total": len(registrations),
        "pending": sum(1 for r in registrations if r.approval_status == GolfRegistration.STATUS_PENDING),
        "approved": sum(1 for r in registrations if r.approval_status == GolfRegistration.STATUS_APPROVED),
        "rejected": sum(1 for r in registrations if r.approval_status == GolfRegistration.STATUS_REJECTED),
        "players": sum(r.player_count for r in registrations),
    }
    revenue = sum((r.total_amount or Decimal("0")) for r in registrations
                  if r.approval_status != GolfRegistration.STATUS_REJECTED)

    return render(request, "register/golf_submission_list.html", {
        "user": request.user,
        "form": form,
        "event": form.fkevent,
        "registrations": registrations,
        "list_questions": list_questions,
        "counts": counts,
        "revenue": revenue,
        "currency": form.currency or "RM",
        "list_url": (
            "golf_participant_form_list" if form.is_participant else "golf_sponsor_form_list"
        ),
        "billing_spec": _billing_spec(form),
        "contact_spec": CONTACT_LABELS,
    })


@login_required
def golf_submission_detail(request, form_id, reg_id):
    """Full detail of one entry, rendered as an HTML fragment for the drawer on
    the entries list."""
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return HttpResponse(status=403)
    registration = get_object_or_404(GolfRegistration, id=reg_id, form=form)

    answers = []
    for a in registration.answers.select_related("question").order_by("question__number"):
        if a.selected_options:
            value = ", ".join(str(o) for o in a.selected_options)
            if a.answer_text and "Other" in a.selected_options:
                value = value.replace("Other", a.answer_text)
        else:
            value = a.answer_text or ""
        answers.append({"label": strip_tags(a.question.text or ""), "value": value})

    return render(request, "register/golf_submission_detail.html", {
        "form": form,
        "event": form.fkevent,
        "registration": registration,
        "players": registration.players.all(),
        "selections": registration.selections.all(),
        "answers": answers,
        "player_fields": form.player_fields,
        "contact_spec": CONTACT_LABELS,
        "billing_spec": _billing_spec(form),
        "currency": registration.currency or form.currency or "RM",
    })


@login_required
def set_golf_registration_status(request, form_id):
    """Bulk approve / reject / reset entries."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)

    status = data.get("status")
    valid = {c[0] for c in GolfRegistration.STATUS_CHOICES}
    if status not in valid:
        return JsonResponse({"success": False, "message": "Invalid status"}, status=400)

    ids = [i for i in (data.get("ids") or []) if str(i).isdigit()]
    if not ids:
        return JsonResponse({"success": False, "message": "No entries selected"}, status=400)

    qs = GolfRegistration.objects.filter(id__in=ids, form=form)
    if status == GolfRegistration.STATUS_APPROVED:
        updated = qs.update(
            approval_status=status, approved_at=timezone.now(), approved_by=request.user
        )
    else:
        updated = qs.update(approval_status=status, approved_at=None, approved_by=None)
    return JsonResponse({"success": True, "updated": updated, "status": status})


@login_required
def update_golf_remarks(request, form_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    reg = get_object_or_404(GolfRegistration, id=data.get("id"), form=form)
    reg.remarks = (data.get("remarks") or "").strip()
    reg.save(update_fields=["remarks"])
    return JsonResponse({"success": True})


@login_required
def delete_golf_registrations(request, form_id):
    """Delete entries. Removing an entry that held a once-only item releases
    that item back to available."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
    form = get_object_or_404(GolfForm, id=form_id)
    if not _can_manage_golf_form(request, form):
        return JsonResponse({"success": False, "message": "Permission denied"}, status=403)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    ids = [i for i in (data.get("ids") or []) if str(i).isdigit()]
    if not ids:
        return JsonResponse({"success": False, "message": "No entries selected"}, status=400)
    deleted, _ = GolfRegistration.objects.filter(id__in=ids, form=form).delete()
    return JsonResponse({"success": True, "deleted": deleted})
