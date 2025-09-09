from django.contrib import admin

# Register your models here.
from .models import Survey, Campaign
admin.site.register(Survey)
admin.site.register(Campaign)
