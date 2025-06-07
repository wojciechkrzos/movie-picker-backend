from django.http import JsonResponse
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status


class APIRootView(View):
    """
    API Root endpoint that provides information about available endpoints
    """
    def get(self, request):
        return JsonResponse({
            "message": "Welcome to Movie Picker API",
            "version": "1.0",
            "endpoints": {
                "authentication": {
                    "login": "/login/",
                    "admin": "/admin/",
                    "api_auth": "/api/v1/auth/",
                    "google_login": "/api/v1/auth/google/",
                    "google_callback": "/api/v1/auth/google/callback/"
                }
            },
            "status": "active"
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Simple health check endpoint - publicly accessible
    """
    return Response({
        "status": "healthy",
        "message": "Movie Picker API is running"
    }, status=status.HTTP_200_OK)
