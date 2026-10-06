from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Campaign, CampaignTeam, Survey, SurveyUser


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
