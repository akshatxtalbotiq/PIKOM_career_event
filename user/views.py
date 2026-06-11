from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.http import require_POST

# Only superusers may manage staff accounts. Mirrors the campaign visibility
# rule already used in register/views.py (current_user.is_superuser).
superuser_required = user_passes_test(lambda u: u.is_superuser)

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        remember_me =  request.POST['remember_me']


        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)

            if not remember_me:
                # Session will expire when browser closes
                request.session.set_expiry(0)
            else:
                # Set session expiry to 2 weeks
                request.session.set_expiry(1209600)  # 2 weeks
                
            return HttpResponseRedirect('/campaign_list/')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        if request.user.is_authenticated:
            return HttpResponseRedirect('/campaign_list/')
        
    return render(request, 'user/login.html') 


def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/login/')


# ---------------------------------------------------------------------------
# Staff user management (superuser only)
#
# Lets a superuser add new login accounts from the dashboard instead of going
# through Django admin. New accounts are created with an *unusable* password
# and the user receives a "set your password" email (reusing the existing
# password-reset confirm flow), so no password is ever typed by the admin.
# ---------------------------------------------------------------------------

def _send_invite_email(request, user):
    """Send a set-password invite to a freshly created (or re-invited) user.

    Reuses the same password_reset_confirm URL / token machinery as the
    forgot-password flow, so the link the user clicks lands on the existing
    'Set a new password' page. Works even though the account has an unusable
    password, because the token generator does not require one.
    """
    context = {
        'user': user,
        'email': user.email,
        'protocol': 'https' if request.is_secure() else 'http',
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': default_token_generator.make_token(user),
    }
    subject = render_to_string('user/account_invite_subject.txt', context).strip()
    text_body = render_to_string('user/account_invite_email.txt', context)
    html_body = render_to_string('user/account_invite_email.html', context)
    send_mail(subject, text_body, None, [user.email],
              html_message=html_body, fail_silently=False)


@login_required
@superuser_required
def user_list(request):
    """Render the staff-account management page."""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'user/user_list.html', {'users': users})


@login_required
@superuser_required
@require_POST
def create_user(request):
    """Create a staff login account and email a set-password invite."""
    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    email = (request.POST.get('email') or '').strip().lower()
    username = (request.POST.get('username') or '').strip() or email
    is_superuser = request.POST.get('is_superuser') == 'true'

    if not email:
        return JsonResponse({'success': False, 'error': 'Email is required.'}, status=400)
    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'success': False, 'error': 'A user with that email already exists.'}, status=400)
    if User.objects.filter(username__iexact=username).exists():
        return JsonResponse({'success': False, 'error': 'A user with that username already exists.'}, status=400)

    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_staff=True,            # allows Django-admin access if granted perms
        is_superuser=is_superuser,
        is_active=True,
    )
    user.set_unusable_password()  # no password until they use the invite link
    user.save()

    invite_sent = True
    try:
        _send_invite_email(request, user)
    except Exception as exc:  # don't lose the account if SMTP hiccups
        invite_sent = False
        invite_error = str(exc)
        return JsonResponse({
            'success': True,
            'id': user.id,
            'invite_sent': False,
            'warning': f'User created, but the invite email could not be sent: {invite_error}',
        })

    return JsonResponse({'success': True, 'id': user.id, 'invite_sent': invite_sent})


@login_required
@superuser_required
def get_user(request, user_id):
    """Return a single user's data for populating the edit modal."""
    try:
        u = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
    return JsonResponse({
        'id': u.id,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'email': u.email,
        'username': u.username,
        'is_superuser': u.is_superuser,
        'is_active': u.is_active,
    })


@login_required
@superuser_required
@require_POST
def update_user(request):
    """Save edits to an existing user (name, email, username, superuser)."""
    user_id = request.POST.get('id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)

    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    email = (request.POST.get('email') or '').strip().lower()
    username = (request.POST.get('username') or '').strip() or email
    is_superuser = request.POST.get('is_superuser') == 'true'

    if not email:
        return JsonResponse({'success': False, 'error': 'Email is required.'}, status=400)
    if User.objects.filter(email__iexact=email).exclude(id=user.id).exists():
        return JsonResponse({'success': False, 'error': 'Another user already uses that email.'}, status=400)
    if User.objects.filter(username__iexact=username).exclude(id=user.id).exists():
        return JsonResponse({'success': False, 'error': 'Another user already uses that username.'}, status=400)

    # Don't let a superuser strip their own superuser status (avoids locking
    # yourself out of this very page).
    if user.id == request.user.id and not is_superuser:
        return JsonResponse({'success': False, 'error': 'You cannot remove your own superuser access.'}, status=400)

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.username = username
    user.is_superuser = is_superuser
    user.save()

    return JsonResponse({'success': True, 'id': user.id})


@login_required
@superuser_required
@require_POST
def resend_invite(request):
    """Resend the set-password invite email to an existing user."""
    user_id = request.POST.get('id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
    if not user.email:
        return JsonResponse({'success': False, 'error': 'User has no email address.'}, status=400)
    try:
        _send_invite_email(request, user)
    except Exception as exc:
        return JsonResponse({'success': False, 'error': f'Could not send email: {exc}'}, status=500)
    return JsonResponse({'success': True})


@login_required
@superuser_required
@require_POST
def impersonate(request, user_id):
    """Log the superuser in as another user ('Login as').

    The original superuser's id is stashed in the session so they can return
    to their own account via stop_impersonation. Note: `login()` flushes the
    session, so impersonator_id must be set *after* the login call.
    """
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
        return HttpResponseRedirect('/users/')
    if target.id == request.user.id:
        return HttpResponseRedirect('/users/')
    if not target.is_active:
        messages.error(request, 'Cannot log in as an inactive user.')
        return HttpResponseRedirect('/users/')

    impersonator_id = request.user.id
    login(request, target, backend='django.contrib.auth.backends.ModelBackend')
    request.session['impersonator_id'] = impersonator_id
    return HttpResponseRedirect('/campaign_list/')


@login_required
def stop_impersonation(request):
    """Return to the original superuser account after impersonating."""
    impersonator_id = request.session.get('impersonator_id')
    if not impersonator_id:
        return HttpResponseRedirect('/campaign_list/')
    try:
        original = User.objects.get(id=impersonator_id)
    except User.DoesNotExist:
        logout(request)
        return HttpResponseRedirect('/login/')
    # login() flushes the session, clearing impersonator_id automatically.
    login(request, original, backend='django.contrib.auth.backends.ModelBackend')
    return HttpResponseRedirect('/users/')


@login_required
@superuser_required
@require_POST
def toggle_user_active(request):
    """Activate / deactivate a user account."""
    user_id = request.POST.get('id')
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found.'}, status=404)
    if user.id == request.user.id:
        return JsonResponse({'success': False, 'error': 'You cannot deactivate your own account.'}, status=400)
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    return JsonResponse({'success': True, 'is_active': user.is_active})


