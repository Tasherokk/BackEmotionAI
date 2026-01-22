from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .services.face_auth import verify_face_authorization
from drf_spectacular.utils import extend_schema, OpenApiExample

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
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        request=RegisterRequestSerializer,
        responses={201: MeResponseSerializer},
        description="Register a new user with username, password, name, and photo",
        examples=[
            OpenApiExample(
                "Register Example",
                value={
                    "username": "john_doe",
                    "password": "secret123",
                    "name": "John Doe",
                    "company_id": 1,
                    "department_id": 1
                }
            )
        ]
    )
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

    @extend_schema(
        request=LoginRequestSerializer,
        responses={200: MeResponseSerializer},
        description="Login with username and password",
        examples=[
            OpenApiExample(
                "Login Example",
                value={
                    "username": "john_doe",
                    "password": "secret123"
                }
            )
        ]
    )
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

    @extend_schema(
        request=RefreshRequestSerializer,
        responses={200: {"type": "object", "properties": {"access": {"type": "string"}}}},
        description="Refresh access token using refresh token",
        examples=[
            OpenApiExample(
                "Refresh Example",
                value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."}
            )
        ]
    )
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

    @extend_schema(
        responses={200: MeResponseSerializer},
        description="Get current authenticated user information"
    )
    def get(self, request):
        return Response(MeResponseSerializer(request.user).data, status=status.HTTP_200_OK)


class PhotoLoginView(APIView):
    """
    Photo-based authorization endpoint.
    Accepts a photo from user, compares with their stored photo via AI service.
    Requires authentication token to identify the user.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=PhotoLoginRequestSerializer,
        responses={
            200: {"type": "object", "properties": {"verdict": {"type": "string"}, "detail": {"type": "string"}}},
            401: {"type": "object", "properties": {"verdict": {"type": "string"}, "detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
        },
        description="Authorize user by comparing uploaded photo with stored photo using AI face recognition"
    )
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
