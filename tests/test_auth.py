import pytest
from fastapi import status


def test_register_user(client):
    user_data = {
        "username": "newuser",
        "email": "newuser@university.edu",
        "password": "NewPass123!",
        "full_name": "New User",
    }

    response = client.post("/api/auth/register", json=user_data)

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "user_id" in data
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data


def test_register_duplicate_username(client, test_user):
    user_data = {
        "username": "testuser",  # Бұрыннан бар
        "email": "different@university.edu",
        "password": "DifferentPass123!",
        "full_name": "Different User"
    }

    response = client.post("/api/auth/register", json=user_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Пайдаланушы аты немесе email бұрыннан бар" in response.json()["detail"]


def test_login_success(client, test_user):
    login_data = {
        "username": "testuser",
        "password": "TestPass123!"
    }

    response = client.post("/api/auth/login", data=login_data)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "expires_in" in data


def test_login_wrong_password(client, test_user):
    login_data = {
        "username": "testuser",
        "password": "WrongPass123!"
    }

    response = client.post("/api/auth/login", data=login_data)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Қате пайдаланушы аты немесе пароль" in response.json()["detail"]


def test_get_current_user(client, test_user):

    login_data = {
        "username": "testuser",
        "password": "TestPass123!"
    }

    login_response = client.post("/api/auth/login", data=login_data)
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]