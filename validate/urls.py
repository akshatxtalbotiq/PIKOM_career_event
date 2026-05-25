from django.urls import path

from validate import views

urlpatterns = [
    path('scangolf/', views.scan_page_golf, name='scangolf'),
    path('scan/<str:id>', views.scan_page, name='scan'),
    path('scanform/<str:survey_code>', views.scan_page_survey, name='scanform'),
    path('validate/<uuid:code>', views.validate, name='validate'),
    path('validategolf/<uuid:code>', views.validategolf, name='validategolf'),
    path('validatesurvey/<uuid:code>', views.validatesurvey, name='validatesurvey'),
]