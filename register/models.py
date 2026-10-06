from django.db import models
from django.contrib.auth.models import User
import re
import uuid
from datetime import datetime

# def upload_sponsor_attachment(instance, filename):
#     year = datetime.now().year
#     return f"sponsors/{year}/{filename}"

# class Team(models.Model):
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=255)    

#     def __str__(self):
#         return self.name

class Registration(models.Model):
    reg_no = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100) 
    email = models.EmailField()
    mobile = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)
    lastmodified = models.DateTimeField(auto_now=True)
    comp_reg_no = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)   
    campaign_code = models.CharField(max_length=255, null=True, blank=True)   
    submitted_by= models.CharField(max_length=100, null=True, blank=True)
    submitted_by_email = models.EmailField(null=True, blank=True)
    submitted_by_mobile = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name

class Player(models.Model):
    TITLE_CHOICES = [
        ('Mr', 'Mr'),
        ('Ms', 'Ms'),
        ('Mrs', 'Mrs'),
        ('Dr', 'Dr'),
        ('Prof', 'Prof'),
        ('Sir', 'Sir'),
        ('Madam', 'Madam'),
    ]

    TSHIRT_SIZES = [
        ('XS', 'XS'),
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'),
        ('XL', 'XL'),
        ('XXL', 'XXL'),
    ]

    title = models.CharField(max_length=100, choices=TITLE_CHOICES,null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=100, blank=True, db_column="mobile")
    designation = models.CharField(max_length=100, db_column="designation",null=True, blank=True)
    organization = models.CharField(max_length=100, blank=True, db_column="organization")
    handicap = models.CharField(max_length=100, db_column="handicap",null=True, blank=True)
    tshirt_size = models.CharField(max_length=5, choices=TSHIRT_SIZES, db_column="tsize", blank=True)
    fkregistration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='players', db_column="fkRegistration",default=None)
    registration_code = models.UUIDField(default=uuid.uuid4, unique=True)
    is_checked_in = models.BooleanField(default=False)
    qr_sent = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class Sponsorship(models.Model):   
    # TITLE_CHOICES = [
    #     ('Mr', 'Mr'),
    #     ('Ms', 'Ms'),
    #     ('Mrs', 'Mrs'),
    #     ('Dr', 'Dr'),
    #     ('Prof', 'Prof'),
    #     ('Sir', 'Sir'),
    #     ('Madam', 'Madam'),
    # ]
    PACKAGE_CHOICES = [
        ('P1', 'PLATINUM SPONSOR (RM 50,000)'),
        ('P2', 'GOLD SPONSOR (RM 35,000)'),
        ('P3', 'GOLF T-SHIRT SPONSOR (RM 30,000)'),
        ('P4', 'DUFFLE BAG SPONSOR (RM 25,000)'),
        ('P5', 'GOLF CAP SPONSOR (RM 15,000)'),
        ('P6', 'UMBRELLA SPONSOR (RM 15,000)'),
        ('P7', 'GOLF SLEEVE SPONSOR (RM 10,000)'),
        ('P8', 'TEE-BOX & NOVELTY SPONSOR (RM 3,500 EACH)'),
        ('P9', 'GOLF GALA DINNER SPONSOR (RM 25,000)'),
        ('P10', 'LUNCHEON SPONSOR (RM 10,000)'),
        ('P11', 'GOLF GALA DINNER TABLE SPONSOR (RM 2,500)'),
        ('P12', 'GOLF FLIGHT SPONSOR (RM 4,000)'),
        ('P13', 'GOLF BALLS SPONSOR (RM 10,000)'),
    ]    

    reg_no = models.CharField(max_length=100, unique=True)
    # title = models.CharField(max_length=10, choices=TITLE_CHOICES)
    title = models.CharField(max_length=100, null=True, blank=True)
    billing_name = models.CharField(max_length=100)
    

    billing_organization = models.CharField(max_length=100)
    billing_reg_no = models.CharField(max_length=100, null=True, blank=True)    
    billing_email = models.EmailField()    
    billing_contact = models.CharField(max_length=100, blank=True)
    billing_address = models.TextField()

    contact_number = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_name = models.CharField(max_length=100)    
    billing_designation = models.CharField(max_length=100)

    submitted_at = models.DateTimeField(auto_now_add=True)

    package = models.CharField(max_length=100, choices=PACKAGE_CHOICES, db_column="package", default=None)
    campaign_code = models.CharField(max_length=255, null=True, blank=True)    
    #logo = models.ImageField(upload_to=upload_sponsor_attachment, blank=True, null=True)

    submitted_by= models.CharField(max_length=100, null=True, blank=True)
    submitted_by_email = models.EmailField(null=True, blank=True)
    submitted_by_mobile = models.CharField(max_length=100, null=True, blank=True)

    

    def __str__(self):
        return f"{self.contact_name} - {self.contact_email}"
    
