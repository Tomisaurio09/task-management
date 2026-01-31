# tests/test_tasks.py
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone
import uuid
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
    
# app/tests/test_tasks_extended.py
import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone


class TestTaskValidations:
    """Test task validation rules"""
    
    def test_create_task_empty_name(self, client, auth_headers, test_project, test_board):
        """Test creating task with empty name fails"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "   "},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_task_long_name(self, client, auth_headers, test_project, test_board):
        """Test creating task with name exceeding max length"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        long_name = "A" * 257  # Max is 256
        
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": long_name},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_task_long_description(self, client, auth_headers, test_project, test_board):
        """Test creating task with description exceeding max length"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        long_description = "A" * 513  # Max is 512
        
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Valid Task",
                "description": long_description
            },
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_create_task_past_due_date(self, client, auth_headers, test_project, test_board):
        """Test creating task with past due date fails"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Task",
                "due_date": past_date
            },
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    
    def test_update_task_past_due_date(self, client, auth_headers, test_project, test_board, test_task):
        """Test updating task with past due date fails"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        task_id = test_task["id"]
        past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json={"due_date": past_date},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestTaskAssignee:
    """Test task assignee validation"""
    
    def test_assign_task_to_project_member(self, client, auth_headers, test_project, test_board, test_user_mem, db_session):
        """Test assigning task to project member"""
        from app.models.membership import Membership, UserRole
        
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Add user to project
        membership = Membership(
            user_id=test_user_mem.id,
            project_id=uuid.UUID(str(project_id)),
            role=UserRole.EDITOR
        )
        db_session.add(membership)
        db_session.commit()
        
        # Assign task
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Assigned Task",
                "assignee_id": str(test_user_mem.id)
            },
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["assignee_id"] == str(test_user_mem.id)
    
    def test_assign_task_to_non_member_fails(self, client, auth_headers, test_project, test_board, test_user_mem):
        """Test assigning task to non-project member fails"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Try to assign to user not in project
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Task",
                "assignee_id": str(test_user_mem.id)
            },
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "member" in response.json()["detail"].lower()
    
    def test_update_assignee_to_non_member_fails(self, client, auth_headers, test_project, test_board, test_task, test_user_mem):
        """Test updating assignee to non-member fails"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        task_id = test_task["id"]
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json={"assignee_id": str(test_user_mem.id)},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_unassign_task(self, client, auth_headers, test_project, test_board, test_user, db_session):
        """Test removing assignee from task"""
        from app.models.membership import Membership, UserRole
        
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create task with assignee
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={
                "name": "Assigned Task",
                "assignee_id": str(test_user.id)
            },
            headers=auth_headers
        )
        task_id = response.json()["id"]
        
        # Remove assignee (set to null)
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json={"assignee_id": None},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["assignee_id"] is None


class TestTaskPositioning:
    """Test task position management"""
    
    def test_task_position_auto_increment(self, client, auth_headers, test_project, test_board):
        """Test task positions auto-increment"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        tasks = []
        for i in range(3):
            response = client.post(
                f"/projects/{project_id}/boards/{board_id}/tasks",
                json={"name": f"Task {i}"},
                headers=auth_headers
            )
            tasks.append(response.json())
        
        assert tasks[0]["position"] == 0
        assert tasks[1]["position"] == 1
        assert tasks[2]["position"] == 2
    
    def test_reorder_tasks(self, client, auth_headers, test_project, test_board, test_task):
        """Test reordering tasks by changing position"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        task_id = test_task["id"]
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json={"position": 5},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["position"] == 5


class TestTaskFiltering:
    """Test task filtering"""
    
    def test_filter_by_status(self, client, auth_headers, test_project, test_board):
        """Test filtering tasks by status"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create tasks with different statuses
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Active Task", "status": "active"},
            headers=auth_headers
        )
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Completed Task", "status": "completed"},
            headers=auth_headers
        )
        
        # Filter by ACTIVE
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?status=active",
            headers=auth_headers
        )
        items = response.json()["items"]
        assert all(task["status"] == "active" for task in items)
        
        # Filter by COMPLETED
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?status=completed",
            headers=auth_headers
        )
        items = response.json()["items"]
        assert all(task["status"] == "completed" for task in items)
    
    def test_filter_by_priority(self, client, auth_headers, test_project, test_board):
        """Test filtering tasks by priority"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create tasks with different priorities
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "High Priority", "priority": "high"},
            headers=auth_headers
        )
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Low Priority", "priority": "low"},
            headers=auth_headers
        )
        
        # Filter by HIGH
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?priority=high",
            headers=auth_headers
        )
        items = response.json()["items"]
        assert all(task["priority"] == "high" for task in items)
    
    def test_filter_by_assignee(self, client, auth_headers, test_project, test_board, test_user, db_session):
        """Test filtering tasks by assignee"""
        from app.models.user import User
        from app.models.membership import Membership, UserRole
        from app.core.security import hash_password
        import uuid
        
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create another user
        user2 = User(
            id=uuid.uuid4(),
            email="user2@example.com",
            password=hash_password("Pass123"),
            full_name="User 2"
        )
        db_session.add(user2)
        db_session.commit()
        
        # Add to project
        membership = Membership(
            user_id=user2.id,
            project_id=uuid.UUID(str(project_id)),
            role=UserRole.EDITOR
        )
        db_session.add(membership)
        db_session.commit()
        
        # Create tasks assigned to different users
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Task 1", "assignee_id": str(test_user.id)},
            headers=auth_headers
        )
        client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Task 2", "assignee_id": str(user2.id)},
            headers=auth_headers
        )
        
        # Filter by test_user
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?assignee_id={test_user.id}",
            headers=auth_headers
        )
        items = response.json()["items"]
        assert all(task["assignee_id"] == str(test_user.id) for task in items)
    
    def test_filter_archived_tasks(self, client, auth_headers, test_project, test_board):
        """Test filtering archived tasks"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        
        # Create and archive a task
        response = client.post(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            json={"name": "Archived Task"},
            headers=auth_headers
        )
        task_id = response.json()["id"]
        
        client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json={"archived": True},
            headers=auth_headers
        )
        
        # Default: exclude archived
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks",
            headers=auth_headers
        )
        assert all(not task["archived"] for task in response.json()["items"])
        
        # Include archived
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks?archived=true",
            headers=auth_headers
        )
        archived_tasks = [t for t in response.json()["items"] if t["archived"]]
        assert len(archived_tasks) >= 1


