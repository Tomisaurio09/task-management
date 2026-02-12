# Role-Based Access Control (RBAC)

## Overview

This project implements **RBAC** at the project level. Each user can have different roles across different projects.

## Roles

```python
class UserRole(Enum):
    OWNER = "OWNER"      # Full control
    EDITOR = "EDITOR"    # Can edit, but not manage members
    VIEWER = "VIEWER"    # Read-only
```

### Role Hierarchy

```
OWNER (Admin)
  ├─ Can do EVERYTHING
  ├─ Add/remove members
  ├─ Change roles
  ├─ Delete project
  └─ Full CRUD
      │
      ▼
EDITOR (Contributor)
  ├─ CRUD for boards and tasks
  ├─ View members
  ├─ ❌ Cannot manage members
  └─ ❌ Cannot delete project
      │
      ▼
VIEWER (Read-only)
  ├─ View projects, boards, tasks
  ├─ View members
  └─ ❌ Cannot create/edit/delete
```

---

## Permission Matrix

| Action | OWNER | EDITOR | VIEWER |
|--------|-------|--------|--------|
| **Projects** | | | |
| View project | ✅ | ✅ | ✅ |
| Create project | ✅ | ✅ | ✅ |
| Edit project | ✅ | ✅ | ❌ |
| Delete project | ✅ | ❌ | ❌ |
| **Memberships** | | | |
| View members | ✅ | ✅ | ✅ |
| Add members | ✅ | ❌ | ❌ |
| Remove members | ✅ | ❌ | ❌ |
| Change roles | ✅ | ❌ | ❌ |
| **Boards** | | | |
| View boards | ✅ | ✅ | ✅ |
| Create boards | ✅ | ✅ | ❌ |
| Edit boards | ✅ | ✅ | ❌ |
| Delete boards | ✅ | ✅ | ❌ |
| **Tasks** | | | |
| View tasks | ✅ | ✅ | ✅ |
| Create tasks | ✅ | ✅ | ❌ |
| Edit tasks | ✅ | ✅ | ❌ |
| Delete tasks | ✅ | ✅ | ❌ |
| Assign tasks | ✅ | ✅ | ❌ |

---

## Implementation

### 1. Membership Model

```python
# app/models/membership.py
class Membership(Base):
    __tablename__ = "memberships"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id"))
    project_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("projects.id"))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now(timezone.utc))
    invited_by: Mapped[UUID | None] = mapped_column(UUID, ForeignKey("users.id"), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("user_id", "project_id", name="uq_membership_user_project"),
    )
```

**Business Rules**:
- A user can have **only one role per project**  
- The project creator is automatically **OWNER**  
- There must always be **at least one OWNER** per project  

---

### 2. Permission Dependency (Factory Pattern)

```python
# app/core/dependencies.py
def require_project_roles(allowed_roles: list[UserRole]):
    """
    Factory that creates a dependency to validate roles.
    
    Usage:
        @router.get("/projects/{project_id}")
        def endpoint(
            membership=Depends(require_project_roles([UserRole.OWNER, UserRole.VIEWER]))
        ):
            # membership contains the current user's Membership
            pass
    """
    def dependency(
        project_id: UUID,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # 1. Find membership
        membership = db.query(Membership).filter(
            Membership.user_id == current_user["id"],
            Membership.project_id == project_id
        ).first()
        
        # 2. Verify membership
        if not membership:
            raise ResourceNotFoundError("You are not a member of this project")
        
        # 3. Verify role
        if membership.role not in allowed_roles:
            raise InsufficientPermissionsError(
                f"You need one of these roles: {[r.value for r in allowed_roles]}"
            )
        
        return membership
    
    return dependency
```

---

### 3. Usage in Endpoints

#### Example 1: Only OWNER can add members

```python
@router.post("/projects/{project_id}/members/add/{user_id}")
def add_member(
    project_id: UUID,
    user_id: UUID,
    body: AddMemberSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))  # ← Enforcement
):
    return membership_service.add_member(
        project_id, user_id, body.role, current_user["id"], db
    )
```

**Flow**:
```
1. User makes request
2. get_current_user → extracts user_id from JWT
3. require_project_roles → verifies membership and role
   ├─ If not a member → 404 Not Found
   └─ If not OWNER → 403 Forbidden
4. If valid → executes endpoint
```

#### Example 2: OWNER and EDITOR can create boards

```python
@router.post("/projects/{project_id}/boards")
def create_board(
    project_id: UUID,
    board_data: BoardCreateSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    return board_service.create_board(project_id, board_data, db)
```

#### Example 3: Everyone can view

```python
@router.get("/projects/{project_id}")
def get_project(
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    return projects_service.get_project_by_id(project_id, db)
```

---

## Business Rules

### Rule 1: Project must always have at least one OWNER

```python
def remove_member(project_id: UUID, user_id: UUID, db: Session):
    member = db.query(Membership).filter_by(
        user_id=user_id,
        project_id=project_id
    ).first()
    
    if not member:
        raise ResourceNotFoundError("Member not found")
    
    if member.role == UserRole.OWNER:
        owners_count = db.query(Membership).filter_by(
            project_id=project_id,
            role=UserRole.OWNER
        ).count()
        
        if owners_count <= 1:
            raise LastOwnerError("Cannot remove the last owner of the project")
    
    db.delete(member)
    db.commit()
```

---

### Rule 2: Cannot change to the same role

```python
def change_member_role(project_id: UUID, user_id: UUID, new_role: UserRole, db: Session):
    member = db.query(Membership).filter_by(...).first()
    
    if not member:
        raise ResourceNotFoundError("Member not found")
    
    if member.role == new_role:
        raise ValidationError(f"Member already has role {new_role.value}")
    
    member.role = new_role
    db.commit()
```

---

### Rule 3: Only OWNER can invite

```python
def add_member(project_id: UUID, user_id: UUID, role: UserRole, invited_by: UUID, db: Session):
    # Validation that invited_by is OWNER is enforced at the endpoint
    # via require_project_roles([UserRole.OWNER])
    
    existing = db.query(Membership).filter_by(
        user_id=user_id,
        project_id=project_id
    ).first()
    
    if existing:
        raise MemberAlreadyExistsError("User is already a member")
    
    new_member = Membership(
        user_id=user_id,
        project_id=project_id,
        role=role,
        invited_by=invited_by
    )
    db.add(new_member)
    db.commit()
```

---

## HTTP Status Codes

| Situation | Status Code | Exception |
|-----------|-------------|-----------|
| Not authenticated | 401 Unauthorized | - |
| Not a member | 404 Not Found | ResourceNotFoundError |
| Insufficient role | 403 Forbidden | InsufficientPermissionsError |
| Success | 200/201/204 | - |

---

## Edge Cases

### Case 1: User removed from project
```python
db.delete(membership)
db.commit()

# Next request
GET /projects/{id}
# → 404 Not Found (no longer a member)
```

### Case 2: Role downgraded
```python
membership.role = UserRole.VIEWER
db.commit()

POST /projects/{id}/boards
# → 403 Forbidden
```

### Case 3: Multiple OWNERS
```python
# Project with 3 OWNERS
remove_member(project_id, owner1.id, db)  # → OK (2 left)
remove_member(project_id, owner2.id, db)  # → OK (1 left)
remove_member(project_id, owner3.id, db)  # → 400 Bad Request (last owner)
```