class Campaign(models.Model):
    id = models.AutoField(primary_key=True)
    campaign_code = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    organizer_name = models.CharField(max_length=255, blank=True, default="")
    organizer_email = models.EmailField(blank=True, default="")
    organizer_phone = models.CharField(max_length=80, blank=True, default="")
    banner = models.ImageField(upload_to="event_banners/", null=True, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    entry_url = models.URLField(max_length=500, null=True, blank=True)
    entry_keyword = models.CharField(max_length=100, null=True, blank=True)
    need_qr = models.BooleanField(default=False)
    pic_email = models.TextField(null=True, blank=True)
    exclude_columns = models.TextField(null=True, blank=True)
    prompt_checkin_info = models.BooleanField(default=True)

    # --- Event details (shared by all forms/emails for this campaign) ---
    # Date is NOT stored here — it is derived from `end_date` (the event day),
    # consistent with the QR/reminder emails.
    event_time = models.CharField(max_length=120, blank=True, default="")      # "8:30am – 5:30pm"
    venue = models.TextField(blank=True, default="")                           # full venue line
    dress_code = models.CharField(max_length=120, blank=True, default="")      # "Smart Casual or Business Attire"
    # Arbitrary extra rows shown after the fixed fields. Each row has an emoji
    # icon, optional bold label, text value, and optional link (renders the
    # value as a clickable link). Covers parking, agenda links, lucky draw, etc.
    # [{"icon": "🅿️", "label": "", "value": "Complimentary Parking", "link": ""},
    #  {"icon": "📝", "label": "", "value": "Summit Agenda", "link": "https://..."}]
    extra_info = models.JSONField(default=list, blank=True)

    # --- Per-email message text: sanitised rich-text HTML, supports merge tags ---
    qr_email_intro = models.TextField(blank=True, default="")    # body HTML of QR confirmation email
    reminder_intro = models.TextField(blank=True, default="")    # body HTML of attendance reminder
    thankyou_intro = models.TextField(blank=True, default="")    # body HTML of "thank you for submission" email
    # Body HTML shown on the public "Registration Closed" page when the form is
    # turned off. Supports the [Event]/[Date] merge tags. Blank = default copy.
    registration_closed_intro = models.TextField(blank=True, default="")
    # Subject lines (plain text, support the same [Event]/[Date]/... merge tags).
    # Blank = use the built-in default subject.
    qr_email_subject = models.CharField(max_length=200, blank=True, default="")
    reminder_subject = models.CharField(max_length=200, blank=True, default="")
    thankyou_subject = models.CharField(max_length=200, blank=True, default="")
    # Sign-off: sanitised rich-text HTML so it can be multi-line with bold /
    # coloured text (e.g. "<strong>The PIKOM Team</strong><br>Frontier of
    # Super Intelligence 2026"). Legacy plain-text values still render (bolded).
    email_signoff = models.TextField(blank=True, default="")
    # Whether to include the event-details block (date/time/venue/etc.) in each email
    show_details_qr = models.BooleanField(default=True)
    show_details_reminder = models.BooleanField(default=True)
    show_details_thankyou = models.BooleanField(default=False)
    # Whether to include the banner image at the top of each email
    show_banner_qr = models.BooleanField(default=True)
    show_banner_reminder = models.BooleanField(default=True)
    show_banner_thankyou = models.BooleanField(default=True)

    # --- Event theme colour ---
    # Hex accent colour used on the public registration form and in registrant
    # emails (header bar, reference pill, headings, links). Each event can set
    # its own; the default is the green used historically in the emails.
    THEME_DEFAULT = "#198754"
    theme_color = models.CharField(max_length=7, blank=True, default="#198754")

    @property
    def theme(self):
        """Validated theme colour hex; falls back to the default green so a
        blank/garbled value can never break the form or emails."""
        c = (self.theme_color or "").strip()
        return c.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", c) else self.THEME_DEFAULT

    @property
    def theme_soft(self):
        """Very light tint of the theme colour (90% white) for pill/badge
        backgrounds — the per-theme equivalent of the old #e7f4ec green."""
        c = self.theme.lstrip("#")
        r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
        return "#{:02x}{:02x}{:02x}".format(*(round(v + (255 - v) * 0.9) for v in (r, g, b)))

    def __str__(self):
        return self.title
    
class Submission(models.Model):    
    id = models.AutoField(primary_key=True)
    reg_no = models.CharField(max_length=100, unique=True)    
    name = models.CharField(max_length=100) 
    email = models.EmailField()
    mobile = models.CharField(max_length=100, blank=True, null=True)
    organization = models.CharField(max_length=100, blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    lastmodified = models.DateTimeField(auto_now=True)
    registration_code = models.UUIDField(default=uuid.uuid4, unique=True)
    is_checked_in = models.BooleanField(default=False)
    qr_sent = models.BooleanField(default=False)
    campaign_code = models.CharField(max_length=255)    #uuid of campaign
    remarks = models.TextField(null=True, blank=True)
    is_member = models.BooleanField(default=False)
    member_code = models.CharField(max_length=100, blank=True, null=True)
    fkcampaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, null=True, blank=True, related_name='submissions', db_column="fkcampaign",default=None)
    category = models.CharField(max_length=500, null=True, blank=True)
    promo_code = models.CharField(max_length=100, blank=True, null=True)
    consent = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class CampaignTeam(models.Model):
    id = models.AutoField(primary_key=True)
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='campaign_teams')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='campaign_user')

    def __str__(self):
        return f"Team for {self.campaign.title} - {self.user.username}"
    
def default_identity_field_config():
    """Default order/visibility/required state for the auto-captured identity
    fields on a registration form. Each registration form gets its own copy
    so reordering one form doesn't affect another."""
    return [
        {"key": "name",         "label": "Name",         "visible": True, "required": True},
        # Participant type is a first-class identity field captured on every
        # registration using a fixed select list.
        {"key": "participant_type", "label": "Participant Type", "visible": True, "required": True},
        {"key": "email",        "label": "Email",        "visible": True, "required": True},
        {"key": "phone",        "label": "Phone",        "visible": True, "required": False},
        {"key": "organization", "label": "Organization", "visible": True, "required": False},
    ]


def merge_identity_field_config(stored):
    """Return the stored identity field config merged with the current defaults.

    JSONField defaults are only applied when a row is first created, so surveys
    built before a field (e.g. phone/organization) was added to
    `default_identity_field_config()` have a stored config that is missing those
    keys. That made the field invisible everywhere it was read from config (list
    columns, builder toggles). This merges so every identity field is always
    present, in canonical order, with stored values winning over defaults and
    any field absent from the stored config falling back to its default
    (visible) state.
    """
    defaults = default_identity_field_config()
    by_key = {item.get("key"): item for item in (stored or []) if isinstance(item, dict)}
    merged = []
    seen = set()
    for d in defaults:
        k = d["key"]
        s = by_key.get(k)
        if s:
            merged.append({
                "key": k,
                "label": s.get("label") or d["label"],
                "visible": s.get("visible", d["visible"]),
                "required": s.get("required", d["required"]),
            })
        else:
            merged.append(dict(d))
        seen.add(k)
    # Preserve any extra (future) keys not covered by defaults.
    for item in (stored or []):
        if isinstance(item, dict) and item.get("key") not in seen:
            merged.append(item)
            seen.add(item.get("key"))
    return merged


class Survey(models.Model):
    PURPOSE_REGISTRATION = "registration"
    PURPOSE_FEEDBACK = "feedback"
    PURPOSE_CHOICES = [
        (PURPOSE_REGISTRATION, "Registration Form"),
        (PURPOSE_FEEDBACK, "Post-event Survey"),
    ]

    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=80, unique=True, null=True, blank=True,
        help_text="Human-friendly identifier used in the public URL "
                  "(e.g. 'cio-conference-2026'). Auto-generated from the title.",
    )
    description = models.TextField(blank=True)
    fkcampaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="surveys", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    survey_code = models.UUIDField(default=uuid.uuid4, unique=True)
    purpose = models.CharField(
        max_length=20, choices=PURPOSE_CHOICES, default=PURPOSE_REGISTRATION
    )
    banner = models.ImageField(upload_to="form_banners/", null=True, blank=True)
    identity_field_config = models.JSONField(default=default_identity_field_config)
    show_event_details = models.BooleanField(
        default=False,
        help_text="Show the campaign's event details block (date, time, venue, etc.) "
                  "at the top of the public registration form.",
    )

    def __str__(self):
        return self.title

class Question(models.Model):
    TYPE_TEXT = "text"           # single open text (input)
    TYPE_TEXTAREA = "textarea"   # long open text (textarea)
    TYPE_RADIO = "radio"         # single-choice
    TYPE_CHECKBOX = "checkbox"   # multi-choice
    TYPE_SELECT = "select"       # dropdown
    TYPE_MATRIX_ROLES = "matrix_roles"  # special Section C (table)

    # Identity types — answers are saved to SurveyUser fields, not the Answer
    # table. They participate in the regular question ordering so they can be
    # interleaved with custom questions (e.g. "Salutation" before "Name").
    TYPE_IDENTITY_NAME = "identity_name"
    TYPE_IDENTITY_PARTICIPANT_TYPE = "identity_participant_type"
    TYPE_IDENTITY_EMAIL = "identity_email"
    TYPE_IDENTITY_PHONE = "identity_phone"
    TYPE_IDENTITY_ORGANIZATION = "identity_organization"

    IDENTITY_TYPES = {
        TYPE_IDENTITY_NAME: "name",
        TYPE_IDENTITY_PARTICIPANT_TYPE: "participant_type",
        TYPE_IDENTITY_EMAIL: "email",
        TYPE_IDENTITY_PHONE: "phone",
        TYPE_IDENTITY_ORGANIZATION: "organization",
    }

    QUESTION_TYPES = [
        (TYPE_TEXT, "Open Text"),
        (TYPE_TEXTAREA, "Paragraph"),
        (TYPE_RADIO, "Single Choice"),
        (TYPE_CHECKBOX, "Multiple Choice"),
        (TYPE_SELECT, "Dropdown"),
        (TYPE_MATRIX_ROLES, "Roles & Skills Matrix (Section C - Q6)"),
        (TYPE_IDENTITY_NAME, "Identity — Name"),
        (TYPE_IDENTITY_PARTICIPANT_TYPE, "Identity — Participant Type"),
        (TYPE_IDENTITY_EMAIL, "Identity — Email"),
        (TYPE_IDENTITY_PHONE, "Identity — Phone"),
        (TYPE_IDENTITY_ORGANIZATION, "Identity — Organization"),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="questions")
    number = models.PositiveIntegerField(help_text="Question number in the survey.")
    text = models.TextField()
    help_text = models.TextField(blank=True)
    question_type = models.CharField(max_length=32, choices=QUESTION_TYPES, default=TYPE_TEXT)
    show_in_list = models.BooleanField(
        default=False,
        help_text="If True, this question's answer is shown as a column in the registrations list.",
    )
    list_column_label = models.CharField(
        max_length=60, blank=True,
        help_text="Optional short label used as the column header in the registrations list. "
                  "Falls back to a truncated question text when empty.",
    )

    # For choice questions, store list of strings as JSON
    choices = models.JSONField(blank=True, null=True, help_text="List of options for radio/checkbox/select.")
    allow_other = models.BooleanField(default=False, help_text="Include an 'Other' free-text input.")
    max_checks = models.PositiveIntegerField(blank=True, null=True, help_text="Optional limit for checkbox selections.")
    is_required = models.BooleanField(default=True)
    # Per-choice follow-up: dict mapping a choice label -> placeholder/label for
    # a free-text input that appears (and becomes required) when that choice is
    # selected. e.g. {"attending by Invitation": "Name of the inviter"}.
    choice_followups = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Q{self.number}: {self.text[:60]}"

