from django.contrib import admin

# Register your models here.
from .models import Booth, Campaign, EventSession, FloorMap, SessionRegistration, Survey

admin.site.register([Survey, Campaign, EventSession, SessionRegistration, FloorMap, Booth])
