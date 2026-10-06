from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .event_services import (
    AttendeeNotEligibleError, SessionCapacityError,
    cancel_session_registration, register_for_session,
)
from .career_services import (
    CareerCapacityError, CareerEligibilityError, book_interview,
    cancel_interview_booking, cancel_voucher_claim, claim_voucher,
    interview_start_times,
)
from .models import (
    Booth, Campaign, CampaignTeam, Employer, EventSession, FloorMap,
    InterviewBooking, InterviewSlot, Job, JobBookmark, SessionRegistration,
    Answer, Question, Survey, SurveyUser, TrainingProvider, University, UniversityProgram,
    VoucherClaim, VoucherPromotion,
)


class PhaseOneEventManagementTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin = self.User.objects.create_superuser(
            username="phase1-admin",
            email="admin@example.com",
            password="test-password",
        )
        self.client.force_login(self.admin)

    def campaign_payload(self, **overrides):
        payload = {
            "title": "PIKOM Career Festival",
            "description": "Meet employers and explore career opportunities.",
            "organizer_name": "Event Team",
            "organizer_email": "events@example.com",
            "organizer_phone": "+60123456789",
            "start_date": "2026-11-02",
            "end_date": "2026-11-03",
            "is_active": "true",
            "theme_color": "#123abc",
            "pic_email": "events@example.com",
            "prompt_checkin_info": "true",
        }
        payload.update(overrides)
        return payload

    def create_campaign(self, **overrides):
        response = self.client.post(
            reverse("create_campaign"), self.campaign_payload(**overrides)
        )
        self.assertEqual(response.status_code, 200, response.content)
        return Campaign.objects.get(pk=response.json()["id"])

    def test_create_event_saves_profile_and_full_date_range(self):
        campaign = self.create_campaign()

        self.assertEqual(campaign.title, "PIKOM Career Festival")
        self.assertEqual(campaign.description, "Meet employers and explore career opportunities.")
        self.assertEqual(campaign.organizer_name, "Event Team")
        self.assertEqual(campaign.organizer_email, "events@example.com")
        self.assertEqual(campaign.organizer_phone, "+60123456789")
        self.assertEqual(campaign.theme, "#123abc")
        self.assertEqual(timezone.localtime(campaign.start_date).date(), date(2026, 11, 2))
        self.assertEqual(timezone.localtime(campaign.end_date).date(), date(2026, 11, 3))
        self.assertEqual(timezone.localtime(campaign.start_date).hour, 0)
        self.assertEqual(timezone.localtime(campaign.end_date).hour, 23)
        self.assertEqual(timezone.localtime(campaign.end_date).minute, 59)

    def test_create_event_rejects_invalid_date_range(self):
        response = self.client.post(
            reverse("create_campaign"),
            self.campaign_payload(start_date="2026-11-04", end_date="2026-11-03"),
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Campaign.objects.count(), 0)

    def test_create_event_requires_a_title(self):
        response = self.client.post(
            reverse("create_campaign"), self.campaign_payload(title="   ")
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Campaign.objects.count(), 0)

    def test_create_event_rejects_oversized_banner(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        response = self.client.post(
            reverse("create_campaign"),
            {
                **self.campaign_payload(),
                "banner": SimpleUploadedFile(
                    "banner.png", b"x" * (5 * 1024 * 1024 + 1), content_type="image/png"
                ),
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Campaign.objects.count(), 0)

    def test_non_admin_cannot_create_event_without_permission(self):
        self.client.logout()
        organizer = self.User.objects.create_user(
            username="organizer", password="test-password"
        )
        self.client.force_login(organizer)

        response = self.client.post(
            reverse("create_campaign"), self.campaign_payload()
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Campaign.objects.count(), 0)

    def test_event_editor_endpoint_requires_team_access(self):
        campaign = self.create_campaign()
        self.client.logout()
        organizer = self.User.objects.create_user(
            username="organizer", password="test-password"
        )
        self.client.force_login(organizer)

        denied = self.client.get(reverse("get_campaign", args=[campaign.pk]))
        self.assertEqual(denied.status_code, 403)

        CampaignTeam.objects.create(campaign=campaign, user=organizer)
        allowed = self.client.get(reverse("get_campaign", args=[campaign.pk]))
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["organizer_email"], "events@example.com")

    def test_event_description_and_banner_fallback_render_on_form_and_email(self):
        import tempfile

        from django.core.files.base import ContentFile
        from django.test import override_settings

        campaign = self.create_campaign()
        survey = Survey.objects.create(
            title="Festival registration", slug="festival-registration",
            fkcampaign=campaign, purpose=Survey.PURPOSE_REGISTRATION, is_active=True,
        )
        attendee = SurveyUser.objects.create(
            survey=survey, name="Attendee", email="attendee@example.com",
        )

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                campaign.banner.save("festival.png", ContentFile(b"image bytes"), save=True)
                public_response = self.client.get(
                    reverse("form_public", args=[survey.slug])
                )

                from .views import _event_email_ctx

                email_context = _event_email_ctx(attendee)

        self.assertEqual(public_response.status_code, 200)
        self.assertContains(public_response, "Meet employers and explore career opportunities.")
        self.assertContains(public_response, campaign.banner.url)
        self.assertIn(campaign.banner.url, email_context["banner_url"])

    def test_dashboard_shows_registration_status_and_attendee_counts(self):
        campaign = self.create_campaign()
        survey = Survey.objects.create(
            title="Festival registration", fkcampaign=campaign,
            purpose=Survey.PURPOSE_REGISTRATION, is_active=True,
        )
        SurveyUser.objects.create(
            survey=survey, name="Approved attendee", email="approved@example.com",
            approval_status=SurveyUser.STATUS_APPROVED, is_checked_in=True,
        )
        SurveyUser.objects.create(
            survey=survey, name="Pending attendee", email="pending@example.com",
            approval_status=SurveyUser.STATUS_PENDING,
        )

        response = self.client.get(reverse("campaign_dashboard", args=[campaign.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["registration_status"], "Open")
        self.assertEqual(response.context["kpis"]["total"], 2)
        self.assertEqual(response.context["kpis"]["approved"], 1)
        self.assertEqual(response.context["kpis"]["pending"], 1)
        self.assertEqual(response.context["kpis"]["checked_in"], 1)

    def test_dashboard_distinguishes_closed_and_unconfigured_registration(self):
        campaign = self.create_campaign()

        unconfigured = self.client.get(
            reverse("campaign_dashboard", args=[campaign.pk])
        )
        self.assertEqual(unconfigured.context["registration_status"], "Not configured")
        self.assertEqual(unconfigured.context["kpis"]["total"], 0)
        self.assertFalse(unconfigured.context["has_data"])

        Survey.objects.create(
            title="Closed registration", fkcampaign=campaign,
            purpose=Survey.PURPOSE_REGISTRATION, is_active=False,
        )
        closed = self.client.get(reverse("campaign_dashboard", args=[campaign.pk]))
        self.assertEqual(closed.context["registration_status"], "Closed")

    def test_event_dashboard_requires_team_access(self):
        campaign = self.create_campaign()
        self.client.logout()
        organizer = self.User.objects.create_user(
            username="organizer", password="test-password"
        )
        self.client.force_login(organizer)

        denied = self.client.get(reverse("campaign_dashboard", args=[campaign.pk]))
        self.assertEqual(denied.status_code, 403)

        CampaignTeam.objects.create(campaign=campaign, user=organizer)
        allowed = self.client.get(reverse("campaign_dashboard", args=[campaign.pk]))
        self.assertEqual(allowed.status_code, 200)


class PhaseTwoEventInfrastructureTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin = self.User.objects.create_superuser(
            username="phase2-admin", email="phase2-admin@example.com", password="password"
        )
        self.client.force_login(self.admin)
        self.campaign = Campaign.objects.create(
            title="Festival", start_date=timezone.datetime(2026, 11, 2, tzinfo=timezone.get_current_timezone()),
            end_date=timezone.datetime(2026, 11, 3, 23, 59, tzinfo=timezone.get_current_timezone()),
        )
        self.survey = Survey.objects.create(
            title="Registration", fkcampaign=self.campaign,
            purpose=Survey.PURPOSE_REGISTRATION,
        )

    def create_attendee(self, name, status=SurveyUser.STATUS_APPROVED):
        return SurveyUser.objects.create(
            survey=self.survey, name=name, email=f"{name.lower().replace(' ', '.')}@example.com",
            approval_status=status,
        )

    def create_session(self, **overrides):
        values = {
            "campaign": self.campaign,
            "title": "Career panel",
            "session_type": "panel",
            "event_date": "2026-11-02",
            "start_time": "10:00",
            "end_time": "11:00",
            "capacity": 2,
        }
        values.update(overrides)
        return EventSession.objects.create(**values)

    def test_organizer_can_create_sessions_and_agenda_is_ordered(self):
        response = self.client.post(
            reverse("event_infrastructure", args=[self.campaign.pk]),
            {
                "action": "save_session", "title": "Afternoon panel", "session_type": "panel",
                "event_date": "2026-11-02", "start_time": "14:00", "end_time": "15:00",
                "capacity": "40", "location": "Stage A", "speaker_name": "A. Speaker",
                "description": "Career paths and hiring trends.", "status": "scheduled",
            },
        )
        self.assertEqual(response.status_code, 302)
        EventSession.objects.create(
            campaign=self.campaign, title="Morning keynote", session_type="speaking",
            event_date="2026-11-02", start_time="09:00", end_time="09:30",
        )
        sessions = list(EventSession.objects.filter(campaign=self.campaign))
        self.assertEqual([s.title for s in sessions], ["Morning keynote", "Afternoon panel"])
        self.assertEqual(sessions[1].duration_minutes, 60)

    def test_session_form_rejects_invalid_times_and_dates_outside_event(self):
        response = self.client.post(
            reverse("event_infrastructure", args=[self.campaign.pk]),
            {
                "action": "save_session", "title": "Invalid session", "session_type": "panel",
                "event_date": "2026-11-04", "start_time": "11:00", "end_time": "10:00",
                "status": "scheduled",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(EventSession.objects.exists())
        self.assertTrue(response.context["session_form"].errors)

    def test_event_infrastructure_requires_event_team_access(self):
        self.client.logout()
        organizer = self.User.objects.create_user(username="outside-organizer", password="password")
        self.client.force_login(organizer)
        url = reverse("event_infrastructure", args=[self.campaign.pk])
        self.assertEqual(self.client.get(url).status_code, 403)
        CampaignTeam.objects.create(campaign=self.campaign, user=organizer)
        self.assertEqual(self.client.get(url).status_code, 200)

    def test_session_capacity_cancellation_and_rebooking(self):
        session = self.create_session(capacity=1)
        first = self.create_attendee("First Attendee")
        second = self.create_attendee("Second Attendee")

        booking = register_for_session(session.pk, first)
        self.assertEqual(booking.status, SessionRegistration.STATUS_BOOKED)
        self.assertEqual(session.booked_count, 1)
        with self.assertRaises(SessionCapacityError):
            register_for_session(session.pk, second)

        cancel_session_registration(session.pk, first)
        rebooked = register_for_session(session.pk, second)
        self.assertEqual(rebooked.attendee_id, second.pk)
        self.assertEqual(session.booked_count, 1)

    def test_session_registration_requires_approved_attendee_for_same_event(self):
        session = self.create_session()
        pending = self.create_attendee("Pending Attendee", SurveyUser.STATUS_PENDING)
        with self.assertRaises(AttendeeNotEligibleError):
            register_for_session(session.pk, pending)

    def test_attendee_can_view_book_and_cancel_session_with_registration_token(self):
        session = self.create_session()
        attendee = self.create_attendee("Token Attendee")
        url = reverse(
            "attendee_session_registration", args=[session.pk, attendee.registration_code]
        )
        self.assertEqual(self.client.get(url).status_code, 200)
        booked = self.client.post(url, {"action": "register"})
        self.assertEqual(booked.status_code, 302)
        registration = SessionRegistration.objects.get(session=session, attendee=attendee)
        self.assertEqual(registration.status, SessionRegistration.STATUS_BOOKED)
        self.client.post(url, {"action": "cancel"})
        registration.refresh_from_db()
        self.assertEqual(registration.status, SessionRegistration.STATUS_CANCELLED)

    def test_attendee_agenda_lists_sessions_and_rejects_cross_event_token(self):
        session = self.create_session()
        attendee = self.create_attendee("Agenda Attendee")
        agenda = self.client.get(reverse("attendee_event_sessions", args=[attendee.registration_code]))
        self.assertEqual(agenda.status_code, 200)
        self.assertContains(agenda, session.title)

        other_campaign = Campaign.objects.create(
            title="Other Festival", start_date=self.campaign.start_date,
            end_date=self.campaign.end_date,
        )
        other_session = self.create_session(campaign=other_campaign, title="Other event session")
        cross_event = reverse(
            "attendee_session_registration", args=[other_session.pk, attendee.registration_code]
        )
        self.assertEqual(self.client.get(cross_event).status_code, 404)

    def test_registration_emails_link_to_the_attendee_agenda(self):
        from django.template.loader import render_to_string
        from django.urls import reverse
        from .views import _event_email_ctx

        attendee = self.create_attendee("Email Attendee")
        agenda_path = reverse(
            "attendee_event_sessions", args=[attendee.registration_code]
        )
        received_html = render_to_string(
            "register/email/email_registration_received.html",
            _event_email_ctx(attendee, intro_field="thankyou_intro"),
        )
        qr_html = render_to_string(
            "register/email/email_registration_qr.html",
            _event_email_ctx(attendee, intro_field="qr_email_intro"),
        )

        self.assertIn(agenda_path, received_html)
        self.assertIn(agenda_path, qr_html)

    def test_organizer_can_upload_floor_map_and_position_booth(self):
        import io
        import tempfile

        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile
        from django.test import override_settings

        image_buffer = io.BytesIO()
        Image.new("RGB", (80, 60), "white").save(image_buffer, format="PNG")
        image_content = image_buffer.getvalue()
        map_url = reverse("event_infrastructure", args=[self.campaign.pk])

        with tempfile.TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                map_response = self.client.post(
                    map_url,
                    {
                        "action": "save_floor_map", "name": "Main hall", "version": "1",
                        "description": "Exhibition level", "status": "published",
                        "image": SimpleUploadedFile("hall.png", image_content, content_type="image/png"),
                    },
                )
                self.assertEqual(map_response.status_code, 302)
                floor_map = FloorMap.objects.get(campaign=self.campaign)

                edit_map_response = self.client.post(
                    map_url,
                    {
                        "action": "save_floor_map", "item_id": floor_map.pk,
                        "name": "Main hall updated", "version": "2",
                        "description": "Updated exhibition level", "status": "published",
                    },
                )
                self.assertEqual(edit_map_response.status_code, 302)

                booth_response = self.client.post(
                    map_url,
                    {
                        "action": "save_booth", "floor_map": floor_map.pk,
                        "number": "A12", "name": "PIKOM Careers", "organization_name": "PIKOM",
                        "category": "Careers", "x_percent": "20", "y_percent": "30",
                        "width_percent": "10", "height_percent": "8", "is_active": "on",
                    },
                )
                self.assertEqual(booth_response.status_code, 302)
                booth = Booth.objects.get(floor_map=floor_map)

                edit_booth_response = self.client.post(
                    map_url,
                    {
                        "action": "save_booth", "item_id": booth.pk,
                        "floor_map": floor_map.pk, "number": "A12", "name": "PIKOM Careers updated",
                        "organization_name": "PIKOM", "category": "Careers",
                        "x_percent": "25", "y_percent": "35", "width_percent": "10",
                        "height_percent": "8", "is_active": "on",
                    },
                )
                self.assertEqual(edit_booth_response.status_code, 302)

        booth = Booth.objects.get(floor_map=floor_map)
        floor_map.refresh_from_db()
        self.assertEqual(floor_map.name, "Main hall updated")
        self.assertTrue(floor_map.image.name)
        self.assertEqual(booth.name, "PIKOM Careers updated")
        self.assertEqual(str(booth.x_percent), "25.00")
        self.assertEqual(str(booth.y_percent), "35.00")
        self.assertEqual(booth.organization_name, "PIKOM")


class PhaseThreeCareerModulesTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin = self.User.objects.create_superuser(
            username="phase3-admin", email="phase3-admin@example.com", password="password"
        )
        self.client.force_login(self.admin)
        self.campaign = Campaign.objects.create(
            title="Career Festival",
            start_date=timezone.datetime(2026, 11, 2, tzinfo=timezone.get_current_timezone()),
            end_date=timezone.datetime(2026, 11, 3, 23, 59, tzinfo=timezone.get_current_timezone()),
        )
        self.survey = Survey.objects.create(
            title="Career registration", fkcampaign=self.campaign,
            purpose=Survey.PURPOSE_REGISTRATION,
        )
        self.employer = Employer.objects.create(campaign=self.campaign, name="Acme")
        self.provider = TrainingProvider.objects.create(campaign=self.campaign, name="LearnCo")

    def attendee(self, name, status=SurveyUser.STATUS_APPROVED, survey=None):
        return SurveyUser.objects.create(
            survey=survey or self.survey, name=name, email=f"{name.lower()}@example.com",
            approval_status=status,
        )

    def test_organizer_creates_scoped_employer_job_university_provider_and_promotion(self):
        url = reverse("event_career", args=[self.campaign.pk])
        self.assertEqual(self.client.post(url, {"action": "save_employer", "name": "New Employer", "is_active": "on"}).status_code, 302)
        employer = Employer.objects.get(name="New Employer")
        self.assertEqual(employer.campaign, self.campaign)
        self.assertEqual(self.client.post(url, {
            "action": "save_job", "employer": employer.pk, "title": "Engineer",
            "employment_type": "full_time", "is_active": "on",
        }).status_code, 302)
        self.assertTrue(Job.objects.filter(employer=employer, title="Engineer").exists())
        self.assertEqual(self.client.post(url, {"action": "save_university", "name": "PIKOM University", "is_active": "on"}).status_code, 302)
        university = University.objects.get(name="PIKOM University")
        self.assertEqual(self.client.post(url, {
            "action": "save_program", "university": university.pk, "name": "AI Diploma", "is_active": "on",
        }).status_code, 302)
        self.assertTrue(UniversityProgram.objects.filter(university=university).exists())
        self.assertEqual(self.client.post(url, {
            "action": "save_promotion", "provider": self.provider.pk, "title": "Course discount",
            "max_claims": 3, "is_active": "on",
        }).status_code, 302)
        self.assertTrue(VoucherPromotion.objects.filter(provider=self.provider).exists())

    def test_organizer_access_is_event_scoped(self):
        other = Campaign.objects.create(title="Other", start_date=self.campaign.start_date, end_date=self.campaign.end_date)
        organizer = self.User.objects.create_user(username="phase3-organizer", password="password")
        self.client.force_login(organizer)
        self.assertEqual(self.client.get(reverse("event_career", args=[other.pk])).status_code, 403)
        CampaignTeam.objects.create(campaign=self.campaign, user=organizer)
        self.assertEqual(self.client.get(reverse("event_career", args=[self.campaign.pk])).status_code, 200)
        other_employer = Employer.objects.create(campaign=other, name="Other Co")
        response = self.client.post(reverse("event_career", args=[self.campaign.pk]), {
            "action": "save_job", "employer": other_employer.pk, "title": "Cross-event job",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Job.objects.filter(title="Cross-event job").exists())

    def test_interview_open_times_capacity_cancellation_and_rebooking(self):
        slot = InterviewSlot.objects.create(
            employer=self.employer, date="2026-11-02", start_time="10:00", end_time="11:00",
            booking_mode=InterviewSlot.MODE_OPEN, slot_duration_minutes=30, capacity=1,
        )
        slot.refresh_from_db()
        self.assertEqual([t.isoformat(timespec="minutes") for t in interview_start_times(slot)], ["10:00", "10:30"])
        first, second = self.attendee("First"), self.attendee("Second")
        booking = book_interview(slot.pk, first, timezone.datetime.strptime("10:00", "%H:%M").time())
        with self.assertRaises(CareerCapacityError):
            book_interview(slot.pk, second, booking.start_time)
        cancel_interview_booking(booking.pk, first)
        rebooked = book_interview(slot.pk, second, booking.start_time)
        self.assertEqual(rebooked.status, InterviewBooking.STATUS_BOOKED)

    def test_interviews_require_approved_attendee_of_same_event_and_valid_time(self):
        slot = InterviewSlot.objects.create(
            employer=self.employer, date="2026-11-02", start_time="10:00", end_time="11:00",
            capacity=1,
        )
        pending = self.attendee("Pending", SurveyUser.STATUS_PENDING)
        with self.assertRaises(CareerEligibilityError):
            book_interview(slot.pk, pending, slot.start_time)
        other_campaign = Campaign.objects.create(title="Other", start_date=self.campaign.start_date, end_date=self.campaign.end_date)
        other_survey = Survey.objects.create(title="Other registration", fkcampaign=other_campaign, purpose=Survey.PURPOSE_REGISTRATION)
        outsider = self.attendee("Outsider", survey=other_survey)
        with self.assertRaises(CareerEligibilityError):
            book_interview(slot.pk, outsider, slot.start_time)

    def test_voucher_claim_limit_cancel_and_reclaim(self):
        promotion = VoucherPromotion.objects.create(provider=self.provider, title="Discount", max_claims=1)
        first, second = self.attendee("Claimant"), self.attendee("Waiting")
        claim = claim_voucher(promotion.pk, first)
        with self.assertRaises(CareerCapacityError):
            claim_voucher(promotion.pk, second)
        cancel_voucher_claim(claim.pk, first)
        reclaimed = claim_voucher(promotion.pk, second)
        self.assertEqual(reclaimed.status, VoucherClaim.STATUS_CLAIMED)

    def test_attendee_hub_is_token_scoped_and_email_links_to_it(self):
        job = Job.objects.create(employer=self.employer, title="Data analyst", application_url="https://example.com/apply")
        attendee = self.attendee("Token Attendee")
        url = reverse("attendee_career_hub", args=[attendee.registration_code])
        self.assertContains(self.client.get(url), job.title)
        self.client.post(url, {"action": "bookmark", "job_id": job.pk})
        self.assertTrue(JobBookmark.objects.filter(job=job, attendee=attendee).exists())
        other = Campaign.objects.create(title="Other", start_date=self.campaign.start_date, end_date=self.campaign.end_date)
        other_employer = Employer.objects.create(campaign=other, name="Hidden Co")
        Job.objects.create(employer=other_employer, title="Hidden role")
        self.assertNotContains(self.client.get(url), "Hidden role")
        from django.template.loader import render_to_string
        from .views import _event_email_ctx
        from django.urls import reverse as url_reverse
        html = render_to_string("register/email/email_registration_received.html", _event_email_ctx(attendee))
        self.assertIn(url_reverse("attendee_career_hub", args=[attendee.registration_code]), html)


class PhaseFourAttendeeAPITests(TestCase):
    def setUp(self):
        from rest_framework.test import APIClient

        self.client = APIClient()
        self.campaign = Campaign.objects.create(
            title="API Festival", start_date=timezone.datetime(2026, 11, 2, tzinfo=timezone.get_current_timezone()),
            end_date=timezone.datetime(2026, 11, 3, 23, 59, tzinfo=timezone.get_current_timezone()),
        )
        self.survey = Survey.objects.create(
            title="API registration", fkcampaign=self.campaign,
            purpose=Survey.PURPOSE_REGISTRATION, is_active=True,
        )
        self.attendee = SurveyUser.objects.create(
            survey=self.survey, name="API Attendee", email="api@example.com",
            approval_status=SurveyUser.STATUS_APPROVED,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.attendee.registration_code}")
        self.employer = Employer.objects.create(campaign=self.campaign, name="API Employer")

    def test_event_list_and_detail_are_public_and_event_scoped(self):
        self.client.credentials()
        response = self.client.get("/api/events/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["title"], "API Festival")
        self.assertEqual(self.client.get(f"/api/events/{self.campaign.pk}/").data["venue"], "")

    def test_api_registration_returns_private_token_and_pending_status(self):
        import os
        from unittest.mock import patch
        from django.core import mail
        from django.test import override_settings

        with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            with patch.dict(os.environ, {"ATTENDEE_APP_URL": "https://attendee.example"}):
                self.client.credentials()
                response = self.client.post(f"/api/events/{self.campaign.pk}/register/", {
                    "name": "New Attendee", "email": "new@example.com", "phone": "123", "organization": "PIKOM",
                }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["approval_status"], SurveyUser.STATUS_PENDING)
        self.assertTrue(response.data["registration_code"])
        self.assertTrue(SurveyUser.objects.filter(email="new@example.com", reg_no=response.data["registration_number"]).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(f"https://attendee.example/login?token={response.data['registration_code']}", mail.outbox[0].alternatives[0][0])

    def test_registration_form_schema_and_custom_answers_are_supported(self):
        name_question = Question.objects.create(
            survey=self.survey, number=1, text="Full name", question_type=Question.TYPE_IDENTITY_NAME,
        )
        email_question = Question.objects.create(
            survey=self.survey, number=2, text="Email", question_type=Question.TYPE_IDENTITY_EMAIL,
        )
        custom_question = Question.objects.create(
            survey=self.survey, number=3, text="What are you interested in?", question_type=Question.TYPE_TEXT,
        )
        choice_question = Question.objects.create(
            survey=self.survey, number=4, text="Preferred track", question_type=Question.TYPE_RADIO,
            choices=["AI", "Cloud"],
        )
        self.client.credentials()
        schema = self.client.get(f"/api/events/{self.campaign.pk}/registration-form/")
        self.assertEqual(schema.status_code, 200)
        self.assertEqual(len(schema.data["questions"]), 4)
        response = self.client.post(f"/api/events/{self.campaign.pk}/register/", {
            "answers": {
                str(name_question.pk): "Custom Form Attendee", str(email_question.pk): "custom@example.com",
                str(custom_question.pk): "AI roles", str(choice_question.pk): "AI",
            },
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Answer.objects.filter(question=custom_question, answer_text="AI roles").exists())
        self.assertTrue(Answer.objects.filter(question=choice_question, selected_options=["AI"]).exists())

    def test_attendee_token_authentication_and_event_directory(self):
        response = self.client.get(f"/api/events/{self.campaign.pk}/directory/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["employers"][0]["name"], self.employer.name)
        self.assertEqual(self.client.get("/api/me/").data["email"], self.attendee.email)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer 00000000-0000-0000-0000-000000000000")
        self.assertEqual(self.client.get("/api/me/").status_code, 401)

    def test_attendee_can_update_own_profile_only(self):
        response = self.client.patch("/api/me/", {"name": "Updated Attendee", "organization": "PIKOM"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.attendee.refresh_from_db()
        self.assertEqual(self.attendee.name, "Updated Attendee")
        self.assertEqual(self.attendee.organization, "PIKOM")

    def test_booking_and_bookmark_api_actions_and_schedule(self):
        job = Job.objects.create(employer=self.employer, title="API Engineer")
        slot = InterviewSlot.objects.create(
            employer=self.employer, date="2026-11-02", start_time="10:00", end_time="11:00", capacity=1,
        )
        session = EventSession.objects.create(
            campaign=self.campaign, title="API Session", session_type="panel", event_date="2026-11-02",
            start_time="09:00", end_time="10:00", capacity=1,
        )
        self.assertEqual(self.client.post(f"/api/jobs/{job.pk}/bookmark/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/sessions/{session.pk}/registration/").status_code, 201)
        directory = self.client.get(f"/api/events/{self.campaign.pk}/directory/").data
        self.assertEqual(directory["sessions"][0]["booked"], 1)
        self.assertEqual(directory["sessions"][0]["remaining"], 0)
        booking_response = self.client.post(f"/api/interview-slots/{slot.pk}/booking/", {"start_time": "10:00"}, format="json")
        self.assertEqual(booking_response.status_code, 201)
        schedule = self.client.get("/api/me/schedule/").data
        self.assertEqual(len(schedule["sessions"]), 1)
        self.assertEqual(len(schedule["interviews"]), 1)
        self.assertEqual(len(schedule["saved_jobs"]), 1)
        self.assertEqual(self.client.delete(f"/api/interview-slots/{slot.pk}/booking/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/jobs/{job.pk}/bookmark/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/sessions/{session.pk}/registration/").status_code, 204)

    def test_pending_attendee_can_read_but_cannot_book(self):
        self.attendee.approval_status = SurveyUser.STATUS_PENDING
        self.attendee.save(update_fields=["approval_status"])
        session = EventSession.objects.create(
            campaign=self.campaign, title="Closed for pending", session_type="panel", event_date="2026-11-02",
            start_time="09:00", end_time="10:00", capacity=1,
        )
        self.assertEqual(self.client.get("/api/me/").status_code, 200)
        self.assertEqual(self.client.post(f"/api/sessions/{session.pk}/registration/").status_code, 400)

    def test_check_in_status_is_read_only_and_event_schedule_has_capacity(self):
        self.attendee.qr_sent = True
        self.attendee.save(update_fields=["qr_sent"])
        response = self.client.get("/api/me/check-in/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["checked_in"])
        self.assertTrue(response.data["qr_code"].startswith("data:image/png;base64,"))
        self.assertEqual(self.client.post("/api/me/check-in/").status_code, 405)


class PhaseFiveHardeningTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.admin = self.User.objects.create_superuser(
            username="phase5-admin", email="phase5-admin@example.com", password="password"
        )
        self.campaign = Campaign.objects.create(
            title="Complete Flow Festival",
            start_date=timezone.datetime(2026, 11, 2, tzinfo=timezone.get_current_timezone()),
            end_date=timezone.datetime(2026, 11, 3, 23, 59, tzinfo=timezone.get_current_timezone()),
        )
        self.survey = Survey.objects.create(
            title="Complete Flow Registration", fkcampaign=self.campaign,
            purpose=Survey.PURPOSE_REGISTRATION, is_active=True,
        )

    def test_registration_to_approval_qr_bookings_and_checkin_end_to_end(self):
        from rest_framework.test import APIClient
        from django.core import mail
        from django.test import override_settings
        import json

        with override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            public_client = APIClient()
            registration = public_client.post(f"/api/events/{self.campaign.pk}/register/", {
                "name": "Festival Attendee", "email": "flow@example.com", "organization": "PIKOM",
            }, format="json")
            self.assertEqual(registration.status_code, 201)
            attendee = SurveyUser.objects.get(pk=registration.data["id"])
            attendee_client = APIClient()
            attendee_client.credentials(HTTP_AUTHORIZATION=f"Bearer {registration.data['registration_code']}")
            self.assertEqual(attendee_client.get("/api/me/").data["approval_status"], SurveyUser.STATUS_PENDING)

            self.client.force_login(self.admin)
            approval = self.client.post(reverse("set_survey_user_status", args=[self.survey.pk]), {
                "ids": json.dumps([attendee.pk]), "status": SurveyUser.STATUS_APPROVED,
            })
            self.assertEqual(approval.status_code, 200)
            sent = self.client.post(reverse("send_survey_qr", args=[self.survey.pk]), {
                "ids": json.dumps([attendee.pk]),
            })
            self.assertTrue(sent.json()["success"])
            attendee.refresh_from_db()
            self.assertTrue(attendee.qr_sent)
            self.assertEqual(len(mail.outbox), 2)  # submission receipt and approval QR

            employer = Employer.objects.create(campaign=self.campaign, name="Flow Employer")
            job = Job.objects.create(employer=employer, title="Flow Engineer")
            slot = InterviewSlot.objects.create(
                employer=employer, date="2026-11-02", start_time="10:00", end_time="11:00", capacity=1,
            )
            session = EventSession.objects.create(
                campaign=self.campaign, title="Flow Session", session_type="panel", event_date="2026-11-02",
                start_time="09:00", end_time="10:00", capacity=1,
            )
            provider = TrainingProvider.objects.create(campaign=self.campaign, name="Flow Training")
            promotion = VoucherPromotion.objects.create(provider=provider, title="Flow Voucher", instructions="Use code FLOW")
            self.assertEqual(attendee_client.post(f"/api/jobs/{job.pk}/bookmark/").status_code, 200)
            self.assertEqual(attendee_client.post(f"/api/sessions/{session.pk}/registration/").status_code, 201)
            self.assertEqual(attendee_client.post(
                f"/api/interview-slots/{slot.pk}/booking/", {"start_time": "10:00"}, format="json"
            ).status_code, 201)
            self.assertEqual(attendee_client.post(f"/api/promotions/{promotion.pk}/claim/").status_code, 201)
            directory = attendee_client.get(f"/api/events/{self.campaign.pk}/directory/")
            self.assertEqual(directory.status_code, 200)
            self.assertEqual(directory.data["sessions"][0]["remaining"], 0)
            schedule = attendee_client.get("/api/me/schedule/").data
            self.assertEqual((len(schedule["sessions"]), len(schedule["interviews"]), len(schedule["saved_jobs"])), (1, 1, 1))
            self.assertEqual(schedule["promotions"][0]["instructions"], "Use code FLOW")
            self.client.post(reverse("set_survey_user_checkin", args=[self.survey.pk]), {
                "id": attendee.pk, "checked": "1",
            })
            status = attendee_client.get("/api/me/check-in/").data
            self.assertTrue(status["checked_in"])
            self.assertTrue(status["qr_code"].startswith("data:image/png;base64,"))
            dashboard = self.client.get(reverse("campaign_dashboard", args=[self.campaign.pk]))
            self.assertEqual(dashboard.context["kpis"]["checked_in"], 1)

    def test_event_permissions_and_attendee_token_do_not_grant_organizer_access(self):
        from rest_framework.test import APIClient
        import json

        attendee = SurveyUser.objects.create(
            survey=self.survey, name="Attendee", email="attendee@example.com",
            approval_status=SurveyUser.STATUS_APPROVED,
        )
        organizer = self.User.objects.create_user(username="other-organizer", password="password")
        self.client.force_login(organizer)
        self.assertEqual(self.client.get(reverse("event_career", args=[self.campaign.pk])).status_code, 403)
        forbidden = self.client.post(reverse("set_survey_user_status", args=[self.survey.pk]), {
            "ids": json.dumps([attendee.pk]), "status": SurveyUser.STATUS_REJECTED,
        })
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(self.client.get(reverse("consolidated_report", args=[self.survey.survey_code])).status_code, 403)
        self.assertEqual(self.client.post(reverse("reorder_questions", args=[self.survey.pk]),
                                          data=json.dumps({"order": [["invalid"]]}),
                                          content_type="application/json").status_code, 403)
        attendee_client = APIClient()
        attendee_client.credentials(HTTP_AUTHORIZATION=f"Bearer {attendee.registration_code}")
        self.assertIn(attendee_client.get(reverse("event_career", args=[self.campaign.pk])).status_code, (302, 403))
        attendee.refresh_from_db()
        self.assertEqual(attendee.approval_status, SurveyUser.STATUS_APPROVED)

    def test_legacy_golf_navigation_is_opt_in_and_routes_remain_available(self):
        from django.test import override_settings

        self.client.force_login(self.admin)
        with override_settings(SHOW_LEGACY_GOLF_TOOLS=False):
            response = self.client.get(reverse("campaign_list"))
            self.assertNotContains(response, "Legacy Golf Tools")
        with override_settings(SHOW_LEGACY_GOLF_TOOLS=True):
            response = self.client.get(reverse("campaign_list"))
            self.assertContains(response, "Legacy Golf Tools")
        self.assertEqual(reverse("golf_event_list"), "/golf_events/")

    def test_event_directory_paginates_each_collection(self):
        from rest_framework.test import APIClient

        attendee = SurveyUser.objects.create(
            survey=self.survey, name="Directory Attendee", email="directory@example.com",
            approval_status=SurveyUser.STATUS_APPROVED,
        )
        first = Employer.objects.create(campaign=self.campaign, name="Directory Employer A")
        second = Employer.objects.create(campaign=self.campaign, name="Directory Employer B")
        Job.objects.create(employer=first, title="Directory Job A")
        Job.objects.create(employer=second, title="Directory Job B")
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {attendee.registration_code}")

        page_one = client.get(f"/api/events/{self.campaign.pk}/directory/?page=1&page_size=1")
        page_two = client.get(f"/api/events/{self.campaign.pk}/directory/?page=2&page_size=1")
        self.assertEqual(page_one.status_code, 200)
        self.assertTrue(page_one.data["pagination"]["has_more"]["employers"])
        self.assertEqual(len(page_one.data["employers"]), 1)
        self.assertEqual(len(page_two.data["employers"]), 1)
        self.assertEqual(len(page_one.data["jobs"]), 1)
        self.assertEqual(len(page_two.data["jobs"]), 1)
        self.assertFalse(page_two.data["pagination"]["has_more"]["employers"])
