"""Stable, attendee-facing JSON API for the Next.js event experience."""
from datetime import time
from uuid import UUID
import json
import base64
from io import BytesIO

from django.db.models import Count, Prefetch, Q
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import BasePermission, AllowAny
from rest_framework.response import Response
from django.utils.html import strip_tags

from .career_services import (
    CareerActionError, book_interview, cancel_interview_booking,
    cancel_voucher_claim, claim_voucher, interview_start_times,
)
from .event_services import (
    AttendeeNotEligibleError, SessionCapacityError, SessionRegistrationError,
    SessionUnavailableError, cancel_session_registration, register_for_session,
)
from .models import (
    Booth, Campaign, Employer, EventSession, FloorMap, InterviewBooking,
    Answer, InterviewSlot, Job, JobBookmark, Question, SessionRegistration, Survey, SurveyUser,
    TrainingProvider, University, UniversityProgram, VoucherClaim,
    VoucherPromotion,
)
from .views import _send_registration_received_email
import qrcode


class AttendeeBearerAuthentication(BaseAuthentication):
    """The existing high-entropy registration UUID is the attendee API token."""
    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        token = header[7:].strip() if header.lower().startswith("bearer ") else request.headers.get("X-Attendee-Token", "")
        if not token:
            return None
        try:
            UUID(token)
        except (ValueError, TypeError):
            raise AuthenticationFailed("Invalid attendee token.")
        try:
            attendee = SurveyUser.objects.select_related("survey__fkcampaign").get(registration_code=token)
        except SurveyUser.DoesNotExist:
            raise AuthenticationFailed("Invalid attendee token.")
        if not attendee.survey_id or attendee.survey.purpose != Survey.PURPOSE_REGISTRATION or not attendee.survey.fkcampaign_id:
            raise AuthenticationFailed("Invalid attendee token.")
        return attendee, attendee

    def authenticate_header(self, request):
        return "Bearer"


class IsAttendee(BasePermission):
    def has_permission(self, request, view):
        return isinstance(request.auth, SurveyUser)


def _validated_email(value, field):
    email = str(value or "").strip().lower()
    try:
        validate_email(email)
    except DjangoValidationError:
        raise ValidationError({field: "Enter a valid email address."})
    return email


def _campaign_data(campaign):
    registration_open = getattr(campaign, "active_registration_form_count", None)
    if registration_open is None:
        registration_open = campaign.surveys.filter(purpose=Survey.PURPOSE_REGISTRATION, is_active=True).exists()
    return {
        "id": campaign.pk, "title": campaign.title, "description": campaign.description,
        "start_date": campaign.start_date.isoformat(), "end_date": campaign.end_date.isoformat(),
        "event_time": campaign.event_time, "venue": campaign.venue,
        "organizer_name": campaign.organizer_name, "organizer_email": campaign.organizer_email,
        "theme_color": campaign.theme, "banner_url": campaign.banner.url if campaign.banner else None,
        "registration_open": bool(registration_open),
    }


def _booth_data(booth):
    return {
        "id": booth.pk, "number": booth.number, "name": booth.name, "description": booth.description,
        "category": booth.category, "organization_name": booth.organization_name,
        "x_percent": float(booth.x_percent), "y_percent": float(booth.y_percent),
        "width_percent": float(booth.width_percent), "height_percent": float(booth.height_percent),
        "floor_map_id": booth.floor_map_id,
    }


def _event_or_404(event_id):
    return get_object_or_404(
        Campaign.objects.annotate(active_registration_form_count=Count(
            "surveys", filter=Q(surveys__purpose=Survey.PURPOSE_REGISTRATION, surveys__is_active=True)
        )), pk=event_id, is_active=True,
    )


