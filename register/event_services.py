from django.db import transaction

from .models import EventSession, SessionRegistration, SurveyUser


class SessionRegistrationError(Exception):
    """A session booking failed a business rule."""


class SessionCapacityError(SessionRegistrationError):
    pass


class SessionUnavailableError(SessionRegistrationError):
    pass


class AttendeeNotEligibleError(SessionRegistrationError):
    pass


@transaction.atomic
def register_for_session(session_id, attendee):
    """Create or restore one attendee booking without exceeding capacity."""
    session = EventSession.objects.select_for_update().select_related("campaign").get(pk=session_id)
    if (not session.campaign.is_active
            or session.status != EventSession.STATUS_SCHEDULED):
        raise SessionUnavailableError("This session is not open for registration.")
    if (attendee.approval_status != SurveyUser.STATUS_APPROVED
            or attendee.survey.fkcampaign_id != session.campaign_id):
        raise AttendeeNotEligibleError("Use an approved registration for this event to book a session.")

    registration = SessionRegistration.objects.filter(
        session=session, attendee=attendee
    ).first()
    if registration and registration.status == SessionRegistration.STATUS_BOOKED:
        return registration

    booked = SessionRegistration.objects.filter(
        session=session, status=SessionRegistration.STATUS_BOOKED
    ).count()
    if session.capacity is not None and booked >= session.capacity:
        raise SessionCapacityError("This session is full.")

    if registration:
        registration.status = SessionRegistration.STATUS_BOOKED
        registration.save(update_fields=["status", "updated_at"])
        return registration
    return SessionRegistration.objects.create(session=session, attendee=attendee)


@transaction.atomic
def cancel_session_registration(session_id, attendee):
    registration = SessionRegistration.objects.select_for_update().filter(
        session_id=session_id,
        attendee=attendee,
        status=SessionRegistration.STATUS_BOOKED,
    ).first()
    if not registration:
        raise SessionRegistrationError("There is no active booking to cancel.")
    registration.status = SessionRegistration.STATUS_CANCELLED
    registration.save(update_fields=["status", "updated_at"])
    return registration
