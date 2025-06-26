from django.db import models
import uuid
from datetime import datetime

# def upload_sponsor_attachment(instance, filename):
#     year = datetime.now().year
#     return f"sponsors/{year}/{filename}"


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
    campaign_code = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=255)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    url = models.URLField(max_length=255, null=True, blank=True)
    need_qr = models.BooleanField(default=False)
    pic_email = models.TextField(null=True, blank=True)   

    def __str__(self):
        return self.title
    

class Submission(models.Model):
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
    campaign_code = models.CharField(max_length=255)    
    remarks = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    
    

