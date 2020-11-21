import redis
from django.conf import settings
from django.core.validators import RegexValidator, EmailValidator
from rest_framework import serializers, exceptions
from rest_framework.validators import UniqueValidator

from core.models import User
from core.tasks import send_email_with_confirm

PASSWORD_VALIDATOR = [RegexValidator(
    regex=r"^(?=.*[A-Z])(?=.*\d).{8,}$",
    message="Пароль должен содержать от 8 символов, 1 заглавную букву, 1 число.",
)]

UNIQUE_EMAIL_VALIDATOR = [UniqueValidator(
    queryset=User.objects.all(), message="Данный email уже зарегистрирован."
), EmailValidator(message="Введите корректный email")]

r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=2)


class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=255, validators=UNIQUE_EMAIL_VALIDATOR)
    password = serializers.CharField(validators=PASSWORD_VALIDATOR, write_only=True)
    password_confirm = serializers.CharField(min_length=8, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs.get("password") != attrs.pop("password_confirm", None):
            raise exceptions.ValidationError({"password": "Пароли не совпадают."})
        return super().validate(attrs)

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        send_email_with_confirm.delay(validated_data["email"])
        return user

    class Meta:
        model = User
        fields = ["full_name", "email", "password", "password_confirm"]


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.CharField(max_length=255, validators=UNIQUE_EMAIL_VALIDATOR)

    class Meta:
        model = User
        fields = ["full_name", "email"]


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, validators=PASSWORD_VALIDATOR, write_only=True)
    new_password_confirm = serializers.CharField(min_length=8, write_only=True)

    def validate(self, attrs):
        if not self.instance.check_password(attrs["password"]):
            raise exceptions.ValidationError({"password": "Неверный старый пароль"})

        if not attrs.get("new_password") or attrs["new_password"] != attrs.pop("new_password_confirm", None):
            raise exceptions.ValidationError({"message": "Новые пароли не совпадают"})

        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.set_password(validated_data["new_password"])
        instance.save()
        return instance

    def to_representation(self, instance):
        return {"message": f"Пароль успешно изменен"}

    class Meta:
        model = User
        fields = ["password", "new_password", "new_password_confirm"]


class EmailConfirmSerializer(serializers.ModelSerializer):
    code = serializers.IntegerField(min_value=100000, max_value=999999)

    def validate(self, attrs):
        code = r.get(self.instance.email).decode("utf-8")
        if not code or code != str(attrs["code"]):
            raise exceptions.ValidationError({"code": "Неверный код"})
        return super().validate(attrs)

    def update(self, instance, validated_data):
        instance.email_confirmed = True
        instance.save()
        return instance

    def to_representation(self, instance):
        return {"message": f"{instance.email} подтвержден."}

    class Meta:
        model = User
        fields = ["code"]