class SurveyUser(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    # Participant grouping used across registration forms and list columns.
    PARTICIPANT_TYPE_ORGANIZER = "Organizer"
    PARTICIPANT_TYPE_DELEGATE = "Delegate"
    PARTICIPANT_TYPE_SPONSOR = "Sponsor"
    PARTICIPANT_TYPE_EXHIBITOR = "Exhibitor"
    PARTICIPANT_TYPE_SPEAKER = "Speaker"
    PARTICIPANT_TYPE_CHOICES = [
        (PARTICIPANT_TYPE_ORGANIZER, "Organizer"),
        (PARTICIPANT_TYPE_DELEGATE, "Delegate"),
        (PARTICIPANT_TYPE_SPONSOR, "Sponsor"),
        (PARTICIPANT_TYPE_EXHIBITOR, "Exhibitor"),
        (PARTICIPANT_TYPE_SPEAKER, "Speaker"),
    ]

    id = models.AutoField(primary_key=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="survey_users")
    name = models.CharField(max_length=500, null=True, blank=True)
    participant_type = models.CharField(
        max_length=32,
        choices=PARTICIPANT_TYPE_CHOICES,
        default=PARTICIPANT_TYPE_DELEGATE,
    )
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    organization = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    registration_code = models.UUIDField(default=uuid.uuid4, unique=True)
    is_checked_in = models.BooleanField(default=False)
    qr_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    remarks = models.TextField(null=True, blank=True)
    # Public-facing reference number given to the registrant (e.g. "REG000123").
    # Assigned right after the row is created so it can include the row id.
    reg_no = models.CharField(max_length=32, unique=True, null=True, blank=True)

    # Vetting workflow. Registrations land as `pending`; an organiser reviews
    # them on the dashboard and flips them to `approved` (which is the gate
    # for issuing the QR-code email) or `rejected`.
    approval_status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING,
        help_text="Vetting status. QR codes are only emailed to approved delegates.",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="surveyuser_approvals",
    )

    def __str__(self):
        return f"{self.name} - {self.survey.title}"

