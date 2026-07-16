# Create your url patterns here.
from django.contrib import admin
from django.urls import path
from .views import index, save_registration, thankyou, sponsorship, save_sponsorship, sponsorship_thankyou, \
    get_registration_list, get_sponsorship_list, registration_list, sponsorship_list, campaign_list, tnc, send_qr, \
    create_campaign, submission_list, get_submission_list, get_campaign, update_remarks, update_registration_remarks, \
    check_taken_packages, talentgap2025_form, save_submission, submission_thankyou, survey_detail, survey_submit, \
    survey_thankyou, survey_list, \
    create_survey, get_survey, survey, survey_initial_submit, survey_submission_list, get_survey_submission_list, \
    survey_answer_view, send_survey_reminder, \
    manual_checkin, send_event_reminder, lead2025_form, exclude_columns, remove_submissions, survey_consolidated_pdf, \
    form_builder, save_question, get_question, delete_question, reorder_questions, form_public, form_initial_submit, \
    form_detail, form_submit, form_thankyou, registration_form_list, \
    upload_banner, delete_banner, save_identity_config, form_preview, \
    send_survey_qr, send_survey_event_reminder, send_survey_feedback_reminder, delete_survey_users, \
    set_survey_user_status, set_survey_user_checkin, save_event_details, save_email_content, preview_email, clone_survey, delete_survey, \
    get_survey_user_edit, update_survey_user, \
    register_walkin, survey_user_labels, survey_user_label_pdf, campaign_dashboard,set_survey_user_participant_type

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
    path('campaign_dashboard/<int:id>/', campaign_dashboard, name='campaign_dashboard'),
    path('submission_list/<str:id>/', submission_list, name='submission_list'),
    path('get_campaign/<str:id>/', get_campaign, name='get_campaign'),    
    path('update_remarks', update_remarks, name='update_remarks'),
    path('update_registration_remarks', update_registration_remarks, name='update_registration_remarks'),
    path('check_taken_packages', check_taken_packages, name='check_taken_packages'),
    
    path('tnc/', tnc, name='tnc'),
    path('send_qr/<str:id>', send_qr, name='send_qr'),
    path('create_campaign', create_campaign, name='create_campaign'),

    path('talentgap2025/', talentgap2025_form , name='talentgap2025'),
    path('lead2025/',lead2025_form , name='lead2025'),
    path('save_submission', save_submission, name='save_submission'),
    path('submission_thankyou/<str:reg_no>/', submission_thankyou, name='submission_thankyou'),

    path('survey_list/', survey_list, name='survey_list'),
    path('registration_forms/', registration_form_list, name='registration_form_list'),
    path('clone_survey/<int:survey_id>/', clone_survey, name='clone_survey'),
    path('delete_survey/<int:survey_id>/', delete_survey, name='delete_survey'),
    path("survey_page/<str:survey_id>/<int:user_id>/", survey_detail, name="survey_detail"),
    path("survey_page/<int:survey_id>/submit/", survey_submit, name="survey_submit"),
    path("survey/thank-you/<str:survey_id>/", survey_thankyou, name="survey_thankyou"),
    path('create_survey', create_survey, name='create_survey'),
    path('get_survey/<str:id>/', get_survey, name='get_survey'),
    path('survey/<str:survey_id>/', survey, name='survey'),
    path('consolidated_report/<str:survey_id>/', survey_consolidated_pdf, name='consolidated_report'),
    path("survey/<int:survey_id>/submit/", survey_initial_submit, name="survey_initial_submit"),

    path('survey_submission_list/<str:id>/', survey_submission_list, name='survey_submission_list'),
    path('get_survey_submission_list', get_survey_submission_list, name='get_survey_submission_list'),
    path('survey_answer_view/<str:survey_id>/<str:user_id>/', survey_answer_view, name='survey_answer_view'),
    path('send_survey_reminder/<str:id>', send_survey_reminder, name='send_survey_reminder'),

    path('manual_checkin/', manual_checkin, name='manual_checkin'),
    path('send_event_reminder/<str:id>', send_event_reminder, name='send_event_reminder'),

    # Form builder (admin authoring UI)
    path('form_builder/<int:survey_id>/', form_builder, name='form_builder'),
    path('save_question', save_question, name='save_question'),
    path('get_question/<int:question_id>/', get_question, name='get_question'),
    path('delete_question/<int:question_id>/', delete_question, name='delete_question'),
    path('reorder_questions/<int:survey_id>/', reorder_questions, name='reorder_questions'),
    path('upload_banner/<int:survey_id>/', upload_banner, name='upload_banner'),
    path('delete_banner/<int:survey_id>/', delete_banner, name='delete_banner'),
    path('save_identity_config/<int:survey_id>/', save_identity_config, name='save_identity_config'),
    path('form_preview/<int:survey_id>/', form_preview, name='form_preview'),
    path('save_event_details/<int:campaign_id>/', save_event_details, name='save_event_details'),
    path('save_email_content/<int:campaign_id>/', save_email_content, name='save_email_content'),
    path('preview_email/<int:survey_id>/<str:kind>/', preview_email, name='preview_email'),

    # Bulk actions on a form's registrations
    path('send_survey_qr/<int:survey_id>/', send_survey_qr, name='send_survey_qr'),
    path('send_survey_event_reminder/<int:survey_id>/', send_survey_event_reminder, name='send_survey_event_reminder'),
    path('send_survey_feedback_reminder/<int:survey_id>/', send_survey_feedback_reminder, name='send_survey_feedback_reminder'),
    path('delete_survey_users/<int:survey_id>/', delete_survey_users, name='delete_survey_users'),
    path('set_survey_user_status/<int:survey_id>/', set_survey_user_status, name='set_survey_user_status'),
    path('set_survey_user_participant_type/<int:survey_id>/', set_survey_user_participant_type, name='set_survey_user_participant_type'),
    path('set_survey_user_checkin/<int:survey_id>/', set_survey_user_checkin, name='set_survey_user_checkin'),
    path('get_survey_user_edit/<int:survey_id>/<int:user_id>/', get_survey_user_edit, name='get_survey_user_edit'),
    path('update_survey_user/<int:survey_id>/<int:user_id>/', update_survey_user, name='update_survey_user'),
    path('register_walkin/<int:survey_id>/', register_walkin, name='register_walkin'),
    path('survey_user_labels/<int:survey_id>/', survey_user_labels, name='survey_user_labels'),
    path('survey_user_label_pdf/<int:survey_id>/', survey_user_label_pdf, name='survey_user_label_pdf'),

    # Generic public registration flow. /event/ is the user-facing path. The
    # legacy /form/ paths are kept as silent fallbacks so any QR codes / emails
    # already shared continue to work. URL names are unchanged, so all
    # `{% url 'form_public' %}` template tags now resolve to /event/<slug>/.
    path('event/<str:survey_code>/', form_public, name='form_public'),
    path('event/<int:survey_id>/start/', form_initial_submit, name='form_initial_submit'),
    path('event/<str:survey_code>/q/<int:user_id>/', form_detail, name='form_detail'),
    path('event/<int:survey_id>/submit/', form_submit, name='form_submit'),
    path('event/<str:survey_code>/thanks/<int:user_id>/', form_thankyou, name='form_thankyou'),

    # Legacy /form/ aliases (do NOT carry name= so reverse() picks /event/)
    path('form/<str:survey_code>/', form_public),
    path('form/<int:survey_id>/start/', form_initial_submit),
    path('form/<str:survey_code>/q/<int:user_id>/', form_detail),
    path('form/<int:survey_id>/submit/', form_submit),
    path('form/<str:survey_code>/thanks/<int:user_id>/', form_thankyou),
    path('exclude_columns/', exclude_columns, name='exclude_columns'),
    path('remove_submissions/', remove_submissions, name='remove_submissions'),

]
