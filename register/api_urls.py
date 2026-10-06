from django.urls import path

from . import api_views

urlpatterns = [
    path("events/", api_views.api_events, name="api_events"),
    path("events/<int:event_id>/", api_views.api_event_detail, name="api_event_detail"),
    path("events/<int:event_id>/registration-form/", api_views.api_registration_form, name="api_registration_form"),
    path("events/<int:event_id>/register/", api_views.api_register, name="api_register"),
    path("events/<int:event_id>/directory/", api_views.api_event_directory, name="api_event_directory"),
    path("me/", api_views.api_me, name="api_me"),
    path("me/schedule/", api_views.api_schedule, name="api_schedule"),
    path("me/check-in/", api_views.api_check_in, name="api_check_in"),
    path("jobs/<int:job_id>/bookmark/", api_views.api_job_bookmark, name="api_job_bookmark"),
    path("sessions/<int:session_id>/registration/", api_views.api_session_registration, name="api_session_registration"),
    path("interview-slots/<int:slot_id>/booking/", api_views.api_interview_booking, name="api_interview_booking"),
    path("promotions/<int:promotion_id>/claim/", api_views.api_voucher_claim, name="api_voucher_claim"),
]
