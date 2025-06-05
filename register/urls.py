# Create your url patterns here.
from django.contrib import admin
from django.urls import path
from .views import index, save_registration, thankyou, sponsorship, save_sponsorship, sponsorship_thankyou, \
    get_registration_list, get_sponsorship_list, registration_list, sponsorship_list, campaign_list, tnc, send_qr,create_campaign,submission_list, get_submission_list,get_campaign, update_remarks, update_registration_remarks, \
    check_taken_packages

urlpatterns = [
    path('', index, name='index'),
    path('save_registration', save_registration, name='save_registration'),
    path('thankyou/<str:reg_no>/', thankyou, name='thankyou'),
    path('sponsorship', sponsorship, name='sponsorship'),
    path('save_sponsorship', save_sponsorship, name='save_sponsorship'),
    path('sponsorship_thankyou/<str:reg_no>/', sponsorship_thankyou, name='sponsorship_thankyou'),
    path('get_registration_list', get_registration_list, name='get_registration_list'),
    path('get_sponsorship_list', get_sponsorship_list, name='get_sponsorship_list'),
    path('get_submission_list', get_submission_list, name='get_submission_list'),
    path('registration_list/<str:id>/', registration_list, name='registration_list'),
    path('sponsorship_list/<str:id>/', sponsorship_list, name='sponsorship_list'),
    path('campaign_list/', campaign_list, name='campaign_list'),
    path('submission_list/<str:id>/', submission_list, name='submission_list'),
    path('get_campaign/<str:id>/', get_campaign, name='get_campaign'),    
    path('update_remarks', update_remarks, name='update_remarks'),
    path('update_registration_remarks', update_registration_remarks, name='update_registration_remarks'),
    path('check_taken_packages', check_taken_packages, name='check_taken_packages'),
    
    path('tnc/', tnc, name='tnc'),
    path('send_qr/<str:id>', send_qr, name='send_qr'),
    path('create_campaign', create_campaign, name='create_campaign'),
]
