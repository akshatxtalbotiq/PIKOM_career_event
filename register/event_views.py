from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .event_services import (
    AttendeeNotEligibleError,
    SessionCapacityError,
    SessionRegistrationError,
    SessionUnavailableError,
    cancel_session_registration,
    register_for_session,
)
from .forms import BoothForm, EventSessionForm, FloorMapForm
from .models import (
    Booth,
    Campaign,
    CampaignTeam,
    EventSession,
    FloorMap,
    SessionRegistration,
    SurveyUser,
)


def _can_manage_event(user, campaign):
    return user.is_superuser or CampaignTeam.objects.filter(
        campaign=campaign, user=user
    ).exists()


def _infrastructure_context(campaign, **forms):
    sessions = EventSession.objects.filter(campaign=campaign).annotate(
        registration_count=Count(
            "registrations",
            filter=Q(registrations__status=SessionRegistration.STATUS_BOOKED),
        )
    )
    session_date = forms.pop("session_date", "")
    if session_date:
        sessions = sessions.filter(event_date=session_date)
    floor_maps = FloorMap.objects.filter(campaign=campaign).prefetch_related("booths")
    return {
        "campaign": campaign,
        "sessions": sessions,
        "session_date": session_date,
        "floor_maps": floor_maps,
        "session_form": forms.get("session_form") or EventSessionForm(campaign=campaign),
        "floor_map_form": forms.get("floor_map_form") or FloorMapForm(),
        "booth_form": forms.get("booth_form") or BoothForm(campaign=campaign),
    }


@login_required
def event_infrastructure(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if not _can_manage_event(request.user, campaign):
        return HttpResponse("You don't have access to this event.", status=403)

    if request.method == "POST":
        action = request.POST.get("action")
        if action in {"save_session", "save_floor_map", "save_booth"}:
            instance = None
            if action == "save_session" and request.POST.get("item_id"):
                instance = get_object_or_404(EventSession, pk=request.POST["item_id"], campaign=campaign)
                form = EventSessionForm(request.POST, instance=instance, campaign=campaign)
            elif action == "save_session":
                form = EventSessionForm(request.POST, campaign=campaign)
            elif action == "save_floor_map" and request.POST.get("item_id"):
                instance = get_object_or_404(FloorMap, pk=request.POST["item_id"], campaign=campaign)
                form = FloorMapForm(request.POST, request.FILES, instance=instance)
            elif action == "save_floor_map":
                form = FloorMapForm(request.POST, request.FILES)
            elif action == "save_booth" and request.POST.get("item_id"):
                instance = get_object_or_404(Booth, pk=request.POST["item_id"], floor_map__campaign=campaign)
                form = BoothForm(request.POST, instance=instance, campaign=campaign)
            else:
                form = BoothForm(request.POST, campaign=campaign)

            if form.is_valid():
                item = form.save(commit=False)
                if action == "save_session":
                    item.campaign = campaign
                elif action == "save_floor_map":
                    item.campaign = campaign
                item.save()
                if action == "save_floor_map":
                    label = "Floor map"
                elif action == "save_session":
                    label = "Session"
                else:
                    label = "Booth"
                messages.success(request, f"{label} saved.")
                return redirect("event_infrastructure", campaign_id=campaign.id)

            context = _infrastructure_context(
                campaign,
                session_date=request.GET.get("date", ""),
                session_form=form if action == "save_session" else None,
                floor_map_form=form if action == "save_floor_map" else None,
                booth_form=form if action == "save_booth" else None,
            )
            return render(request, "register/event_infrastructure.html", context)

        delete_specs = {
            "delete_session": (EventSession, {"campaign": campaign}, "Session"),
            "delete_floor_map": (FloorMap, {"campaign": campaign}, "Floor map"),
            "delete_booth": (Booth, {"floor_map__campaign": campaign}, "Booth"),
        }
        if action in delete_specs:
            model, filters, label = delete_specs[action]
            item = get_object_or_404(model, pk=request.POST.get("item_id"), **filters)
            item.delete()
            messages.success(request, f"{label} deleted.")
            return redirect("event_infrastructure", campaign_id=campaign.id)

    edit_session = request.GET.get("edit_session")
    edit_map = request.GET.get("edit_map")
    edit_booth = request.GET.get("edit_booth")
    context = _infrastructure_context(
        campaign,
        session_date=request.GET.get("date", ""),
        session_form=EventSessionForm(
            instance=get_object_or_404(EventSession, pk=edit_session, campaign=campaign) if edit_session else None,
            campaign=campaign,
        ),
        floor_map_form=FloorMapForm(
            instance=get_object_or_404(FloorMap, pk=edit_map, campaign=campaign) if edit_map else None
        ),
        booth_form=BoothForm(
            instance=get_object_or_404(Booth, pk=edit_booth, floor_map__campaign=campaign) if edit_booth else None,
            campaign=campaign,
        ),
    )
    return render(request, "register/event_infrastructure.html", context)


def attendee_session_registration(request, session_id, registration_code):
    session = get_object_or_404(
        EventSession.objects.select_related("campaign"), pk=session_id
    )
    attendee = get_object_or_404(
        SurveyUser.objects.select_related("survey"),
        registration_code=registration_code,
        survey__fkcampaign=session.campaign,
    )
    if request.method == "POST":
        try:
            if request.POST.get("action") == "cancel":
                cancel_session_registration(session.pk, attendee)
                messages.success(request, "Your session booking was cancelled.")
            else:
                register_for_session(session.pk, attendee)
                messages.success(request, "You are registered for this session.")
        except SessionCapacityError as exc:
            messages.error(request, str(exc))
        except (SessionUnavailableError, AttendeeNotEligibleError, SessionRegistrationError) as exc:
            messages.error(request, str(exc))
        return redirect(reverse("attendee_session_registration", args=[session.pk, attendee.registration_code]))

    registration = SessionRegistration.objects.filter(
        session=session, attendee=attendee
    ).first()
    booked_count = session.registrations.filter(status=SessionRegistration.STATUS_BOOKED).count()
    remaining_capacity = None if session.capacity is None else max(session.capacity - booked_count, 0)
    return render(request, "register/attendee_session_registration.html", {
        "session": session,
        "attendee": attendee,
        "registration": registration,
        "remaining_capacity": remaining_capacity,
        "can_register": (
            session.status == EventSession.STATUS_SCHEDULED
            and session.campaign.is_active
            and attendee.approval_status == SurveyUser.STATUS_APPROVED
            and (remaining_capacity is None or remaining_capacity > 0)
        ),
    })


def attendee_event_sessions(request, registration_code):
    attendee = get_object_or_404(
        SurveyUser.objects.select_related("survey__fkcampaign"),
        registration_code=registration_code,
    )
    campaign = attendee.survey.fkcampaign
    if not campaign:
        return HttpResponse("No event is attached to this registration.", status=404)
    sessions = EventSession.objects.filter(campaign=campaign).annotate(
        registration_count=Count(
            "registrations",
            filter=Q(registrations__status=SessionRegistration.STATUS_BOOKED),
        )
    )
    current_bookings = dict(
        SessionRegistration.objects.filter(attendee=attendee).values_list("session_id", "status")
    )
    for session in sessions:
        session.attendee_registration_status = current_bookings.get(session.id, "")
        session.remaining_capacity = (
            None if session.capacity is None
            else max(session.capacity - session.registration_count, 0)
        )
    return render(request, "register/attendee_event_sessions.html", {
        "campaign": campaign,
        "attendee": attendee,
        "sessions": sessions,
    })
