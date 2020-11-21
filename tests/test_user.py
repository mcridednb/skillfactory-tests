from unittest.mock import patch

import pytest
from django.test import override_settings
from django.urls import reverse
from rest_framework import status

from core.models import User

# To use db
pytestmark = pytest.mark.django_db(transaction=True)


def test__user_registration__success(client, user_data):
    user_data["password_confirm"] = user_data["password"]

    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    user_data.pop("password")
    user_data.pop("password_confirm")
    assert response.json() == user_data


def test__user_registration__invalid_fields__fail(client, user_data):
    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["password"] == ["Пароли не совпадают."]

    user_data["password"] = "123"
    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["password"] == ["Пароль должен содержать от 8 символов, 1 заглавную букву, 1 число."]

    response = client.post(reverse("registration"), {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    for field in ["full_name", "email", "password"]:
        assert response.json()[field] == ["Это поле обязательно."]

    response = client.post(reverse("registration"), {"email": "sldhkasjd"}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["email"] == ["Введите корректный email"]


def test__user_registration__already_exist__fail(client, user_data):
    user_data["password_confirm"] = user_data["password"]

    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["email"] == ["Данный email уже зарегистрирован."]


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
@patch("django.core.mail.send_mail")
@patch("redis.Redis.set")
def test__email_send_code__success(redis_set, send_mail, client, user_data):
    user_data["password_confirm"] = user_data["password"]

    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    assert send_mail.called
    assert send_mail.call_count == 1
    assert send_mail.call_args[0][3][0] == user_data["email"]

    assert redis_set.called
    assert redis_set.call_count == 1
    assert redis_set.call_args[0][0] == user_data["email"]
    assert redis_set.call_args[0][1] in send_mail.call_args[0][1]
    assert redis_set.call_args[1]["ex"] == 60 * 60 * 24


@patch("redis.Redis.get")
def test__email_confirm__success(redis_get, api_client, user_data):
    code = 800555

    redis_get.return_value = str(code).encode("utf-8")

    user = User.objects.get(id=1)
    assert not user.email_confirmed

    response = api_client.patch(reverse("email-confirm"), {"code": code}, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == f"{user_data['email']} подтвержден."

    user.refresh_from_db()
    assert user.email_confirmed

    assert redis_get.called
    assert redis_get.call_count == 1
    assert redis_get.call_args[0][0] == user_data["email"]


@patch("redis.Redis.get")
def test__email_confirm__fail(redis_get, api_client, user_data):
    code = 800555
    invalid_code = 800666

    redis_get.return_value = str(code).encode("utf-8")

    user = User.objects.get(id=1)
    assert not user.email_confirmed

    response = api_client.patch(reverse("email-confirm"), {"code": invalid_code}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["code"][0] == "Неверный код"

    user.refresh_from_db()
    assert not user.email_confirmed

    assert redis_get.called
    assert redis_get.call_count == 1
    assert redis_get.call_args[0][0] == user_data["email"]


def test__get_profile__success(api_client, user_data):
    response = api_client.get(reverse("profile"))
    user_data.pop("password")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == user_data


def test__update_user_data__success(api_client):
    body = {
        "full_name": "Николай",
    }

    response = api_client.patch(reverse("profile"), body, format="json")
    assert response.status_code == status.HTTP_200_OK

    assert response.json()["full_name"] == body["full_name"]

    response = api_client.patch(reverse("profile"), {"phone": "+88005553535"}, format="json")
    assert response.status_code == status.HTTP_200_OK


def test__update_user_data__fail(client, api_client, user_data):
    user_data["password_confirm"] = user_data["password"]
    user_data["email"] = "nick@yandex.ru"

    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    user_data.pop("password")
    user_data.pop("password_confirm")

    response = api_client.patch(reverse("profile"), user_data, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["email"][0] == "Данный email уже зарегистрирован."


def test__get_token__success(client, user_data):
    user_data["password_confirm"] = user_data["password"]

    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    body = {
        "email": user_data["email"],
        "password": user_data["password"],
    }
    response = client.post(reverse("token-obtain-pair"), body, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access"]
    assert response.json()["refresh"]


def test__get_token__fail(client, user_data):
    user_data["password_confirm"] = user_data["password"]

    response = client.post(reverse("registration"), user_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    body = {
        "email": user_data["email"],
        "password": user_data["password"] + "1",
    }
    response = client.post(reverse("token-obtain-pair"), body, format="json")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "No active account found with the given credentials"


def test__change_user_password__success(api_client, user_data):
    body = {
        "password": user_data["password"],
        "new_password": user_data["password"] + "1",
        "new_password_confirm": user_data["password"] + "1",
    }

    response = api_client.patch(reverse("change-password"), body, format="json")
    assert response.status_code == status.HTTP_200_OK

    body = {
        "email": user_data["email"],
        "password": body["new_password"],
    }
    response = api_client.post(reverse("token-obtain-pair"), body, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access"]
    assert response.json()["refresh"]


def test__change_user_password__fail(api_client, user_data):
    body = {
        "password": user_data["password"] + "1",
        "new_password": user_data["password"],
        "new_password_confirm": user_data["password"],
    }

    response = api_client.patch(reverse("change-password"), body, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["password"][0] == "Неверный старый пароль"

    body = {
        "password": user_data["password"],
        "new_password": user_data["password"] + "1",
        "new_password_confirm": user_data["password"],
    }

    response = api_client.patch(reverse("change-password"), body, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["message"][0] == "Новые пароли не совпадают"