def _event_attendee(request, event):
    attendee = request.auth
    if attendee.survey.fkcampaign_id != event.pk:
        raise ValidationError({"detail": "This attendee token belongs to another event."})
    if attendee.approval_status != SurveyUser.STATUS_APPROVED:
        raise ValidationError({"detail": "Your registration is awaiting approval."})
    if not event.is_active:
        raise ValidationError({"detail": "This event is no longer active."})
    return attendee


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_events(request):
    events = Campaign.objects.filter(is_active=True).annotate(active_registration_form_count=Count(
        "surveys", filter=Q(surveys__purpose=Survey.PURPOSE_REGISTRATION, surveys__is_active=True)
    )).order_by("start_date")
    return Response([_campaign_data(event) for event in events])


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_event_detail(request, event_id):
    return Response(_campaign_data(_event_or_404(event_id)))


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_registration_form(request, event_id):
    event = _event_or_404(event_id)
    survey = event.surveys.filter(purpose=Survey.PURPOSE_REGISTRATION, is_active=True).order_by("-created_at").first()
    if survey is None:
        return Response({"detail": "Registration is not open."}, status=409)
    questions = [{
        "id": question.pk, "text": strip_tags(question.text or ""),
        "help_text": strip_tags(question.help_text or ""), "type": question.question_type,
        "required": question.is_required, "choices": question.choices or [],
        "allow_other": question.allow_other, "max_checks": question.max_checks,
        "choice_followups": question.choice_followups or {},
    } for question in survey.questions.all()]
    return Response({"event": _campaign_data(event), "survey_id": survey.pk, "questions": questions})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def api_register(request, event_id):
    event = _event_or_404(event_id)
    survey = event.surveys.filter(purpose=Survey.PURPOSE_REGISTRATION, is_active=True).order_by("-created_at").first()
    if survey is None:
        return Response({"detail": "Registration is not open."}, status=409)
    questions = list(survey.questions.all())
    answers = request.data.get("answers") or {}
    if not isinstance(answers, dict):
        raise ValidationError({"answers": "Answers must be an object keyed by question id."})
    identity = {"name": request.data.get("name", ""), "email": request.data.get("email", ""),
        "phone": request.data.get("phone", ""), "organization": request.data.get("organization", ""),
        "participant_type": request.data.get("participant_type", SurveyUser.PARTICIPANT_TYPE_DELEGATE)}
    for question in questions:
        target = Question.IDENTITY_TYPES.get(question.question_type)
        if target:
            value = answers.get(str(question.pk), answers.get(question.pk))
            if value is not None:
                identity[target] = value
    name = str(identity.get("name", "")).strip()
    email = str(identity.get("email", "")).strip().lower()
    if not name:
        raise ValidationError({"name": "Name is required."})
    email = _validated_email(email, "email")
    if not email:
        raise ValidationError({"name": "Name is required.", "email": "Enter a valid email address."})
    if survey.survey_users.filter(email__iexact=email).exists():
        return Response({"detail": "This email is already registered for the event."}, status=409)
    missing, clean_answers = [], {}
    for question in questions:
        raw = answers.get(str(question.pk), answers.get(question.pk))
        if question.question_type in Question.IDENTITY_TYPES:
            raw = identity.get(Question.IDENTITY_TYPES[question.question_type], "")
        if isinstance(raw, dict):
            value = raw.get("value", "")
            other = raw.get("other", "")
            followups = raw.get("followups", {})
        else:
            value, other, followups = raw, "", {}
        has_value = bool(value) or (question.allow_other and bool(other))
        if question.is_required and not has_value:
            missing.append(strip_tags(question.text or "").strip() or f"Question {question.pk}")
        if question.question_type in (Question.TYPE_RADIO, Question.TYPE_SELECT):
            options = question.choices if isinstance(question.choices, list) else []
            if value == "Other" and not question.allow_other:
                raise ValidationError({"answers": f"An 'Other' response is not allowed for {question.text}."})
            if value and options and value not in options and value != "Other":
                raise ValidationError({"answers": f"Choose a valid option for {question.text}."})
        elif question.question_type == Question.TYPE_CHECKBOX:
            value = value if isinstance(value, list) else ([value] if value else [])
            options = question.choices if isinstance(question.choices, list) else []
            if question.max_checks and len(value) > question.max_checks:
                raise ValidationError({"answers": f"Select no more than {question.max_checks} options for {question.text}."})
            if "Other" in value and not question.allow_other:
                raise ValidationError({"answers": f"An 'Other' response is not allowed for {question.text}."})
            if options and any(option not in options and option != "Other" for option in value):
                raise ValidationError({"answers": f"Choose valid options for {question.text}."})
        clean_answers[question.pk] = (value, other, followups)
    if missing:
        raise ValidationError({"answers": "Complete required fields: " + ", ".join(missing)})
    participant_type = str(identity.get("participant_type", SurveyUser.PARTICIPANT_TYPE_DELEGATE)).strip()
    valid_participant_types = {choice[0] for choice in SurveyUser.PARTICIPANT_TYPE_CHOICES}
    if participant_type not in valid_participant_types:
        raise ValidationError({"participant_type": "Choose a valid attendee type."})
    from django.db import transaction
    with transaction.atomic():
        attendee = SurveyUser.objects.create(
            survey=survey, name=name, email=email,
            phone=str(identity.get("phone", "")).strip(),
            organization=str(identity.get("organization", "")).strip(),
            participant_type=participant_type, approval_status=SurveyUser.STATUS_PENDING,
        )
        attendee.reg_no = f"REG{attendee.pk:06d}"
        attendee.save(update_fields=["reg_no"])
        for question in questions:
            if question.question_type in Question.IDENTITY_TYPES:
                continue
            value, other, followups = clean_answers[question.pk]
            if question.question_type in (Question.TYPE_TEXT, Question.TYPE_TEXTAREA, Question.TYPE_MATRIX_ROLES):
                if value:
                    text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value).strip()
                    Answer.objects.create(survey=survey, question=question, user=attendee, answer_text=text)
            elif question.question_type in (Question.TYPE_RADIO, Question.TYPE_SELECT):
                picked = str(value or "").strip()
                if picked or other:
                    answer_text = str(other).strip() if picked == "Other" else None
                    if followups:
                        answer_text = json.dumps(followups, ensure_ascii=False)
                    Answer.objects.create(survey=survey, question=question, user=attendee,
                        selected_options=[picked] if picked else ["Other"], answer_text=answer_text)
            elif question.question_type == Question.TYPE_CHECKBOX:
                picked = list(value or [])
                if other and "Other" not in picked:
                    picked.append("Other")
                if picked or other:
                    answer_text = json.dumps(followups, ensure_ascii=False) if followups else (str(other).strip() or None)
                    Answer.objects.create(survey=survey, question=question, user=attendee,
                        selected_options=picked, answer_text=answer_text)
    _send_registration_received_email(attendee, request=request)
    return Response({
        "id": attendee.pk, "name": attendee.name, "email": attendee.email,
        "registration_code": str(attendee.registration_code),
        "registration_number": attendee.reg_no, "approval_status": attendee.approval_status,
    }, status=201)


