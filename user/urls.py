from django.urls import path
from .views import user_login,user_logout


urlpatterns = [
    
    path('login/', user_login, name='login'),  # URL pattern for user login
    path('logout/', user_logout, name='logout'), # URL pattern for user logout
   
]
