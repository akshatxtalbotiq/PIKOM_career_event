from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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


