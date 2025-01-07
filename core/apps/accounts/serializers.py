from django.contrib.auth.hashers import make_password
from rest_framework import serializers

from apps.accounts.models import User


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password')

    def validate_password(self, value: str) -> str:
        return make_password(value)
