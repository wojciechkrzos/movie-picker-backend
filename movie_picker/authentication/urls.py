from django.urls import path
from .views import (
    GoogleLogin, GoogleLoginCallback, LoginPage, protected_view,
    UserProfileView, QuestionsListView, QuizAnswersView
)

urlpatterns = [
    path('google/', GoogleLogin.as_view(), name='google_login'),
    path('google/callback/', GoogleLoginCallback.as_view(), name='google_login_callback'),
    path('login/', LoginPage.as_view(), name='login'),
    path('test/', protected_view, name='protected_test'),

    # New endpoints for frontend requirements
    path('profile/', UserProfileView.as_view(), name='user_profile'),  # Endpoint #2
    path('questions/', QuestionsListView.as_view(), name='questions_list'),
    path('quiz-answers/', QuizAnswersView.as_view(), name='quiz_answers'),  # Endpoint #3
]