class TestTaskMovement:
    """Test moving tasks between boards"""
    
    def test_move_task_to_another_board(self, client, auth_headers, test_project, test_board, test_task):
        """Test moving task to another board in same project"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        task_id = test_task["id"]
        
        # Create another board
        response = client.post(
            f"/projects/{project_id}/boards",
            json={"name": "New Board"},
            headers=auth_headers
        )
        new_board_id = response.json()["id"]
        
        # Move task
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{task_id}",
            json={"board_id": new_board_id},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["board_id"] == new_board_id


class TestTaskEdgeCases:
    """Test task edge cases"""
    
    def test_get_nonexistent_task(self, client, auth_headers, test_project, test_board):
        """Test getting non-existent task"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.get(
            f"/projects/{project_id}/boards/{board_id}/tasks/{fake_uuid}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_update_nonexistent_task(self, client, auth_headers, test_project, test_board):
        """Test updating non-existent task"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.patch(
            f"/projects/{project_id}/boards/{board_id}/tasks/{fake_uuid}",
            json={"name": "Updated"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_nonexistent_task(self, client, auth_headers, test_project, test_board):
        """Test deleting non-existent task"""
        project_id = test_project["id"]
        board_id = test_board["id"]
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.delete(
            f"/projects/{project_id}/boards/{board_id}/tasks/{fake_uuid}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND