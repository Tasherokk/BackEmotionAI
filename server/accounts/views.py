from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .services.face_auth import verify_face_authorization

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import (
    RegisterRequestSerializer,
    LoginRequestSerializer,
    RefreshRequestSerializer,
    PhotoLoginRequestSerializer,
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

        return Response(
            {**tokens, "user": MeResponseSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]
        tokens = make_token_pair(user)

        return Response(
            {**tokens, "user": MeResponseSerializer(user).data},
            status=status.HTTP_200_OK
        )


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


class PhotoLoginView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    """
    Photo-based authorization endpoint.
    Accepts a photo from user, compares with their stored photo via AI service.
    Requires authentication token to identify the user.
    """

    def post(self, request):
        serializer = PhotoLoginRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uploaded_photo = serializer.validated_data['photo']
        user = request.user
        
        # Check if user has a photo
        if not user.photo:
            return Response(
                {"detail": "User has no registered photo"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Verify face authorization using AI service
            ai_result = verify_face_authorization(user.photo, uploaded_photo)
            
            # Check verdict
            verdict = ai_result.get('verdict', 'NO')
            
            if verdict == 'YES':
                return Response(
                    {"verdict": "YES", "detail": "Authorization successful"},
                    status=status.HTTP_200_OK
                )
            else:
                # NO or RETRY both count as failure
                return Response(
                    {"verdict": "NO", "detail": "Authorization failed"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
        except Exception as e:
            return Response(
                {"detail": f"Authorization error: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
