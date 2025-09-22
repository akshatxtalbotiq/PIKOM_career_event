# Create your url patterns here.
from django.contrib import admin
from django.urls import path
from .views import index, save_registration, thankyou, sponsorship, save_sponsorship, sponsorship_thankyou, \
    get_registration_list, get_sponsorship_list, registration_list, sponsorship_list, campaign_list, tnc, send_qr,create_campaign,submission_list, get_submission_list,get_campaign, update_remarks, update_registration_remarks, \
    check_taken_packages,talentgap2025_form, save_submission,submission_thankyou, survey_detail, survey_submit, survey_thankyou,survey_list, \
    create_survey,get_survey,survey,survey_initial_submit, survey_submission_list,get_survey_submission_list, survey_answer_view,send_survey_reminder

urlpatterns = [
    path('', campaign_list, name='campaign_list'),
    path('index', index, name='index'),
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

    path('talentgap2025/', talentgap2025_form , name='talentgap2025'),
    path('save_submission', save_submission, name='save_submission'),
    path('submission_thankyou/<str:reg_no>/', submission_thankyou, name='submission_thankyou'),

    path('survey_list/', survey_list, name='survey_list'),
    path("survey_page/<str:survey_id>/<int:user_id>/", survey_detail, name="survey_detail"),
    path("survey_page/<int:survey_id>/submit/", survey_submit, name="survey_submit"),
    path("survey/thank-you/<str:survey_id>/", survey_thankyou, name="survey_thankyou"),
    path('create_survey', create_survey, name='create_survey'),
    path('get_survey/<str:id>/', get_survey, name='get_survey'),
    path('survey/<str:survey_id>/', survey, name='survey'),
    path("survey/<int:survey_id>/submit/", survey_initial_submit, name="survey_initial_submit"),

    path('survey_submission_list/<str:id>/', survey_submission_list, name='survey_submission_list'),
    path('get_survey_submission_list', get_survey_submission_list, name='get_survey_submission_list'),
    path('survey_answer_view/<str:survey_id>/<str:user_id>/', survey_answer_view, name='survey_answer_view'),
    path('send_survey_reminder/<str:id>', send_survey_reminder, name='send_survey_reminder'),
]