class Answer(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    user = models.ForeignKey(SurveyUser, on_delete=models.SET_NULL, null=True, blank=True)

    # For text/textarea -> answer_text
    # For radio/select/checkbox -> selected_options (list of strings)
    # For matrix_roles (Q6) -> structured JSON in answer_text (stringified JSON)
    answer_text = models.TextField(blank=True, null=True)
    selected_options = models.JSONField(blank=True, null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.user if self.user_id else "Anonymous"
        return f"{who} Q{self.question.number}"
    

# ===========================================================================
# GOLF EVENT
# ---------------------------------------------------------------------------
# A self-contained stack for golf tournaments, deliberately kept separate from
# Campaign / Survey so golf events never mix into the regular Campaigns list
# and the legacy 2025 Registration / Player / Sponsorship rows stay untouched.
#
#   GolfEvent            the tournament (dates, venue, theme, email wording)
#   GolfEventTeam        which users may manage it
#   GolfForm             a participant form OR a sponsor form for the event
#   GolfQuestion         extra custom questions on a form (asked once per entry)
#   GolfSponsorItem      a sponsorship item authored on a sponsor form
#   GolfRegistration     one submitted entry (participant or sponsor)
#   GolfPlayer           a player slot inside a participant entry
#   GolfSelection        a sponsor item picked on an entry (package or add-on)
#   GolfAnswer           an answer to a GolfQuestion
# ===========================================================================


def default_golf_extra_info():
    return []


class GolfEvent(models.Model):
    """A golf tournament. Plays the same role for the golf flow that Campaign
    plays for the regular registration flow."""

    THEME_DEFAULT = "#198754"

    id = models.AutoField(primary_key=True)
    event_code = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Comma-separated organiser addresses used as Reply-To on outgoing mail and
    # notified when a new entry lands.
    pic_email = models.TextField(blank=True, default="")

    # --- Event details (shared by every form / email for this event) ---
    # The date is derived from `end_date` (the event day), same convention the
    # campaign emails use.
    event_time = models.CharField(max_length=120, blank=True, default="")
    venue = models.TextField(blank=True, default="")
    dress_code = models.CharField(max_length=120, blank=True, default="")
    # [{"icon": "\U0001f17f️", "label": "", "value": "Complimentary Parking", "link": ""}]
    extra_info = models.JSONField(default=default_golf_extra_info, blank=True)

    # --- Confirmation email (sanitised rich text, supports merge tags) ---
    confirmation_subject = models.CharField(max_length=200, blank=True, default="")
    confirmation_intro = models.TextField(blank=True, default="")
    show_banner_confirmation = models.BooleanField(default=True)
    show_details_confirmation = models.BooleanField(default=True)
    email_signoff = models.TextField(blank=True, default="")

    # Body HTML for the public "Registration Closed" page.
    registration_closed_intro = models.TextField(blank=True, default="")

    # Accent colour used on the public pages and in the emails.
    theme_color = models.CharField(max_length=7, blank=True, default=THEME_DEFAULT)

    class Meta:
        ordering = ["-start_date"]

    @property
    def theme(self):
        """Validated accent colour; falls back to the default green so a blank
        or garbled value can never break a public page or an email."""
        c = (self.theme_color or "").strip()
        return c.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", c) else self.THEME_DEFAULT

    @property
    def theme_soft(self):
        """90%-white tint of the accent colour, for pill / badge backgrounds."""
        c = self.theme.lstrip("#")
        r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
        return "#{:02x}{:02x}{:02x}".format(*(round(v + (255 - v) * 0.9) for v in (r, g, b)))

    def __str__(self):
        return self.title


class GolfEventTeam(models.Model):
    """Users allowed to manage a golf event (mirrors CampaignTeam)."""
    id = models.AutoField(primary_key=True)
    event = models.ForeignKey(GolfEvent, on_delete=models.CASCADE, related_name="event_teams")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="golf_event_user")

    class Meta:
        unique_together = ("event", "user")

    def __str__(self):
        return f"Team for {self.event.title} - {self.user.username}"


def default_golf_player_field_config():
    """Order / visibility / required state of the fixed player identity fields
    on a golf participant form. Each form gets its own copy so editing one form
    never affects another.

    ``in_list`` controls whether the field also gets its own column on the
    entries table (/golf_submission_list/). Every field starts switched on."""
    return [
        {"key": "salutation",   "label": "Salutation",         "visible": True, "required": True, "in_list": True},
        {"key": "name",         "label": "Name",               "visible": True, "required": True, "in_list": True},
        {"key": "handicap",     "label": "Handicap (USGA)",    "visible": True, "required": True, "in_list": True},
        {"key": "tgcc_member",  "label": "Member of TGCC",     "visible": True, "required": True, "in_list": True},
        {"key": "organisation", "label": "Organisation",       "visible": True, "required": True, "in_list": True},
        {"key": "designation",  "label": "Designation",        "visible": True, "required": True, "in_list": True},
        {"key": "mobile",       "label": "Mobile Number",      "visible": True, "required": True, "in_list": True},
        {"key": "email",        "label": "Email",              "visible": True, "required": True, "in_list": True},
        {"key": "tshirt_size",  "label": "T-Shirt Asian Size", "visible": True, "required": True, "in_list": True},
    ]


GOLF_PLAYER_FIELD_KEYS = [f["key"] for f in default_golf_player_field_config()]


def merge_golf_player_field_config(stored):
    """Stored player-field config merged over the current defaults, in canonical
    order. JSONField defaults only apply at row creation, so a form built before
    a field existed would otherwise be missing it entirely."""
    defaults = default_golf_player_field_config()
    by_key = {i.get("key"): i for i in (stored or []) if isinstance(i, dict)}
    merged, seen = [], set()
    for d in defaults:
        s = by_key.get(d["key"])
        if s:
            merged.append({
                "key": d["key"],
                "label": s.get("label") or d["label"],
                "visible": s.get("visible", d["visible"]),
                "required": s.get("required", d["required"]),
                # Forms saved before the column switch existed keep every
                # field on the entries table, which is the stated default.
                "in_list": s.get("in_list", d["in_list"]),
            })
        else:
            merged.append(dict(d))
        seen.add(d["key"])
    for item in (stored or []):
        if isinstance(item, dict) and item.get("key") not in seen:
            merged.append(item)
            seen.add(item.get("key"))
    return merged


def default_golf_salutations():
    return ["Mr", "Ms"]


def default_golf_tshirt_sizes():
    return ["S", "M", "L", "XL", "2XL", "3XL", "4XL", "5XL"]


class GolfForm(models.Model):
    """A public form belonging to a golf event: either the participant
    (flight registration) form or the sponsor form."""

    KIND_PARTICIPANT = "participant"
    KIND_SPONSOR = "sponsor"
    KIND_CHOICES = [
        (KIND_PARTICIPANT, "Participant Form"),
        (KIND_SPONSOR, "Sponsor Form"),
    ]

    id = models.AutoField(primary_key=True)
    form_code = models.UUIDField(default=uuid.uuid4, unique=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default=KIND_PARTICIPANT)
    title = models.CharField(max_length=255)
    slug = models.SlugField(
        max_length=80, unique=True, null=True, blank=True,
        help_text="Human-friendly identifier used in the public URL "
                  "(e.g. 'pikom-golf-2026'). Auto-generated from the title.",
    )
    description = models.TextField(blank=True)
    fkevent = models.ForeignKey(
        GolfEvent, on_delete=models.CASCADE, related_name="forms", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    banner = models.ImageField(upload_to="golf_banners/", null=True, blank=True)
    show_event_details = models.BooleanField(
        default=False,
        help_text="Show the event's details block (date, time, venue, etc.) at "
                  "the top of the public page.",
    )

    # Sanitised rich text shown at the very bottom of the public page, directly
    # above the Submit button. Used for payment instructions, T&Cs, etc.
    note = models.TextField(blank=True, default="")

    # --- Participant-form only ---
    player_slots = models.PositiveSmallIntegerField(
        default=4, help_text="How many player sub-forms to show (a flight is 4)."
    )
    required_players = models.PositiveSmallIntegerField(
        default=4, help_text="How many of those player sub-forms must be completed."
    )
    package_label = models.CharField(
        max_length=200, blank=True, default="Participation Package",
        help_text="Label shown next to the base package price.",
    )
    package_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="One base price for the whole entry (covers all player slots).",
    )
    currency = models.CharField(max_length=8, blank=True, default="RM")

    # Fixed player identity fields: order / visibility / required / label.
    player_field_config = models.JSONField(default=default_golf_player_field_config)
    salutation_options = models.JSONField(default=default_golf_salutations)
    tshirt_sizes = models.JSONField(default=default_golf_tshirt_sizes)
    size_guide_label = models.CharField(
        max_length=80, blank=True, default="Size guide",
        help_text="Text of the link shown next to the T-shirt size field on the "
                  "public page. The link only appears once size images exist.",
    )

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_participant(self):
        return self.kind == self.KIND_PARTICIPANT

    @property
    def is_sponsor(self):
        return self.kind == self.KIND_SPONSOR

    @property
    def public_ident(self):
        """Identifier used in the public URL (slug preferred, UUID fallback)."""
        return self.slug or str(self.form_code)

    @property
    def theme(self):
        return self.fkevent.theme if self.fkevent else GolfEvent.THEME_DEFAULT

    @property
    def theme_soft(self):
        return self.fkevent.theme_soft if self.fkevent else "#e7f4ec"

    @property
    def player_fields(self):
        """Merged player-field config (always complete, canonical order)."""
        return merge_golf_player_field_config(self.player_field_config)

    def player_field_map(self):
        """{key: config} for template / view lookups."""
        return {f["key"]: f for f in self.player_fields}

    @property
    def size_guide_images(self):
        """Size-guide slides in display order. Empty means the public page shows
        no size-guide link at all."""
        return list(self.size_images.all())

    @property
    def size_guide_link_text(self):
        return (self.size_guide_label or "").strip() or "Size guide"

    def __str__(self):
        return f"{self.title} ({self.get_kind_display()})"


class GolfSizeImage(models.Model):
    """One slide of the T-shirt size guide: an image the organiser uploads on the
    participant form builder, shown in a carousel from the public page."""

    form = models.ForeignKey(
        GolfForm, on_delete=models.CASCADE, related_name="size_images"
    )
    image = models.ImageField(upload_to="golf_size_images/")
    caption = models.CharField(
        max_length=200, blank=True, default="",
        help_text="Optional line shown under the slide.",
    )
    number = models.PositiveIntegerField(default=0, help_text="Slide order.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["number", "id"]

    def __str__(self):
        return self.caption or f"Size image {self.number}"


class GolfQuestion(models.Model):
    """An extra custom question on a golf form. Asked once per entry (not per
    player), and rendered after the player blocks."""

    TYPE_TEXT = "text"
    TYPE_TEXTAREA = "textarea"
    TYPE_RADIO = "radio"
    TYPE_CHECKBOX = "checkbox"
    TYPE_SELECT = "select"
    QUESTION_TYPES = [
        (TYPE_TEXT, "Open Text"),
        (TYPE_TEXTAREA, "Paragraph"),
        (TYPE_RADIO, "Single Choice"),
        (TYPE_CHECKBOX, "Multiple Choice"),
        (TYPE_SELECT, "Dropdown"),
    ]

    form = models.ForeignKey(GolfForm, on_delete=models.CASCADE, related_name="questions")
    number = models.PositiveIntegerField(help_text="Display order on the form.")
    text = models.TextField()
    help_text = models.TextField(blank=True)
    question_type = models.CharField(max_length=32, choices=QUESTION_TYPES, default=TYPE_TEXT)
    choices = models.JSONField(blank=True, null=True, help_text="Options for radio/checkbox/select.")
    allow_other = models.BooleanField(default=False, help_text="Include an 'Other' free-text input.")
    max_checks = models.PositiveIntegerField(blank=True, null=True, help_text="Optional limit for checkbox selections.")
    is_required = models.BooleanField(default=True)
    show_in_list = models.BooleanField(
        default=False,
        help_text="If True, this answer is shown as a column in the entries list.",
    )
    list_column_label = models.CharField(
        max_length=60, blank=True,
        help_text="Optional short column header for the entries list.",
    )

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Q{self.number}: {self.text[:60]}"


class GolfSponsorItem(models.Model):
    """A sponsorship item (package) authored on a sponsor form. Items flagged
    `show_in_participant` also appear as paid add-ons on the participant form of
    the same golf event.

    On the public sponsor page each item is one full-width row: package `image` on
    the left, name / price / description in the middle, a Select control on the
    right. A sold-out `once_only` item becomes unclickable and credits its buyer via
    `logo` in the top-right corner (or shows 'NOT AVAILABLE' when no logo is set)."""

    form = models.ForeignKey(GolfForm, on_delete=models.CASCADE, related_name="sponsor_items")
    number = models.PositiveIntegerField(default=1, help_text="Display order on the sponsor page.")
    image = models.ImageField(
        upload_to="golf_sponsor_items/", null=True, blank=True,
        help_text="The package image — the main picture on the item card.",
    )
    name = models.CharField(max_length=255)
    price = models.DecimalField(
        max_digits=12, decimal_places=2,
        help_text="The item price. This is the only price shown on the sponsor page, "
                  "and the amount a sponsor is charged for it.",
    )
    special_price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        help_text="The participant add-on price — shown ONLY on the participant page, "
                  "never on the sponsor page. Mandatory when `show_in_participant` is "
                  "set. May be higher or lower than `price`.",
    )
    description = models.TextField(blank=True, help_text="Rich text shown on the item card.")
    logo = models.ImageField(
        upload_to="golf_sponsor_logos/", null=True, blank=True,
        help_text="Optional. The logo of the sponsor who BOUGHT this item, uploaded by "
                  "an organiser. Shown on the top-right corner of the card once the item "
                  "is sold out; when absent the card shows 'NOT AVAILABLE' instead. Not "
                  "displayed while the item is still available.",
    )
    once_only = models.BooleanField(
        default=False,
        help_text="Item can only be taken once. After the first entry the card becomes "
                  "unclickable and credits the buyer's logo (or shows 'TAKEN').",
    )
    show_in_participant = models.BooleanField(
        default=False,
        help_text="Also offer this item as a paid add-on on the participant form.",
    )
    is_available = models.BooleanField(
        default=True,
        help_text="Organiser switch for whether this item can still be taken. Turn it "
                  "off to close the item by hand (e.g. sold offline): it stays listed "
                  "but the card becomes unclickable and shows the buyer's logo — or "
                  "'TAKEN' when no logo is set. Independent of `once_only`, which "
                  "closes the item automatically after the first entry.",
    )
    # NOTE: `is_active` is a different thing — it hides the item from the public
    # page entirely. `is_available` keeps it listed but closes it for selection.
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the item appears on the public page at all.",
    )

    class Meta:
        ordering = ["number", "id"]

    # Two prices, two audiences — never mixed:
    #   sponsor page      -> `price`         (the item price)
    #   participant page  -> `special_price` (the add-on price)
    # `special_price` is not a "discount"; it may be higher or lower than `price`.

    @property
    def sponsor_price(self):
        """What the sponsor page shows and charges."""
        return self.price

    @property
    def addon_price(self):
        """What the participant page shows and charges. Never None for an item
        offered there — `show_in_participant` requires a special price."""
        return self.special_price if self.special_price is not None else self.price

    def price_for(self, form):
        """The amount to charge for this item on `form`."""
        return self.addon_price if form.is_participant else self.sponsor_price

    @property
    def taken_count(self):
        return self.selections.count()

    @property
    def is_taken(self):
        """A once-only item is closed as soon as one entry has claimed it."""
        return bool(self.once_only and self.selections.exists())

    @property
    def is_sold_out(self):
        """Not selectable on the public page, for either reason: an organiser
        switched it off by hand, or it is a once-only item that has been claimed.
        This is what the public pages render as unavailable."""
        return (not self.is_available) or self.is_taken

    def __str__(self):
        return self.name


