from django.urls import path
from .views import GoogleLogin, GoogleLoginCallback, LoginPage, protected_view

urlpatterns = [
    path('google/', GoogleLogin.as_view(), name='google_login'),
    path('google/callback/', GoogleLoginCallback.as_view(), name='google_login_callback'),
    path('login/', LoginPage.as_view(), name='login'),
    path('test/', protected_view, name='protected_test'),
]
