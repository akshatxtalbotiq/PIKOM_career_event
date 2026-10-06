from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone

from .models import (
    InterviewBooking, InterviewSlot, SurveyUser, VoucherClaim, VoucherPromotion,
)


class CareerActionError(Exception):
    pass


class CareerEligibilityError(CareerActionError):
    pass


class CareerUnavailableError(CareerActionError):
    pass


class CareerCapacityError(CareerActionError):
    pass


def interview_start_times(slot):
    if slot.booking_mode == InterviewSlot.MODE_FIXED:
        return [slot.start_time]
    duration = slot.slot_duration_minutes
    if not duration or duration < 1:
        return []
    current = datetime.combine(slot.date, slot.start_time)
    end = datetime.combine(slot.date, slot.end_time)
    step = timedelta(minutes=duration)
    result = []
    while current + step <= end:
        result.append(current.time())
        current += step
    return result


def _eligible(attendee, campaign):
    if (attendee.approval_status != SurveyUser.STATUS_APPROVED or not attendee.survey_id
            or attendee.survey.fkcampaign_id != campaign.pk):
        raise CareerEligibilityError("Only approved attendees for this event can use this feature.")


@transaction.atomic
def book_interview(slot_id, attendee, start_time):
    slot = InterviewSlot.objects.select_for_update().select_related("employer__campaign").get(pk=slot_id)
    employer, campaign = slot.employer, slot.employer.campaign
    _eligible(attendee, campaign)
    if not campaign.is_active or not employer.is_active or slot.status != InterviewSlot.STATUS_OPEN:
        raise CareerUnavailableError("This interview slot is not available.")
    if start_time not in interview_start_times(slot):
        raise CareerUnavailableError("Choose a valid interview time.")
    existing = InterviewBooking.objects.filter(slot=slot, attendee=attendee, status=InterviewBooking.STATUS_BOOKED).first()
    if existing:
        if existing.start_time == start_time:
            return existing
        raise CareerUnavailableError("You already have a booking with this employer for this slot.")
    count = InterviewBooking.objects.filter(slot=slot, start_time=start_time, status=InterviewBooking.STATUS_BOOKED).count()
    if count >= slot.capacity:
        raise CareerCapacityError("That interview time is full.")
    booking, _ = InterviewBooking.objects.update_or_create(
        slot=slot, attendee=attendee, start_time=start_time,
        defaults={"status": InterviewBooking.STATUS_BOOKED},
    )
    return booking


@transaction.atomic
def cancel_interview_booking(booking_id, attendee):
    booking = InterviewBooking.objects.select_for_update().get(pk=booking_id, attendee=attendee)
    if booking.status != InterviewBooking.STATUS_BOOKED:
        raise CareerUnavailableError("This interview booking is already cancelled.")
    booking.status = InterviewBooking.STATUS_CANCELLED
    booking.save(update_fields=["status", "updated_at"])
    return booking


@transaction.atomic
def claim_voucher(promotion_id, attendee):
    promotion = VoucherPromotion.objects.select_for_update().select_related("provider__campaign").get(pk=promotion_id)
    campaign = promotion.provider.campaign
    _eligible(attendee, campaign)
    if not campaign.is_active or not promotion.provider.is_active or not promotion.is_active:
        raise CareerUnavailableError("This promotion is not available.")
    if promotion.expires_at and promotion.expires_at <= timezone.now():
        raise CareerUnavailableError("This promotion has expired.")
    existing = VoucherClaim.objects.filter(promotion=promotion, attendee=attendee).first()
    if existing and existing.status == VoucherClaim.STATUS_CLAIMED:
        return existing
    if promotion.max_claims is not None and VoucherClaim.objects.filter(
        promotion=promotion, status=VoucherClaim.STATUS_CLAIMED
    ).count() >= promotion.max_claims:
        raise CareerCapacityError("This promotion has reached its claim limit.")
    if existing:
        existing.status = VoucherClaim.STATUS_CLAIMED
        existing.save(update_fields=["status", "updated_at"])
        return existing
    return VoucherClaim.objects.create(promotion=promotion, attendee=attendee)


@transaction.atomic
def cancel_voucher_claim(claim_id, attendee):
    claim = VoucherClaim.objects.select_for_update().get(pk=claim_id, attendee=attendee)
    if claim.status != VoucherClaim.STATUS_CLAIMED:
        raise CareerUnavailableError("This promotion claim is already cancelled.")
    claim.status = VoucherClaim.STATUS_CANCELLED
    claim.save(update_fields=["status", "updated_at"])
    return claim
