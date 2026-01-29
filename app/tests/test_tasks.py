# tests/test_tasks.py
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
class TestTasks:
    """Test task operations"""
    
    def test_create_task(self, client, auth_headers, test_project, test_board):
        """Test creating a task"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Implement feature X",
                "description": "Add new authentication flow",
                "priority": "high",
                "status": "active"
            },
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Implement feature X"
        assert data["priority"] == "high"
        assert data["position"] == 0
    
    def test_list_tasks(self, client, auth_headers, test_project, test_board, test_task):
        """Test listing tasks"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
    
    def test_list_tasks_with_filters(self, client, auth_headers, test_project, test_board):
        """Test filtering tasks"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create tasks with different priorities
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "High priority task", "priority": "high"},
            headers=auth_headers
        )
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Low priority task", "priority": "low"},
            headers=auth_headers
        )
        
        # Filter by HIGH priority
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?priority=high",
            headers=auth_headers
        )
        data = response.json()
        assert all(task["priority"] == "high" for task in data["items"])
    
    def test_update_task(self, client, auth_headers, test_project, test_board, test_task):
        """Test updating a task"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        task_id = test_task["id"]
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json={
                "name": "Updated task name",
                "status": "completed"
            },
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "Updated task name"
        assert data["status"] == "completed"
    
    def test_delete_task(self, client, auth_headers, test_project, test_board, test_task):
        """Test deleting a task"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        task_id = test_task["id"]
        
        response = client.delete(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_task_sorting_by_due_date(self, client, auth_headers, test_project, test_board):
        """Test sorting tasks by due date"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create tasks with different due dates
        today = datetime.now(timezone.utc)
        
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Task 1",
                "due_date": (today + timedelta(days=3)).isoformat()
            },
            headers=auth_headers
        )
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Task 2",
                "due_date": (today + timedelta(days=1)).isoformat()
            },
            headers=auth_headers
        )
        
        # Sort by due_date ascending
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?sort_by=due_date&sort_order=asc",
            headers=auth_headers
        )
        data = response.json()
        # First task should have earliest due date
        assert data["items"][0]["name"] == "Task 2"