class GolfRegistration(models.Model):
    """One submitted entry against a golf form — a flight of players on a
    participant form, or a sponsorship on a sponsor form."""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    ]

    id = models.AutoField(primary_key=True)
    form = models.ForeignKey(GolfForm, on_delete=models.CASCADE, related_name="registrations")
    reg_no = models.CharField(max_length=32, unique=True, null=True, blank=True)
    registration_code = models.UUIDField(default=uuid.uuid4, unique=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    lastmodified = models.DateTimeField(auto_now=True)

    # --- Contact details (both form kinds) ---
    contact_person = models.CharField(max_length=255, blank=True, default="")
    contact_designation = models.CharField(max_length=255, blank=True, default="")
    contact_number = models.CharField(max_length=100, blank=True, default="")
    contact_email = models.EmailField(blank=True, default="")

    # --- Billing details ---
    # Shared columns, labelled differently per form kind on the public page:
    #   participant: Company Full Name (ROS/ROC) / Business Reg. No. /
    #                Company Full Address / Contact person (e-Invoice) email
    #   sponsor:     Organisation / (unused) / Billing Address / Email Address
    #                + billing contact person, designation and contact number
    billing_company = models.CharField(max_length=255, blank=True, default="")
    billing_reg_no = models.CharField(max_length=100, blank=True, default="")
    billing_address = models.TextField(blank=True, default="")
    billing_email = models.EmailField(blank=True, default="")
    billing_contact_person = models.CharField(max_length=255, blank=True, default="")
    billing_designation = models.CharField(max_length=255, blank=True, default="")
    billing_contact_number = models.CharField(max_length=100, blank=True, default="")

    # --- Money (snapshotted at submission so later price edits don't rewrite
    #     historical entries) ---
    base_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    items_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=8, blank=True, default="RM")

    # --- Vetting ---
    approval_status = models.CharField(
        max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING,
        help_text="Organiser review state of this entry.",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="golf_registration_approvals",
    )
    confirmation_sent = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-submitted_at"]

    def recalc_totals(self, save=True):
        """Recompute items_total / total_amount from the linked selections."""
        from decimal import Decimal
        items = sum((s.unit_price or Decimal("0")) for s in self.selections.all())
        self.items_total = items
        self.total_amount = (self.base_price or Decimal("0")) + items
        if save:
            self.save(update_fields=["items_total", "total_amount"])
        return self.total_amount

    def __str__(self):
        return f"{self.reg_no or self.id} - {self.contact_person}"


