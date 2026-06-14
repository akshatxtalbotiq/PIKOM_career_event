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
    # Subject lines (plain text, support the same [Event]/[Date]/... merge tags).
    # Blank = use the built-in default subject.
    qr_email_subject = models.CharField(max_length=200, blank=True, default="")
    reminder_subject = models.CharField(max_length=200, blank=True, default="")
    # Sign-off: sanitised rich-text HTML so it can be multi-line with bold /
    # coloured text (e.g. "<strong>The PIKOM Team</strong><br>Frontier of
    # Super Intelligence 2026"). Legacy plain-text values still render (bolded).
    email_signoff = models.TextField(blank=True, default="")
    # Whether to include the event-details block (date/time/venue/etc.) in each email
    show_details_qr = models.BooleanField(default=True)
    show_details_reminder = models.BooleanField(default=True)

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
    TYPE_IDENTITY_EMAIL = "identity_email"
    TYPE_IDENTITY_PHONE = "identity_phone"
    TYPE_IDENTITY_ORGANIZATION = "identity_organization"

    IDENTITY_TYPES = {
        TYPE_IDENTITY_NAME: "name",
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

    id = models.AutoField(primary_key=True)
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name="survey_users")
    name = models.CharField(max_length=500, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=50, null=True, blank=True)
    organization = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    registration_code = models.UUIDField(default=uuid.uuid4, unique=True)
    is_checked_in = models.BooleanField(default=False)
    qr_sent = models.BooleanField(default=False)
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
    

