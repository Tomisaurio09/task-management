# tests/test_auth.py
import pytest
from fastapi import status


class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_user_success(self, client):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123",
                "full_name": "New User"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "password" not in data
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registration with existing email fails"""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "Pass__123",
                "full_name": "Duplicate User"
            }
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"].lower()
    
    def test_register_invalid_password(self, client):
        """Test registration with weak password fails"""
        response = client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "weak",  # Too short and no numbers
                "full_name": "Test User"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email fails"""
        response = client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "ValidPass123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_success(self, client, test_user):
        """Test successful login"""
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "TestPass123"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails"""
        response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "WrongPass"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email fails"""
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent@example.com", "password": "Pass123"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestTokenRefresh:
    """Test token refresh endpoint"""
    
    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh"""
        # Login first
        login_response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "TestPass123"}
        )
        

        refresh_token = login_response.json()["refresh_token"]
        
        # Refresh
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_refresh_invalid_token(self, client):
        """Test refresh with invalid token fails"""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestUserLogout:
    """Test user logout endpoint"""
    
    def test_logout_success(self, client, test_user):
        """Test successful logout"""
        # Login first
        login_response = client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "TestPass123"}
        )
        access_token = login_response.json()["access_token"]
        
        # Logout
        response = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_requires_token_body(self, client):
        response = client.post("/auth/logout")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

  
