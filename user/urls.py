from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import user_login, user_logout


urlpatterns = [

    path('login/', user_login, name='login'),  # URL pattern for user login
    path('logout/', user_logout, name='logout'),  # URL pattern for user logout

    # Forgot / reset password flow (uses Django's built-in auth views with
    # project-specific templates that match the existing login styling).
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(
            template_name='user/password_reset.html',
            email_template_name='user/password_reset_email.html',
            subject_template_name='user/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='user/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='user/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='user/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
