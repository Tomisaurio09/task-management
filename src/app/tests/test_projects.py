# tests/test_projects.py
import pytest
from fastapi import status


class TestProjectCreation:
    """Test project creation"""
    
    def test_create_project_success(self, client, auth_headers):
        """Test successful project creation"""
        response = client.post(
            "/projects",
            json={"name": "My New Project"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "My New Project"
        assert "id" in data
        assert "owner_id" in data
        assert len(data["memberships"]) == 1
        assert data["memberships"][0]["role"] == "OWNER"
    
    def test_create_project_unauthorized(self, client):
        """Test project creation without auth fails"""
        response = client.post(
            "/projects",
            json={"name": "Unauthorized Project"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_project_empty_name(self, client, auth_headers):
        """Test creating project with empty name fails"""
        response = client.post(
            "/projects",
            json={"name": "   "},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestProjectList:
    """Test listing projects"""
    
    def test_list_projects_empty(self, client, auth_headers):
        """Test listing projects when user has none"""
        response = client.get("/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
    
    def test_list_projects_with_data(self, client, auth_headers, test_project):
        """Test listing projects with data"""
        response = client.get("/projects", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        assert data["items"][0]["name"] == "Test Project"
    
    def test_list_projects_pagination(self, client, auth_headers):
        """Test project pagination"""
        # Create multiple projects
        for i in range(5):
            client.post(
                "/projects",
                json={"name": f"Project {i}"},
                headers=auth_headers
            )
        
        # Get first page with 2 items
        response = client.get(
            "/projects?page=1&page_size=2",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert data["total"] == 5
        assert data["has_next"] == True
        assert data["has_previous"] == False
    
    def test_list_projects_sorting(self, client, auth_headers):
        """Test project sorting"""
        # Create projects with different names
        client.post("/projects", json={"name": "Zebra"}, headers=auth_headers)
        client.post("/projects", json={"name": "Apple"}, headers=auth_headers)
        
        # Sort ascending
        response = client.get(
            "/projects?sort_by=name&sort_order=asc",
            headers=auth_headers
        )
        data = response.json()
        assert data["items"][0]["name"] == "Apple"
        
        # Sort descending
        response = client.get(
            "/projects?sort_by=name&sort_order=desc",
            headers=auth_headers
        )
        data = response.json()
        assert data["items"][0]["name"] == "Zebra"
    
    def test_list_projects_filter_by_name(self, client, auth_headers):
        """Test filtering projects by name"""
        client.post("/projects", json={"name": "Backend API"}, headers=auth_headers)
        client.post("/projects", json={"name": "Frontend App"}, headers=auth_headers)
        
        response = client.get(
            "/projects?name=backend",
            headers=auth_headers
        )
        data = response.json()
        assert data["total"] == 1
        assert "backend" in data["items"][0]["name"].lower()


class TestProjectOperations:
    """Test project CRUD operations"""
    
    def test_get_project_by_id(self, client, auth_headers, test_project):
        """Test getting a specific project"""
        project_id = test_project["id"]
        response = client.get(
            f"/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Test Project"
    
    def test_get_nonexistent_project(self, client, auth_headers):
        """Test getting non-existent project fails"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        response = client.get(
            f"/projects/{fake_uuid}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_project(self, client, auth_headers, test_project):
        """Test updating a project"""
        project_id = test_project["id"]
        response = client.patch(
            f"/projects/{project_id}",
            json={"name": "Updated Project Name"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Project Name"
    
    def test_delete_project(self, client, auth_headers, test_project):
        """Test deleting a project"""
        project_id = test_project["id"]
        response = client.delete(
            f"/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify project is deleted
        response = client.get(
            f"/projects/{project_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestProjectMaxLimit:
    """Test project creation limits"""
    
    def test_max_projects_limit(self, client, auth_headers):
        """Test that users can't create more than 20 projects"""
        # Create 20 projects (max allowed)
        for i in range(20):
            response = client.post(
                "/projects",
                json={"name": f"Project {i}"},
                headers=auth_headers
            )
            assert response.status_code == status.HTTP_201_CREATED
        
        # Try to create 21st project
        response = client.post(
            "/projects",
            json={"name": "Project 21"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert "maximum" in response.json()["detail"].lower()