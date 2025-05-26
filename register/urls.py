# Create your url patterns here.
from django.contrib import admin
from django.urls import path
from .views import index,save_registration,thankyou,sponsorship,save_sponsorship,sponsorship_thankyou, get_registration_list, get_sponsorship_list, registration_list, sponsorship_list,campaign_list,tnc


urlpatterns = [
    path('', index, name='index'),
    path('save_registration', save_registration, name='save_registration'),
    path('thankyou/<str:reg_no>/', thankyou, name='thankyou'),
    path('sponsorship', sponsorship, name='sponsorship'),
    path('save_sponsorship', save_sponsorship, name='save_sponsorship'),
    path('sponsorship_thankyou/<str:reg_no>/', sponsorship_thankyou, name='sponsorship_thankyou'),
    path('get_registration_list', get_registration_list, name='get_registration_list'),
    path('get_sponsorship_list', get_sponsorship_list, name='get_sponsorship_list'),
    path('registration_list/', registration_list, name='registration_list'),
    path('sponsorship_list/', sponsorship_list, name='sponsorship_list'),
    path('campaign_list/', campaign_list, name='campaign_list'),
    path('tnc/', tnc, name='tnc'),
]
