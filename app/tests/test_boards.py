# tests/test_boards.py
import pytest
from fastapi import status


class TestBoards:
    """Test board operations"""
    
    def test_create_board(self, client, auth_headers, test_project):
        """Test creating a board"""
        project_id = test_project["id"]
        response = client.post(
            f"/projects/{project_id}/boards",
            json={"name": "Sprint Backlog"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Sprint Backlog"
        assert data["position"] == 0
        assert data["archived"] == False
    
    def test_list_boards(self, client, auth_headers, test_project, test_board):
        """Test listing boards"""
        project_id = test_project["id"]
        response = client.get(
            f"/projects/{project_id}/boards",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1

    def test_get_board_by_id(self, client, auth_headers, test_project, test_board):
        """Test getting a specific project"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == board_id
        assert data["name"] == "To Do"
    
    def test_list_boards_pagination(self, client, auth_headers, test_project):
        """Test board pagination"""
        project_id = test_project["id"]
        
        # Create 5 boards
        for i in range(5):
            client.post(
                f"/projects/{project_id}/boards",
                json={"name": f"Board {i}"},
                headers=auth_headers
            )
        
        # Get with pagination
        response = client.get(
            f"/projects/{project_id}/boards?page=1&page_size=2",
            headers=auth_headers
        )
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
    
    def test_update_board(self, client, auth_headers, test_project, test_board):
        """Test updating a board"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}",
            json={"name": "Updated Board", "archived": True},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated Board"
        assert data["archived"] == True
    
    def test_delete_board(self, client, auth_headers, test_project, test_board):
        """Test deleting a board"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        response = client.delete(
            f"/projects/{project_id}/boards/{board_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT