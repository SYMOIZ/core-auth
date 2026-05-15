import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    response = await client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["is_active"] is True
    assert data["is_superuser"] is False
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data
    assert "hashed_password" not in data
    print("PASS: test_register_user")


@pytest.mark.asyncio
async def test_login_user(client, registered_user):
    response = await client.post("/auth/login", data={
        "username": "testuser@example.com",
        "password": "TestPassword123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    print("PASS: test_login_user")


@pytest.mark.asyncio
async def test_access_protected_route(client, auth_tokens):
    token = auth_tokens["access_token"]
    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["is_active"] is True
    print("PASS: test_access_protected_route")


@pytest.mark.asyncio
async def test_refresh_token(client, auth_tokens):
    response = await client.post("/auth/refresh", json={
        "refresh_token": auth_tokens["refresh_token"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    print("PASS: test_refresh_token")


@pytest.mark.asyncio
async def test_logout(client, auth_tokens):
    response = await client.post("/auth/logout", json={
        "refresh_token": auth_tokens["access_token"]
    })
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Successfully logged out"
    print("PASS: test_logout")


@pytest.mark.asyncio
async def test_blacklisted_token(client, auth_tokens):
    access_token = auth_tokens["access_token"]

    await client.post("/auth/logout", json={
        "refresh_token": access_token
    })

    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401
    print("PASS: test_blacklisted_token - zero trust verified")
