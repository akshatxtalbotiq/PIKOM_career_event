from django.db import models

# Create your models here.

class Registration(models.Model):
    reg_no = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100) 
    email = models.EmailField()
    mobile = models.CharField(max_length=20)
    created_on = models.DateTimeField(auto_now_add=True)
    lastmodified = models.DateTimeField(auto_now=True)

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

    title = models.CharField(max_length=10, choices=TITLE_CHOICES,null=True, blank=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=20, blank=True, db_column="mobile")
    designation = models.CharField(max_length=100, db_column="designation",null=True, blank=True)
    organization = models.CharField(max_length=100, blank=True, db_column="organization")
    handicap = models.CharField(max_length=10, db_column="handicap",null=True, blank=True)
    tshirt_size = models.CharField(max_length=5, choices=TSHIRT_SIZES, db_column="tsize", blank=True)
    fkregistration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='players', db_column="fkRegistration",default=None)

    def __str__(self):
        return self.name
    

class Sponsorship(models.Model):   
    TITLE_CHOICES = [
        ('Mr', 'Mr'),
        ('Ms', 'Ms'),
        ('Mrs', 'Mrs'),
        ('Dr', 'Dr'),
        ('Prof', 'Prof'),
        ('Sir', 'Sir'),
        ('Madam', 'Madam'),
    ]
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
        ('P13', '2 GOLFER SPONSOR (RM 2,200)'),
    ]    

    reg_no = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=10, choices=TITLE_CHOICES)
    contact_name = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=20)
    contact_email = models.EmailField()

    billing_organization = models.CharField(max_length=100)
    billing_name = models.CharField(max_length=100)
    billing_email = models.EmailField()
    billing_designation = models.CharField(max_length=100)
    billing_address = models.TextField()

    submitted_at = models.DateTimeField(auto_now_add=True)

    package = models.CharField(max_length=10, choices=PACKAGE_CHOICES, db_column="package", default=None)

    

    def __str__(self):
        return f"{self.contact_name} - {self.contact_email}"