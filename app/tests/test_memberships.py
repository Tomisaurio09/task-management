# app/tests/test_memberships.py
import pytest
from fastapi import status
from app.models.membership import UserRole


class TestAddMember:
    """Test adding members to projects"""
    
    def test_add_member_as_owner(self, client, auth_headers, test_project, test_user_mem):
        """Test OWNER can add members"""
        project_id = test_project["id"]
        user_id = test_user_mem.id
        
        response = client.post(
            f"/projects/{project_id}/members/add/{user_id}",
            json={"role": "EDITOR"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == str(user_id)
        assert data["role"] == "EDITOR"
    
    def test_add_member_duplicate(self, client, auth_headers, test_project, test_user_mem):
        """Test adding same member twice fails"""
        project_id = test_project["id"]
        user_id = test_user_mem.id
        
        # Add first time
        client.post(
            f"/projects/{project_id}/members/add/{user_id}",
            json={"role": "VIEWER"},
            headers=auth_headers
        )
        
        # Try to add again
        response = client.post(
            f"/projects/{project_id}/members/add/{user_id}",
            json={"role": "EDITOR"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already a member" in response.json()["detail"].lower()
    
    def test_add_member_different_roles(self, client, auth_headers, test_project, db_session):
        """Test adding members with different roles"""
        from app.models.user import User
        from app.core.security import hash_password
        import uuid
        
        project_id = test_project["id"]
        
        # Create test users
        viewer = User(
            id=uuid.uuid4(),
            email="viewer@example.com",
            password=hash_password("Pass123"),
            full_name="Viewer User"
        )
        editor = User(
            id=uuid.uuid4(),
            email="editor@example.com",
            password=hash_password("Pass123"),
            full_name="Editor User"
        )
        db_session.add_all([viewer, editor])
        db_session.commit()
        
        # Add as VIEWER
        response = client.post(
            f"/projects/{project_id}/members/add/{viewer.id}",
            json={"role": "VIEWER"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["role"] == "VIEWER"
        
        # Add as EDITOR
        response = client.post(
            f"/projects/{project_id}/members/add/{editor.id}",
            json={"role": "EDITOR"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["role"] == "EDITOR"


class TestRemoveMember:
    """Test removing members from projects"""
    
    def test_remove_member_success(self, client, auth_headers, test_project, test_user_mem):
        """Test removing a member"""
        project_id = test_project["id"]
        user_id = test_user_mem.id
        
        # Add member first
        client.post(
            f"/projects/{project_id}/members/add/{user_id}",
            json={"role": "VIEWER"},
            headers=auth_headers
        )
        
        # Remove member
        response = client.delete(
            f"/projects/{project_id}/members/remove/{user_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT
    
    def test_remove_nonexistent_member(self, client, auth_headers, test_project):
        """Test removing non-existent member fails"""
        project_id = test_project["id"]
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.delete(
            f"/projects/{project_id}/members/remove/{fake_uuid}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_remove_last_owner_fails(self, client, auth_headers, test_project, test_user):
        """Test removing last owner fails"""
        project_id = test_project["id"]
        user_id = test_user.id
        
        # Try to remove the only owner (test_user)
        response = client.delete(
            f"/projects/{project_id}/members/remove/{user_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "last owner" in response.json()["detail"].lower()
    
    def test_remove_owner_when_multiple_owners(self, client, auth_headers, test_project, test_user_mem, test_user):
        """Test removing an owner when there are multiple owners"""
        project_id = test_project["id"]
        
        # Add another owner
        client.post(
            f"/projects/{project_id}/members/add/{test_user_mem.id}",
            json={"role": "OWNER"},
            headers=auth_headers
        )
        
        # Now we can remove the first owner
        response = client.delete(
            f"/projects/{project_id}/members/remove/{test_user.id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestChangeRole:
    """Test changing member roles"""
    
    def test_change_role_success(self, client, auth_headers, test_project, test_user_mem):
        """Test changing a member's role"""
        project_id = test_project["id"]
        user_id = test_user_mem.id
        
        # Add member as VIEWER
        client.post(
            f"/projects/{project_id}/members/add/{user_id}",
            json={"role": "VIEWER"},
            headers=auth_headers
        )
        
        # Change to EDITOR
        response = client.patch(
            f"/projects/{project_id}/members/change-role/{user_id}",
            json={"role": "EDITOR"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["role"] == "EDITOR"
    
    def test_change_to_same_role(self, client, auth_headers, test_project, test_user_mem):
        """Test changing to the same role fails"""
        project_id = test_project["id"]
        user_id = test_user_mem.id
        
        # Add member as VIEWER
        client.post(
            f"/projects/{project_id}/members/add/{user_id}",
            json={"role": "VIEWER"},
            headers=auth_headers
        )
        
        # Try to change to same role
        response = client.patch(
            f"/projects/{project_id}/members/change-role/{user_id}",
            json={"role": "VIEWER"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
        assert "already has role" in response.json()["detail"].lower()
    
    def test_change_role_nonexistent_member(self, client, auth_headers, test_project):
        """Test changing role of non-existent member"""
        project_id = test_project["id"]
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        response = client.patch(
            f"/projects/{project_id}/members/change-role/{fake_uuid}",
            json={"role": "EDITOR"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_change_role_viewer_to_owner(self, client, auth_headers, test_project, test_user_mem):
        """Test promoting VIEWER to OWNER"""
        project_id = test_project["id"]
        user_id = test_user_mem.id
        
        # Add as VIEWER
        client.post(
            f"/projects/{project_id}/members/add/{user_id}",
            json={"role": "VIEWER"},
            headers=auth_headers
        )
        
        # Promote to OWNER
        response = client.patch(
            f"/projects/{project_id}/members/change-role/{user_id}",
            json={"role": "OWNER"},
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "OWNER"


class TestListMembers:
    """Test listing project members"""
    
    def test_list_members_single_owner(self, client, auth_headers, test_project):
        """Test listing members with only owner"""
        project_id = test_project["id"]
        
        response = client.get(
            f"/projects/{project_id}/members",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["role"] == "OWNER"
    
    def test_list_members_multiple(self, client, auth_headers, test_project, db_session):
        """Test listing multiple members"""
        from app.models.user import User
        from app.core.security import hash_password
        import uuid
        
        project_id = test_project["id"]
        
        # Create and add multiple users
        users = []
        for i in range(3):
            user = User(
                id=uuid.uuid4(),
                email=f"member{i}@example.com",
                password=hash_password("Pass123"),
                full_name=f"Member {i}"
            )
            users.append(user)
        
        db_session.add_all(users)
        db_session.commit()
        
        # Add them to project
        roles = ["VIEWER", "EDITOR", "OWNER"]
        for user, role in zip(users, roles):
            client.post(
                f"/projects/{project_id}/members/add/{user.id}",
                json={"role": role},
                headers=auth_headers
            )
        
        # List all members
        response = client.get(
            f"/projects/{project_id}/members",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 4  # 3 added + 1 original owner


class TestMembershipPermissions:
    """Test permission checks for membership operations"""
    
    def test_editor_cannot_add_members(self, client, test_project, test_user_mem, db_session):
        """Test EDITOR cannot add members"""
        from app.models.user import User
        from app.core.security import hash_password
        import uuid
        
        project_id = test_project["id"]
        
        # Create editor user
        editor = User(
            id=uuid.uuid4(),
            email="editor@example.com",
            password=hash_password("EditorPass123"),
            full_name="Editor User"
        )
        db_session.add(editor)
        db_session.commit()
        
        # Add editor to project
        from app.models.membership import Membership, UserRole
        membership = Membership(
            user_id=editor.id,
            project_id=uuid.UUID(str(project_id)),
            role=UserRole.EDITOR
        )
        db_session.add(membership)
        db_session.commit()
        
        # Login as editor
        response = client.post(
            "/auth/login",
            data={"username": "editor@example.com", "password": "EditorPass123"}
        )
        editor_token = response.json()["access_token"]
        editor_headers = {"Authorization": f"Bearer {editor_token}"}
        
        # Try to add member
        response = client.post(
            f"/projects/{project_id}/members/add/{test_user_mem.id}",
            json={"role": "VIEWER"},
            headers=editor_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_viewer_cannot_change_roles(self, client, test_project, test_user_mem, db_session):
        """Test VIEWER cannot change roles"""
        from app.models.user import User
        from app.core.security import hash_password
        import uuid
        
        project_id = test_project["id"]
        
        # Create viewer user
        viewer = User(
            id=uuid.uuid4(),
            email="viewer@example.com",
            password=hash_password("ViewerPass123"),
            full_name="Viewer User"
        )
        db_session.add(viewer)
        db_session.commit()
        
        # Add viewer to project
        from app.models.membership import Membership, UserRole
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
        viewer_token = response.json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}
        
        # Try to change role
        response = client.patch(
            f"/projects/{project_id}/members/change-role/{test_user_mem.id}",
            json={"role": "EDITOR"},
            headers=viewer_headers
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN