from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password


class CreateUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    name = serializers.CharField(source='user_name', required=True)

    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'push_token', 'preferences')

    def validate(self, attrs):
        """
        class UserPreference:
            email: bool
            push: bool
        """
        preferences = attrs.get("prefeferences")
        if preferences:
            if not isinstance(preferences, dict):
                raise serializers.ValidationError("Preferences must be a dictionary")
            if "email" not in preferences or "push" not in preferences:
                raise serializers.ValidationError("Preferences must include 'email' and 'push' keys")
            if not isinstance(preferences["email"], bool) or not isinstance(preferences["push"], bool):
                raise serializers.ValidationError("'email' and 'push' preferences must be boolean values")
        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            user_name=validated_data['user_name'],
            push_token=validated_data.get('push_token', ''),
            preferences=validated_data.get('preferences')
        )
        user.set_password(validated_data['password'])
        user.save()
        return user
