from rest_framework import serializers
from django.contrib.auth import authenticate
from accounts.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

class RegisterRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField(allow_blank=True, required=False)
    password = serializers.CharField(min_length=6, write_only=True)

    def validate_username(self, value):
        v = value.strip().lower()
        if User.objects.filter(username=v).exists():
            raise serializers.ValidationError("username already exists")
        return v

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            name=validated_data.get("name", "")
        )
        return user

class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs["username"].strip().lower()
        password = attrs["password"]
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("user is inactive")
        attrs["user"] = user
        return attrs

class RefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class MeResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "name")

def make_token_pair(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
