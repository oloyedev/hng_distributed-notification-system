from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CreateUserSerializer
from .models import User

class CreateUserView(APIView):
    """
    Request Body:{
      name: str
      email: Email
      push_token: Optional[str]  # can be updated with an update endpoint
      preferences: UserPreference
      password: str
    }

    class UserPreference:
        email: bool
        push: bool
    """
    def post(self, request):
        serializer = CreateUserSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": f"User {user.email} created successfully"}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    """
    Request Body:{
      email: Email
      password: str
    }
    """
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                tokens = user.tokens()
                return Response(
                    {
                        "access_tokens": tokens["access"],
                        "refresh_token": tokens["refresh"]
                    }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        except User.DoesNotExist:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
