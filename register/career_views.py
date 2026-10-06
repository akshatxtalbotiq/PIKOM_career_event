from datetime import time

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .career_services import (
    CareerActionError, book_interview, cancel_interview_booking,
    cancel_voucher_claim, claim_voucher, interview_start_times,
)
from .event_views import _can_manage_event
from .forms import (
    EmployerForm, InterviewSlotForm, JobForm, TrainingProviderForm,
    UniversityForm, UniversityProgramForm, VoucherPromotionForm,
)
from .models import (
    Campaign, Employer, InterviewBooking, InterviewSlot, Job, JobBookmark,
    SurveyUser, TrainingProvider, University, UniversityProgram, VoucherClaim,
    VoucherPromotion,
)


FORM_CONFIG = {
    "employer": (Employer, EmployerForm, {"campaign": "campaign"}),
    "job": (Job, JobForm, {"employer__campaign": "campaign"}),
    "university": (University, UniversityForm, {"campaign": "campaign"}),
    "program": (UniversityProgram, UniversityProgramForm, {"university__campaign": "campaign"}),
    "provider": (TrainingProvider, TrainingProviderForm, {"campaign": "campaign"}),
    "promotion": (VoucherPromotion, VoucherPromotionForm, {"provider__campaign": "campaign"}),
    "interview": (InterviewSlot, InterviewSlotForm, {"employer__campaign": "campaign"}),
}
FORM_ORDER = ("employer", "job", "interview", "university", "program", "provider", "promotion")


def _career_context(campaign, forms=None, params=None):
    forms = forms or {}
    params = params or {}
    context = {"campaign": campaign, "forms": forms}
    for key in FORM_ORDER:
        model, form_class, _ = FORM_CONFIG[key]
        if key not in forms:
            instance = None
            edit_id = None
            # A compact, explicit lookup keeps every edit scoped to this event.
            if key == "job": query = Job.objects.filter(employer__campaign=campaign)
            elif key == "program": query = UniversityProgram.objects.filter(university__campaign=campaign)
            elif key == "promotion": query = VoucherPromotion.objects.filter(provider__campaign=campaign)
            elif key == "interview": query = InterviewSlot.objects.filter(employer__campaign=campaign)
            else: query = model.objects.filter(campaign=campaign)
            edit_id = None
            context[f"{key}_items"] = query
            edit_id = params.get(f"edit_{key}")
            instance = query.filter(pk=edit_id).first() if edit_id else None
            context[f"{key}_form"] = form_class(instance=instance, campaign=campaign)
    return context


