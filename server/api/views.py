from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    RegisterRequestSerializer,
    LoginRequestSerializer,
    RefreshRequestSerializer,
    MeResponseSerializer,
    make_token_pair
)

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        tokens = make_token_pair(user)
        return Response(tokens, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]
        tokens = make_token_pair(user)
        return Response(tokens, status=status.HTTP_200_OK)

class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RefreshRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        refresh_str = ser.validated_data["refresh"]

        try:
            refresh = RefreshToken(refresh_str)
            access = str(refresh.access_token)
            return Response({"access": access}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({"detail": "invalid refresh"}, status=status.HTTP_401_UNAUTHORIZED)

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(MeResponseSerializer(request.user).data, status=status.HTTP_200_OK)
