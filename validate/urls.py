from django.urls import path

from validate import views

urlpatterns = [
    path('scangolf/', views.scan_page_golf, name='scangolf'),
    path('scan/<str:id>', views.scan_page, name='scan'),
    path('validate/<uuid:code>', views.validate, name='validate'),
    path('validategolf/<uuid:code>', views.validategolf, name='validategolf'),
]