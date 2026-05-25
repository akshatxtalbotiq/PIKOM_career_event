from django.db import models
from django.contrib.auth.models import User
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


class Survey(models.Model):
    PURPOSE_REGISTRATION = "registration"
    PURPOSE_FEEDBACK = "feedback"
    PURPOSE_CHOICES = [
        (PURPOSE_REGISTRATION, "Registration Form"),
        (PURPOSE_FEEDBACK, "Post-event Survey"),
    ]

    title = models.CharField(max_length=255)
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
    

