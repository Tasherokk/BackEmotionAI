from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken

class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()

class RegisterRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    name = serializers.CharField(allow_blank=True, required=False)
    password = serializers.CharField(min_length=6, write_only=True)
    photo = serializers.ImageField(required=True)
    company_id = serializers.IntegerField(required=False, allow_null=True)
    department_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_username(self, value):
        v = value.strip().lower()
        if User.objects.filter(username=v).exists():
            raise serializers.ValidationError("username already exists")
        return v

    def create(self, validated_data):
        company_id = validated_data.pop('company_id', None)
        department_id = validated_data.pop('department_id', None)
        photo = validated_data.pop('photo', None)
        
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            name=validated_data.get("name", ""),
            company_id=company_id,
            department_id=department_id
        )
        if photo:
            user.photo = photo
            user.save()
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

class PhotoLoginRequestSerializer(serializers.Serializer):
    photo = serializers.ImageField(required=True)

class MeResponseSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)
    
    class Meta:
        model = User
        fields = ("id", "username", "name", "role", "company", "company_name", "department", "department_name")

def make_token_pair(user: User) -> dict:
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}
