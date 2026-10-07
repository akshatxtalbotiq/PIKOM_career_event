from django.contrib import admin

from .models import (
    Booth,
    Campaign,
    Employer,
    EventSession,
    FloorMap,
    InterviewBooking,
    InterviewSlot,
    Job,
    JobBookmark,
    SessionRegistration,
    Survey,
    TrainingProvider,
    University,
    UniversityProgram,
    VoucherClaim,
    VoucherPromotion,
)

admin.site.site_header = "PIKOM Operations"
admin.site.site_title = "PIKOM Admin"
admin.site.index_title = "Manage events, attendees, and opportunities"


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("title", "start_date", "end_date", "is_active", "organizer_name")
    list_filter = ("is_active", "start_date")
    search_fields = ("title", "organizer_name", "organizer_email", "url")
    date_hierarchy = "start_date"
    list_per_page = 30
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Event", {"fields": ("title", "description", "banner", "is_active", "start_date", "end_date", "event_time", "venue", "dress_code", "extra_info")}),
        ("Organizer", {"fields": ("organizer_name", "organizer_email", "organizer_phone", "pic_email")}),
        ("Registration", {"fields": ("url", "entry_url", "entry_keyword", "need_qr", "exclude_columns", "prompt_checkin_info")}),
        ("Attendee email content", {"fields": ("qr_email_subject", "qr_email_intro", "reminder_subject", "reminder_intro", "thankyou_subject", "thankyou_intro", "registration_closed_intro", "email_signoff")}),
        ("Email display", {"fields": ("show_details_qr", "show_details_reminder", "show_details_thankyou", "show_banner_qr", "show_banner_reminder", "show_banner_thankyou", "theme_color")}),
        ("Record details", {"fields": ("campaign_code", "created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ("title", "fkcampaign", "purpose", "start_date", "end_date", "is_active")
    list_filter = ("is_active", "purpose", "start_date")
    search_fields = ("title", "slug", "fkcampaign__title")
    list_select_related = ("fkcampaign",)
    readonly_fields = ("created_at", "survey_code")


@admin.register(EventSession)
class EventSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "campaign", "event_date", "start_time", "end_time", "session_type", "status", "capacity")
    list_filter = ("status", "session_type", "event_date")
    search_fields = ("title", "campaign__title", "speaker_name", "location")
    list_select_related = ("campaign",)
    date_hierarchy = "event_date"
    list_per_page = 40


@admin.register(SessionRegistration)
class SessionRegistrationAdmin(admin.ModelAdmin):
    list_display = ("session", "attendee", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("session__title", "attendee__name", "attendee__email")
    list_select_related = ("session", "attendee")
    date_hierarchy = "created_at"


@admin.register(FloorMap)
class FloorMapAdmin(admin.ModelAdmin):
    list_display = ("name", "campaign", "version", "status", "updated_at")
    list_filter = ("status", "campaign")
    search_fields = ("name", "campaign__title", "version")
    list_select_related = ("campaign",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Booth)
class BoothAdmin(admin.ModelAdmin):
    list_display = ("number", "name", "organization_name", "floor_map", "category", "is_active")
    list_filter = ("is_active", "category", "floor_map__campaign")
    search_fields = ("number", "name", "organization_name", "floor_map__name")
    list_select_related = ("floor_map", "floor_map__campaign")


@admin.register(Employer)
class EmployerAdmin(admin.ModelAdmin):
    list_display = ("name", "campaign", "booth", "is_active", "created_at")
    list_filter = ("is_active", "campaign")
    search_fields = ("name", "campaign__title", "contact_name", "contact_email")
    list_select_related = ("campaign", "booth")
    readonly_fields = ("created_at",)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("title", "employer", "employment_type", "experience_level", "location", "is_active")
    list_filter = ("is_active", "employment_type", "experience_level")
    search_fields = ("title", "employer__name", "location", "description")
    list_select_related = ("employer", "employer__campaign")


@admin.register(JobBookmark)
class JobBookmarkAdmin(admin.ModelAdmin):
    list_display = ("job", "attendee", "created_at")
    list_filter = ("created_at",)
    search_fields = ("job__title", "attendee__name", "attendee__email")
    list_select_related = ("job", "attendee")
    date_hierarchy = "created_at"


@admin.register(InterviewSlot)
class InterviewSlotAdmin(admin.ModelAdmin):
    list_display = ("employer", "date", "start_time", "end_time", "booking_mode", "capacity", "status")
    list_filter = ("status", "booking_mode", "date")
    search_fields = ("employer__name", "interviewer_info")
    list_select_related = ("employer",)
    date_hierarchy = "date"


@admin.register(InterviewBooking)
class InterviewBookingAdmin(admin.ModelAdmin):
    list_display = ("employer_name", "slot", "attendee", "start_time", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("slot__employer__name", "attendee__name", "attendee__email")
    list_select_related = ("slot", "slot__employer", "attendee")
    date_hierarchy = "created_at"

    @admin.display(description="Employer", ordering="slot__employer__name")
    def employer_name(self, booking):
        return booking.slot.employer.name


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "campaign", "booth", "is_active")
    list_filter = ("is_active", "campaign")
    search_fields = ("name", "campaign__title", "contact_name", "contact_email")
    list_select_related = ("campaign", "booth")


@admin.register(UniversityProgram)
class UniversityProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "university", "is_active")
    list_filter = ("is_active", "university__campaign")
    search_fields = ("name", "university__name", "description")
    list_select_related = ("university", "university__campaign")


@admin.register(TrainingProvider)
class TrainingProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "campaign", "booth", "is_active")
    list_filter = ("is_active", "campaign")
    search_fields = ("name", "campaign__title", "contact_name", "contact_email")
    list_select_related = ("campaign", "booth")


@admin.register(VoucherPromotion)
class VoucherPromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "provider", "value_label", "expires_at", "max_claims", "is_active")
    list_filter = ("is_active", "expires_at", "provider__campaign")
    search_fields = ("title", "provider__name", "description")
    list_select_related = ("provider", "provider__campaign")


@admin.register(VoucherClaim)
class VoucherClaimAdmin(admin.ModelAdmin):
    list_display = ("promotion", "attendee", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("promotion__title", "attendee__name", "attendee__email")
    list_select_related = ("promotion", "attendee")
    date_hierarchy = "created_at"