class GolfPlayer(models.Model):
    """One player slot inside a participant entry."""

    SALUTATION_OTHER = "Others"

    registration = models.ForeignKey(
        GolfRegistration, on_delete=models.CASCADE, related_name="players"
    )
    slot = models.PositiveSmallIntegerField(default=1, help_text="Player 1..4 within the entry.")
    salutation = models.CharField(max_length=50, blank=True, default="")
    salutation_other = models.CharField(
        max_length=100, blank=True, default="",
        help_text="Free text captured when the salutation is 'Others'.",
    )
    name = models.CharField(max_length=255, blank=True, default="")
    handicap = models.CharField(max_length=50, blank=True, default="", help_text="USGA handicap.")
    is_tgcc_member = models.BooleanField(default=False)
    tgcc_membership_no = models.CharField(max_length=100, blank=True, default="")
    organisation = models.CharField(max_length=255, blank=True, default="")
    designation = models.CharField(max_length=255, blank=True, default="")
    mobile = models.CharField(max_length=100, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    tshirt_size = models.CharField(max_length=10, blank=True, default="")
    registration_code = models.UUIDField(default=uuid.uuid4, unique=True)
    is_checked_in = models.BooleanField(default=False)
    remarks = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["slot"]
        unique_together = ("registration", "slot")

    @property
    def display_salutation(self):
        if self.salutation == self.SALUTATION_OTHER and self.salutation_other:
            return self.salutation_other
        return self.salutation

    @property
    def display_name(self):
        sal = self.display_salutation
        return f"{sal} {self.name}".strip() if sal else self.name

    def field_value(self, key):
        """Human-readable value of one player-identity field, addressed by the
        same key the form's ``player_field_config`` uses. Used to build the
        per-field columns on the entries table."""
        if key == "salutation":
            return self.display_salutation or ""
        if key == "tgcc_member":
            if not self.is_tgcc_member:
                return "No"
            return f"Yes ({self.tgcc_membership_no})" if self.tgcc_membership_no else "Yes"
        return str(getattr(self, key, "") or "")

    def __str__(self):
        return self.display_name or f"Player {self.slot}"


class GolfSelection(models.Model):
    """A sponsor item claimed by an entry — a package on the sponsor form, or a
    paid add-on on the participant form. Name and price are snapshotted so the
    entry keeps reading correctly after the item is edited or removed."""

    registration = models.ForeignKey(
        GolfRegistration, on_delete=models.CASCADE, related_name="selections"
    )
    item = models.ForeignKey(
        GolfSponsorItem, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="selections",
    )
    item_name = models.CharField(max_length=255, blank=True, default="")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_addon = models.BooleanField(
        default=False, help_text="True when picked as an add-on on the participant form."
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.item_name} ({self.unit_price})"


class GolfAnswer(models.Model):
    """An answer to a GolfQuestion."""

    form = models.ForeignKey(GolfForm, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(GolfQuestion, on_delete=models.CASCADE, related_name="answers")
    registration = models.ForeignKey(
        GolfRegistration, on_delete=models.CASCADE, null=True, blank=True, related_name="answers"
    )
    answer_text = models.TextField(blank=True, null=True)
    selected_options = models.JSONField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration_id} Q{self.question.number}"