@api_view(["GET", "PATCH"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_me(request):
    attendee = request.auth
    if request.method == "PATCH":
        fields = ("name", "email", "phone", "organization")
        if "name" in request.data and not str(request.data["name"]).strip():
            raise ValidationError({"name": "Name cannot be blank."})
        if "email" in request.data:
            email = _validated_email(request.data["email"], "email")
            if SurveyUser.objects.filter(survey=attendee.survey, email__iexact=email).exclude(pk=attendee.pk).exists():
                raise ValidationError({"email": "This email is already registered for the event."})
            attendee.email = email
        for field in fields:
            if field in request.data and field != "email":
                setattr(attendee, field, str(request.data[field]).strip())
        attendee.save(update_fields=[field for field in fields if field in request.data])
    return Response({
        "id": attendee.pk, "name": attendee.name, "email": attendee.email,
        "phone": attendee.phone, "organization": attendee.organization,
        "registration_number": attendee.reg_no, "approval_status": attendee.approval_status,
        "checked_in": attendee.is_checked_in, "qr_sent": attendee.qr_sent,
        "event": _campaign_data(attendee.survey.fkcampaign),
    })


@api_view(["GET"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_event_directory(request, event_id):
    event = _event_or_404(event_id)
    try:
        page = max(1, int(request.query_params.get("page", "1")))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = min(100, max(1, int(request.query_params.get("page_size", "100"))))
    except (TypeError, ValueError):
        page_size = 100
    offset = (page - 1) * page_size

    def page_items(queryset):
        total = queryset.count()
        return list(queryset[offset:offset + page_size]), total > offset + page_size

    employers, employers_more = page_items(
        Employer.objects.filter(campaign=event, is_active=True).select_related("booth__floor_map")
    )
    jobs, jobs_more = page_items(
        Job.objects.filter(employer__campaign=event, employer__is_active=True, is_active=True).select_related("employer")
    )
    now = timezone.now()
    universities, universities_more = page_items(University.objects.filter(campaign=event, is_active=True).prefetch_related(
        Prefetch("programs", queryset=UniversityProgram.objects.filter(is_active=True), to_attr="active_programs")
    ))
    providers, providers_more = page_items(TrainingProvider.objects.filter(campaign=event, is_active=True).prefetch_related(
        Prefetch("promotions", queryset=VoucherPromotion.objects.filter(is_active=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=now)
        ), to_attr="active_promotions")
    ))
    sessions, sessions_more = page_items(EventSession.objects.filter(campaign=event, status=EventSession.STATUS_SCHEDULED).annotate(
        registration_count=Count("registrations", filter=Q(registrations__status=SessionRegistration.STATUS_BOOKED))
    ))
    maps = FloorMap.objects.filter(campaign=event, status=FloorMap.STATUS_PUBLISHED).prefetch_related(
        Prefetch("booths", queryset=Booth.objects.filter(is_active=True), to_attr="active_booths")
    )
    maps, maps_more = page_items(maps)
    attendee = request.auth
    bookmarks = set(JobBookmark.objects.filter(attendee=attendee, job__employer__campaign=event).values_list("job_id", flat=True))
    interview_slots, interview_slots_more = page_items(InterviewSlot.objects.filter(employer__campaign=event, employer__is_active=True,
        status=InterviewSlot.STATUS_OPEN).select_related("employer").prefetch_related(
            Prefetch("bookings", queryset=InterviewBooking.objects.filter(status=InterviewBooking.STATUS_BOOKED),
                     to_attr="active_bookings")
        ))
    return Response({
        "event": _campaign_data(event),
        "pagination": {"page": page, "page_size": page_size, "has_more": {
            "employers": employers_more, "jobs": jobs_more, "universities": universities_more,
            "training_providers": providers_more, "interview_slots": interview_slots_more,
            "sessions": sessions_more, "floor_maps": maps_more,
        }},
        "employers": [{"id": e.pk, "name": e.name, "description": e.description, "website": e.website,
            "contact_email": e.contact_email, "logo_url": e.logo.url if e.logo else None,
            "booth": _booth_data(e.booth) if e.booth else None} for e in employers],
        "jobs": [{"id": j.pk, "employer_id": j.employer_id, "employer": j.employer.name, "title": j.title,
            "description": j.description, "requirements": j.requirements, "employment_type": j.employment_type,
            "experience_level": j.experience_level, "location": j.location, "application_url": j.application_url,
            "application_email": j.application_email, "saved": j.pk in bookmarks} for j in jobs],
        "universities": [{"id": u.pk, "name": u.name, "description": u.description, "website": u.website,
            "programs": [{"id": p.pk, "name": p.name, "description": p.description,
                "eligibility": p.eligibility, "upcoming_batch_info": p.upcoming_batch_info,
                "internship_fresher_info": p.internship_fresher_info} for p in u.active_programs]} for u in universities],
        "training_providers": [{"id": p.pk, "name": p.name, "description": p.description, "website": p.website,
            "promotions": [{"id": v.pk, "title": v.title, "description": v.description, "value": v.value_label,
                "expires_at": v.expires_at.isoformat() if v.expires_at else None, "document_url": v.document.url if v.document else None}
                for v in p.active_promotions]} for p in providers],
        "interview_slots": [{"id": s.pk, "employer": s.employer.name, "date": s.date.isoformat(),
            "start_time": s.start_time.isoformat(), "end_time": s.end_time.isoformat(),
            "capacity": s.capacity, "interviewer_info": s.interviewer_info,
            "options": [{"start_time": t.isoformat(timespec="minutes"), "remaining": max(0, s.capacity - sum(
                1 for booking in s.active_bookings if booking.start_time == t
            ))} for t in interview_start_times(s)]} for s in interview_slots],
        "sessions": [{"id": s.pk, "title": s.title, "type": s.session_type, "description": s.description,
            "date": s.event_date.isoformat(), "start_time": s.start_time.isoformat(), "end_time": s.end_time.isoformat(),
            "location": s.location, "speaker": s.speaker_name, "capacity": s.capacity,
            "booked": s.registration_count, "remaining": None if s.capacity is None else max(0, s.capacity - s.registration_count)} for s in sessions],
        "floor_maps": [{"id": m.pk, "name": m.name, "description": m.description, "version": m.version,
            "image_url": m.image.url, "booths": [_booth_data(b) for b in m.active_booths]} for m in maps],
    })


@api_view(["GET"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_schedule(request):
    attendee = request.auth
    sessions = SessionRegistration.objects.filter(attendee=attendee, status=SessionRegistration.STATUS_BOOKED).select_related("session")
    interviews = InterviewBooking.objects.filter(attendee=attendee, status=InterviewBooking.STATUS_BOOKED).select_related("slot__employer")
    claims = VoucherClaim.objects.filter(attendee=attendee, status=VoucherClaim.STATUS_CLAIMED).select_related("promotion__provider")
    saved_jobs = JobBookmark.objects.filter(attendee=attendee, job__is_active=True).select_related("job__employer")
    return Response({
        "sessions": [{"id": r.session_id, "title": r.session.title, "date": r.session.event_date.isoformat(),
            "start_time": r.session.start_time.isoformat(), "end_time": r.session.end_time.isoformat(), "location": r.session.location} for r in sessions],
        "interviews": [{"booking_id": b.pk, "slot_id": b.slot_id, "employer": b.slot.employer.name,
            "date": b.slot.date.isoformat(), "start_time": b.start_time.isoformat(timespec="minutes")} for b in interviews],
        "saved_jobs": [{"id": b.job_id, "title": b.job.title, "employer": b.job.employer.name} for b in saved_jobs],
        "promotions": [{"claim_id": c.pk, "title": c.promotion.title, "provider": c.promotion.provider.name,
            "promotion_id": c.promotion_id, "instructions": c.promotion.instructions} for c in claims],
    })


@api_view(["POST", "DELETE"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_job_bookmark(request, job_id):
    job = get_object_or_404(Job, pk=job_id, is_active=True, employer__is_active=True)
    attendee = _event_attendee(request, job.employer.campaign)
    bookmark, created = JobBookmark.objects.get_or_create(job=job, attendee=attendee)
    if request.method == "DELETE":
        bookmark.delete()
        return Response(status=204)
    return Response({"saved": True, "created": created})


@api_view(["POST", "DELETE"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_session_registration(request, session_id):
    attendee = request.auth
    session = get_object_or_404(EventSession.objects.select_related("campaign"), pk=session_id)
    _event_attendee(request, session.campaign)
    try:
        if request.method == "DELETE":
            cancel_session_registration(session.pk, attendee)
            return Response(status=204)
        registration = register_for_session(session.pk, attendee)
        return Response({"registration_id": registration.pk, "status": registration.status}, status=201)
    except (AttendeeNotEligibleError, SessionUnavailableError, SessionCapacityError, SessionRegistrationError) as error:
        return Response({"detail": str(error)}, status=409)


@api_view(["POST", "DELETE"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_interview_booking(request, slot_id):
    slot = get_object_or_404(InterviewSlot.objects.select_related("employer__campaign"), pk=slot_id)
    attendee = _event_attendee(request, slot.employer.campaign)
    try:
        if request.method == "DELETE":
            booking = get_object_or_404(InterviewBooking, slot=slot, attendee=attendee, status=InterviewBooking.STATUS_BOOKED)
            cancel_interview_booking(booking.pk, attendee)
            return Response(status=204)
        start_time = time.fromisoformat(str(request.data.get("start_time", "")))
        booking = book_interview(slot.pk, attendee, start_time)
        return Response({"booking_id": booking.pk, "start_time": booking.start_time.isoformat(timespec="minutes")}, status=201)
    except (CareerActionError, ValueError, TypeError) as error:
        return Response({"detail": str(error) or "Choose a valid start_time."}, status=409)


@api_view(["POST", "DELETE"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_voucher_claim(request, promotion_id):
    promotion = get_object_or_404(VoucherPromotion.objects.select_related("provider__campaign"), pk=promotion_id)
    attendee = _event_attendee(request, promotion.provider.campaign)
    try:
        if request.method == "DELETE":
            claim = get_object_or_404(VoucherClaim, promotion=promotion, attendee=attendee, status=VoucherClaim.STATUS_CLAIMED)
            cancel_voucher_claim(claim.pk, attendee)
            return Response(status=204)
        already_claimed = VoucherClaim.objects.filter(
            promotion=promotion, attendee=attendee, status=VoucherClaim.STATUS_CLAIMED
        ).exists()
        claim = claim_voucher(promotion.pk, attendee)
        if attendee.email and not already_claimed:
            send_mail(
                f"Promotion claimed: {promotion.title}",
                f"You claimed {promotion.title} for {promotion.provider.campaign.title}.\n\n"
                f"{promotion.instructions}\n\nValue: {promotion.value_label}\n",
                None, [attendee.email], fail_silently=True,
            )
        return Response({"claim_id": claim.pk, "status": claim.status, "instructions": promotion.instructions}, status=201)
    except CareerActionError as error:
        return Response({"detail": str(error)}, status=409)


@api_view(["GET"])
@authentication_classes([AttendeeBearerAuthentication])
@permission_classes([IsAttendee])
def api_check_in(request):
    attendee = request.auth
    qr_data = None
    # Approval authorizes the attendee to use their check-in credential.
    # qr_sent tracks email delivery only; it should not control in-app display.
    if attendee.approval_status == SurveyUser.STATUS_APPROVED:
        buffer = BytesIO()
        qrcode.make(str(attendee.registration_code)).save(buffer, format="PNG")
        qr_data = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    return Response({"checked_in": attendee.is_checked_in, "registration_number": attendee.reg_no,
        "qr_sent": attendee.qr_sent, "approval_status": attendee.approval_status, "qr_code": qr_data})
