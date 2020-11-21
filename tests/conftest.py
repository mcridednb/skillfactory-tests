import pytest
from rest_framework.test import APIClient

from core.models import User


@pytest.fixture
def book():
    return {
        "author": "Булгаков",
        "title": "Мастер и Маргарита",
    }


@pytest.fixture
def user_data():
    return {
        "full_name": "Афанасьев Николай",
        "email": "nick@gmail.com",
        "password": "kLmN0PzzZ",
    }


@pytest.fixture
def api_client(user_data):
    client = APIClient()
    password = user_data.get("password")
    user = User.objects.create(id=1, **user_data)
    user.set_password(password)
    user.save()
    client.force_authenticate(user)
    return client


@pytest.fixture
def another_api_client(user_data):
    client = APIClient()
    user_data["email"] = "nick@yandex.ru"
    password = user_data.get("password")
    user = User.objects.create(id=2, **user_data)
    user.set_password(password)
    user.save()
    client.force_authenticate(user)
    return client
