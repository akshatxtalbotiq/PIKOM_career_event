from django.contrib import admin

# Register your models here.
from .models import (
    Booth, Campaign, Employer, EventSession, FloorMap, InterviewBooking,
    InterviewSlot, Job, JobBookmark, SessionRegistration, Survey,
    TrainingProvider, University, UniversityProgram, VoucherClaim,
    VoucherPromotion,
)

admin.site.register([Survey, Campaign, EventSession, SessionRegistration, FloorMap, Booth])
admin.site.register([
    Employer, Job, JobBookmark, InterviewSlot, InterviewBooking, University,
    UniversityProgram, TrainingProvider, VoucherPromotion, VoucherClaim,
])