@login_required
def event_career(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    if not _can_manage_event(request.user, campaign):
        return HttpResponse("You don't have access to this event.", status=403)
    if request.method == "POST":
        action = request.POST.get("action", "")
        key = action.removeprefix("save_")
        if key in FORM_CONFIG and action == f"save_{key}":
            model, form_class, _ = FORM_CONFIG[key]
            filters = {
                "employer": {"campaign": campaign}, "job": {"employer__campaign": campaign},
                "university": {"campaign": campaign}, "program": {"university__campaign": campaign},
                "provider": {"campaign": campaign}, "promotion": {"provider__campaign": campaign},
                "interview": {"employer__campaign": campaign},
            }[key]
            instance = get_object_or_404(model, pk=request.POST["item_id"], **filters) if request.POST.get("item_id") else None
            form = form_class(request.POST, request.FILES, instance=instance, campaign=campaign)
            if form.is_valid():
                item = form.save(commit=False)
                if key in {"employer", "university", "provider"}:
                    item.campaign = campaign
                item.save()
                messages.success(request, f"{item} saved.")
                return redirect("event_career", campaign_id=campaign.pk)
            context = _career_context(campaign, {key: form})
            return render(request, "register/event_career.html", context)
        delete_key = action.removeprefix("delete_")
        if delete_key in FORM_CONFIG and action == f"delete_{delete_key}":
            model, _, _ = FORM_CONFIG[delete_key]
            filters = {
                "employer": {"campaign": campaign}, "job": {"employer__campaign": campaign},
                "university": {"campaign": campaign}, "program": {"university__campaign": campaign},
                "provider": {"campaign": campaign}, "promotion": {"provider__campaign": campaign},
                "interview": {"employer__campaign": campaign},
            }[delete_key]
            get_object_or_404(model, pk=request.POST.get("item_id"), **filters).delete()
            messages.success(request, "Item deleted.")
            return redirect("event_career", campaign_id=campaign.pk)
    context = _career_context(campaign, params=request.GET)
    context["interview_items"] = InterviewSlot.objects.filter(employer__campaign=campaign).annotate(
        booking_count=Count("bookings", filter=Q(bookings__status=InterviewBooking.STATUS_BOOKED))
    )
    context["promotion_items"] = VoucherPromotion.objects.filter(provider__campaign=campaign).annotate(
        claim_count=Count("claims", filter=Q(claims__status=VoucherClaim.STATUS_CLAIMED))
    )
    return render(request, "register/event_career.html", context)


def attendee_career_hub(request, registration_code):
    attendee = get_object_or_404(SurveyUser.objects.select_related("survey__fkcampaign"), registration_code=registration_code)
    campaign = attendee.survey.fkcampaign if attendee.survey_id else None
    if campaign is None:
        return HttpResponse("Career information is unavailable.", status=404)
    employers = Employer.objects.filter(campaign=campaign, is_active=True).prefetch_related("jobs")
    jobs = Job.objects.filter(employer__campaign=campaign, employer__is_active=True, is_active=True).select_related("employer")
    universities = University.objects.filter(campaign=campaign, is_active=True).prefetch_related("programs")
    providers = TrainingProvider.objects.filter(campaign=campaign, is_active=True).prefetch_related("promotions")
    promotions = VoucherPromotion.objects.filter(provider__campaign=campaign, provider__is_active=True, is_active=True).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    ).select_related("provider")
    slots = InterviewSlot.objects.filter(employer__campaign=campaign, employer__is_active=True,
        status=InterviewSlot.STATUS_OPEN).select_related("employer").prefetch_related("bookings")
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action in {"bookmark", "unbookmark"}:
                if attendee.approval_status != SurveyUser.STATUS_APPROVED:
                    raise CareerActionError("Only approved attendees can save jobs.")
                job = get_object_or_404(jobs, pk=request.POST.get("job_id"))
                if action == "bookmark": JobBookmark.objects.get_or_create(job=job, attendee=attendee)
                else: JobBookmark.objects.filter(job=job, attendee=attendee).delete()
                messages.success(request, "Job saved." if action == "bookmark" else "Job removed from saved jobs.")
            elif action == "book_interview":
                book_interview(int(request.POST["slot_id"]), attendee, time.fromisoformat(request.POST["start_time"]))
                messages.success(request, "Interview booking confirmed.")
            elif action == "cancel_interview":
                cancel_interview_booking(int(request.POST["booking_id"]), attendee)
                messages.success(request, "Interview booking cancelled.")
            elif action == "claim_promotion":
                claim = claim_voucher(int(request.POST["promotion_id"]), attendee)
                promotion = claim.promotion
                if attendee.email:
                    send_mail(
                        f"Promotion claimed: {promotion.title}",
                        f"You claimed {promotion.title} for {campaign.title}.\n\n{promotion.instructions}\n\nValue: {promotion.value_label}\n",
                        None, [attendee.email], fail_silently=True,
                    )
                messages.success(request, "Promotion claimed. Instructions have been emailed if an address is on file.")
            elif action == "cancel_claim":
                cancel_voucher_claim(int(request.POST["claim_id"]), attendee)
                messages.success(request, "Promotion claim cancelled.")
        except (CareerActionError, ValueError, TypeError):
            messages.error(request, "That action could not be completed. Please refresh and try again.")
        return redirect("attendee_career_hub", registration_code=registration_code)
    bookmarks = set(JobBookmark.objects.filter(attendee=attendee).values_list("job_id", flat=True))
    bookings = InterviewBooking.objects.filter(attendee=attendee, status=InterviewBooking.STATUS_BOOKED).select_related("slot__employer")
    claims = VoucherClaim.objects.filter(attendee=attendee, status=VoucherClaim.STATUS_CLAIMED).select_related("promotion")
    slot_options = []
    for slot in slots:
        own = bookings.filter(slot=slot).first()
        options = []
        for start in interview_start_times(slot):
            used = sum(1 for b in slot.bookings.all() if b.status == InterviewBooking.STATUS_BOOKED and b.start_time == start)
            options.append({"value": start.isoformat(timespec="minutes"), "remaining": max(0, slot.capacity - used)})
        slot_options.append({"slot": slot, "options": options, "booking": own})
    return render(request, "register/attendee_career.html", {
        "attendee": attendee, "campaign": campaign, "employers": employers, "jobs": jobs,
        "universities": universities, "providers": providers, "promotions": promotions,
        "slots": slots, "slot_options": slot_options, "bookmarks": bookmarks, "bookings": bookings, "claims": claims,
    })
