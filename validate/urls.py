from django.urls import path

from validate import views

urlpatterns = [
    path('scan/', views.scan_page, name='scan'),
    path('validate/<uuid:code>/', views.validate, name='validate'),
]