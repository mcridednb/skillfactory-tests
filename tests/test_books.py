import pytest
from django.urls import reverse
from rest_framework import status

# to use db
pytestmark = pytest.mark.django_db(transaction=True)


def test__book_add__success(client, book):
    response = client.post(reverse("book-list"), book, format="json")
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == book["title"]
    assert response.json()["author"] == book["author"]


def test__book_add__fail(client):
    response = client.post(reverse("book-list"), {}, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"author": ["Это поле обязательно."], "title": ["Это поле обязательно."]}


def test__book_list__success(client, book):
    client.post(reverse("book-list"), book, format="json")

    response = client.get(reverse("book-list"))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["title"] == book["title"]
    assert response.json()[0]["author"] == book["author"]


def test__book_get_detail__success(client, book):
    response = client.post(reverse("book-list"), book, format="json")
    book_id = response.json()["id"]
    response = client.get(reverse("book-detail", kwargs={"pk": book_id}))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == book["title"]
    assert response.json()["author"] == book["author"]


def test__book_get_detail__not_found__fail(client):
    book_id = 123
    response = client.get(reverse("book-detail", kwargs={"pk": book_id}))
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test__book_delete__success(client, book):
    response = client.post(reverse("book-list"), book, format="json")
    book_id = response.json()["id"]
    response = client.delete(reverse("book-detail", kwargs={"pk": book_id}))
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test__book_delete__fail(client, book):
    book_id = 123
    response = client.delete(reverse("book-detail", kwargs={"pk": book_id}))
    assert response.status_code == status.HTTP_404_NOT_FOUND
