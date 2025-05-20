# Create your url patterns here.
from django.contrib import admin
from django.urls import path
from .views import index,save_registration,thankyou

urlpatterns = [
    path('', index, name='index'),
    path('save_registration', save_registration, name='save_registration'),
    path('thankyou/<str:reg_no>/', thankyou, name='thankyou'),
]
