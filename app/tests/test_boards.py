# tests/test_boards.py

import pytest
from fastapi import status
import time
from app.models.user import User
from app.models.membership import Membership, UserRole
from app.core.security import hash_password
import uuid

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

class TestBoardEdgeCases:
    """Test board edge cases and error handling"""
    
    def test_create_board_empty_name(self, client, auth_headers, test_project):
        """Test creating board with empty name fails"""
        project_id = test_project["id"]
        
        response = client.post(
            f"/projects/{project_id}/boards",
            json={"name": "   "},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_board_long_name(self, client, auth_headers, test_project):
        """Test creating board with name exceeding max length"""
        project_id = test_project["id"]
        long_name = "A" * 129  # Max is 128
        
        response = client.post(
            f"/projects/{project_id}/boards",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_board_position_auto_increment(self, client, auth_headers, test_project):
        """Test that board positions auto-increment"""
        project_id = test_project["id"]
        
        # Create 3 boards
        boards = []
        for i in range(3):
            response = client.post(
                f"/projects/{project_id}/boards",
                json={"name": f"Board {i}"},
                headers=auth_headers
            )
            boards.append(response.json())
        
        # Verify positions
        assert boards[0]["position"] == 0
        assert boards[1]["position"] == 1
        assert boards[2]["position"] == 2
    
    def test_update_board_negative_position(self, client, auth_headers, test_project, test_board):
        """Test updating board with negative position fails"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}",
            json={"position": -1},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_update_board_empty_name(self, client, auth_headers, test_project, test_board):
        """Test updating board with empty name fails"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}",
            json={"name": ""},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_get_nonexistent_board(self, client, auth_headers, test_project):
        """Test getting non-existent board"""
        project_id = test_project["id"]
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/projects/{project_id}/boards/{fake_uuid}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_board_cascades_tasks(self, client, auth_headers, test_project, test_board):
        """Test deleting board also deletes its tasks"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create a task in the board
        task_response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Task to be deleted"},
            headers=auth_headers
        )
        task_id = task_response.json()["id"]
        
        # Delete board
        response = client.delete(
            f"/projects/{project_id}/boards/{board_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify task is also deleted (board doesn't exist anymore)
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestBoardFiltering:
    """Test board filtering functionality"""
    
    def test_filter_by_name(self, client, auth_headers, test_project):
        """Test filtering boards by name"""
        project_id = test_project["id"]
        
        # Create boards
        client.post(f"/projects/{project_id}/boards", json={"name": "Backend Tasks"}, headers=auth_headers)
        client.post(f"/projects/{project_id}/boards", json={"name": "Frontend Tasks"}, headers=auth_headers)
        client.post(f"/projects/{project_id}/boards", json={"name": "DevOps"}, headers=auth_headers)
        
        # Filter by name
        response = client.get(
            f"/projects/{project_id}/boards?name=backend",
            headers=auth_headers
        )
        data = response.json()
        assert data["total"] == 1
        assert "backend" in data["items"][0]["name"].lower()
    
    def test_include_archived_boards(self, client, auth_headers, test_project):
        """Test including archived boards in results"""
        project_id = test_project["id"]
        
        # Create and archive a board
        response = client.post(
            f"/projects/{project_id}/boards",
            json={"name": "Archived Board"},
            headers=auth_headers
        )
        board_id = response.json()["id"]
        
        client.patch(
            f"/projects/{project_id}/boards/{board_id}",
            json={"archived": True},
            headers=auth_headers
        )
        
        # Default: exclude archived
        response = client.get(
            f"/projects/{project_id}/boards",
            headers=auth_headers
        )
        assert all(not board["archived"] for board in response.json()["items"])
        
        # Include archived
        response = client.get(
            f"/projects/{project_id}/boards?archived=true",
            headers=auth_headers
        )
        archived_boards = [b for b in response.json()["items"] if b["archived"]]
        assert len(archived_boards) >= 1


class TestBoardSorting:
    """Test board sorting functionality"""
    
    def test_sort_by_name(self, client, auth_headers, test_project):
        """Test sorting boards by name"""
        project_id = test_project["id"]
        
        # Create boards
        client.post(f"/projects/{project_id}/boards", json={"name": "Zebra"}, headers=auth_headers)
        client.post(f"/projects/{project_id}/boards", json={"name": "Apple"}, headers=auth_headers)
        client.post(f"/projects/{project_id}/boards", json={"name": "Mango"}, headers=auth_headers)
        
        # Sort ascending
        response = client.get(
            f"/projects/{project_id}/boards?sort_by=name&sort_order=asc",
            headers=auth_headers
        )
        items = response.json()["items"]
        names = [item["name"] for item in items]
        assert names == sorted(names)
        
        # Sort descending
        response = client.get(
            f"/projects/{project_id}/boards?sort_by=name&sort_order=desc",
            headers=auth_headers
        )
        items = response.json()["items"]
        names = [item["name"] for item in items]
        assert names == sorted(names, reverse=True)
    
    def test_sort_by_position(self, client, auth_headers, test_project):
        """Test sorting boards by position"""
        project_id = test_project["id"]
        
        # Create boards (they'll have positions 0, 1, 2)
        for i in range(3):
            client.post(
                f"/projects/{project_id}/boards",
                json={"name": f"Board {i}"},
                headers=auth_headers
            )
        
        # Default sort is by position ascending
        response = client.get(
            f"/projects/{project_id}/boards",
            headers=auth_headers
        )
        items = response.json()["items"]
        positions = [item["position"] for item in items]
        assert positions == sorted(positions)
    
    def test_sort_by_created_at(self, client, auth_headers, test_project):
        """Test sorting boards by creation date"""
        project_id = test_project["id"]
        
        # Create boards
        for i in range(3):
            client.post(
                f"/projects/{project_id}/boards",
                json={"name": f"Board {i}"},
                headers=auth_headers
            )
            time.sleep(0.01)
        
        # Sort by created_at desc (newest first)
        response = client.get(
            f"/projects/{project_id}/boards?sort_by=created_at&sort_order=desc",
            headers=auth_headers
        )
        items = response.json()["items"]
        created_times = [item["created_at"] for item in items]
        assert created_times == sorted(created_times, reverse=True)




class TestBoardPermissions:
    """Test board permissions based on user roles"""
    
    def test_viewer_can_read_boards(self, client, test_project, db_session):
        """Test VIEWER can read boards"""
        
        project_id = test_project["id"]
        
        # Create viewer
        viewer = User(
            id=uuid.uuid4(),
            email="viewer@example.com",
            password=hash_password("ViewerPass123"),
            full_name="Viewer"
        )
        db_session.add(viewer)
        db_session.commit()
        
        # Add to project as VIEWER
        membership = Membership(
            user_id=viewer.id,
            project_id=uuid.UUID(str(project_id)),
            role=UserRole.VIEWER
        )
        db_session.add(membership)
        db_session.commit()
        
        # Login as viewer
        response = client.post(
            "/auth/login",
            data={"username": "viewer@example.com", "password": "ViewerPass123"}
        )
        viewer_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # Can read boards
        response = client.get(
            f"/projects/{project_id}/boards",
            headers=viewer_headers
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_viewer_cannot_create_boards(self, client, test_project, db_session):
        """Test VIEWER cannot create boards"""
        project_id = test_project["id"]
        
        # Create viewer
        viewer = User(
            id=uuid.uuid4(),
            email="viewer2@example.com",
            password=hash_password("ViewerPass123"),
            full_name="Viewer"
        )
        db_session.add(viewer)
        db_session.commit()
        
        # Add to project as VIEWER
        membership = Membership(
            user_id=viewer.id,
            project_id=uuid.UUID(str(project_id)),
            role=UserRole.VIEWER
        )
        db_session.add(membership)
        db_session.commit()
        
        # Login as viewer
        response = client.post(
            "/auth/login",
            data={"username": "viewer2@example.com", "password": "ViewerPass123"}
        )
        viewer_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
        
        # Cannot create boards
        response = client.post(
            f"/projects/{project_id}/boards",
            json={"name": "New Board"},
            headers=viewer_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN