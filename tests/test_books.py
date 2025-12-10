import pytest
from fastapi import status


def test_search_books(client, test_user):
    login_data = {
        "username": "testuser",
        "password": "TestPass123!"
    }

    login_response = client.post("/api/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/books/",
        params={"query": "тест", "page": 1, "size": 10},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_create_book(client, test_user):

    login_data = {
        "username": "testuser",
        "password": "TestPass123!"
    }

    login_response = client.post("/api/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    book_data = {
        "title": "Тест кітабы",
        "isbn": "123-456-789",
        "publish_year": 2023,
        "author_ids": []
    }

    response = client.post(
        "/api/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_book_by_id(client, test_user):

    login_data = {
        "username": "testuser",
        "password": "TestPass123!"
    }

    login_response = client.post("/api/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/books/999999",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND