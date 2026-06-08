from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    user_login, user_logout,
    user_list, create_user, get_user, update_user, resend_invite, toggle_user_active,
    impersonate, stop_impersonation,
)


urlpatterns = [

    path('login/', user_login, name='login'),  # URL pattern for user login
    path('logout/', user_logout, name='logout'),  # URL pattern for user logout

    # Staff user management (superuser only)
    path('users/', user_list, name='user_list'),
    path('users/create/', create_user, name='create_user'),
    path('users/get/<int:user_id>/', get_user, name='get_user'),
    path('users/update/', update_user, name='update_user'),
    path('users/resend_invite/', resend_invite, name='resend_invite'),
    path('users/toggle_active/', toggle_user_active, name='toggle_user_active'),
    path('users/impersonate/<int:user_id>/', impersonate, name='impersonate'),
    path('stop_impersonation/', stop_impersonation, name='stop_impersonation'),

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
