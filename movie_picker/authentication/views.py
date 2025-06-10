from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import render
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import RetrieveAPIView, ListAPIView, UpdateAPIView
from django.db import transaction
from .models import Question, Answer
from .serializers import (
    QuestionSerializer, QuizAnswersSerializer, UserProfileSerializer,
    UserStreamingServiceUpdateSerializer
)


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.GOOGLE_OAUTH_CALLBACK_URL
    client_class = OAuth2Client
    permission_classes = [AllowAny]  # Added permission class


class GoogleLoginCallback(APIView):
    permission_classes = [AllowAny]  # Added permission class

    def get(self, request, *args, **kwargs):
        """
        Handle the callback from Google OAuth and attempt to log in the user.
        """
        code = request.GET.get("code")

        if code is None:
            return Response({"error": "Authorization code not provided"}, status=status.HTTP_400_BAD_REQUEST)

        token_endpoint_url = request.build_absolute_uri(reverse("google_login"))
        internal_response = requests.post(url=token_endpoint_url, data={"code": code})

        response_data = {}
        # Determine response_data based on internal_response
        if 200 <= internal_response.status_code < 300:  # Success from internal call
            try:
                response_data = internal_response.json()
            except requests.exceptions.JSONDecodeError:
                # This is unexpected if SocialLoginView works correctly (should return JSON with tokens)
                response_data = {"error": "Login successful, but response format from login service was unexpected."}
        else:  # Error from internal_response (e.g., 4xx, 5xx)
            try:
                # DRF errors are usually JSON
                response_data = internal_response.json()
            except requests.exceptions.JSONDecodeError:
                # Non-JSON error from SocialLoginView or underlying layers
                response_data = {
                    "error": "Login failed during token exchange.",
                    "detail": f"Internal login service responded with status {internal_response.status_code}.",
                    "debug_info": internal_response.text[:200]  # Add a snippet of the response for debugging
                }

        return Response(
            response_data,
            status=internal_response.status_code  # Pass through the status from the internal call
        )


class LoginPage(View):
    def get(self, request, *args, **kwargs):
        return render(
            request,
            "pages/login.html",
            {
                "google_callback_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
                "google_client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            },
        )


class SuccessPage(View):
    def get(self, request, *args, **kwargs):
        return render(request, "pages/success.html")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def protected_view(request):
    """
    A simple protected view to test JWT authentication
    """
    return Response({
        'message': 'Hello authenticated user!',
        'user': request.user.email,
        'user_id': request.user.id
    }, status=status.HTTP_200_OK)


class UserProfileView(RetrieveAPIView):
    """
    Return user info with preferences (streaming services, quiz answers)
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class QuestionsListView(ListAPIView):
    """
    Get all available quiz questions
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]


class UserStreamingServicesView(UpdateAPIView):
    """
    PUT/PATCH: Update user's streaming services
    """
    serializer_class = UserStreamingServiceUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()

            # Return updated user profile with streaming services
            profile_serializer = UserProfileSerializer(user)
            return Response({
                'message': 'Streaming services updated successfully',
                'user': profile_serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class QuizAnswersView(APIView):
    """
    POST quiz answers to save user responses
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = QuizAnswersSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        answers_data = serializer.validated_data['answers']
        user = request.user

        # Save quiz answers
        with transaction.atomic():
            for answer_data in answers_data:
                question_id = answer_data['question_id']
                answer_text = answer_data['answer']

                # Update or create the answer
                Answer.objects.update_or_create(
                    user=user,
                    question_id=question_id,
                    defaults={'answer': answer_text}
                )

        return Response({
            'message': 'Quiz answers saved successfully'
        }, status=status.HTTP_201_CREATED)
