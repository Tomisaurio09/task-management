# Architecture

## Overview

This project follows **Clean Architecture** principles with a clear separation of responsibilities across layers.

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (Routers)                      │
│  • Receives HTTP requests                                    │
│  • Validates with Pydantic schemas                           │
│  • Handles authentication (dependencies)                     │
│  • Returns HTTP responses                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  • Business logic                                            │
│  • Business validations                                      │
│  • Operation orchestration                                   │
│  • Raises domain exceptions                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer (Models)                       │
│  • SQLAlchemy models                                         │
│  • Database queries                                          │
│  • Entity relationships                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     PostgreSQL Database                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Main Components

### 1. API Layer (`app/api/`)

**Responsibilities**:
- Define endpoints and routing  
- Validate input with Pydantic schemas  
- Apply middlewares (auth, rate limiting)  
- Serialize responses  
- Map domain exceptions to HTTP status codes  

**Must not**:
- Contain business logic  
- Perform direct DB queries  
- Manage transactions  

**Example**:
```python
@router.post("/projects", status_code=201)
def create_project(
    project_data: ProjectCreateSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only orchestrates: validates input, calls service, returns response
    return projects_service.create_project_membership(
        project_details=project_data,
        user_id=current_user["id"],
        db=db
    )
```

---

### 2. Service Layer (`app/services/`)

**Responsibilities**:
- Implement business logic  
- Enforce business rules (e.g., max 20 projects per user)  
- Orchestrate complex operations  
- Manage transactions  
- Raise domain exceptions  

**Must not**:
- Know HTTP details (status codes, headers)  
- Depend on FastAPI  
- Access request/response directly  

**Example**:
```python
def create_project_membership(
    project_details: ProjectCreateSchema,
    user_id: UUID,
    db: Session
) -> Project:
    # Business validation
    projects_count = db.query(Project).join(Membership).filter(
        Membership.user_id == user_id
    ).count()
    
    if projects_count >= 20:
        raise ValidationError("Max 20 projects per user")
    
    # Business logic
    new_project = Project(name=project_details.name, owner_id=user_id)
    db.add(new_project)
    db.flush()
    
    # Automatic membership creation
    membership = Membership(
        user_id=user_id,
        project_id=new_project.id,
        role=UserRole.OWNER
    )
    db.add(membership)
    db.commit()
    
    return new_project
```

---

### 3. Data Layer (`app/models/`)

**Responsibilities**:
- Define database schema  
- Manage entity relationships  
- Apply DB-level constraints and validations  

**Example**:
```python
class Project(Base):
    __tablename__ = "projects"
    
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    owner_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("users.id"))
    
    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(
        "Membership",
        back_populates="project",
        cascade="all, delete-orphan"
    )
```

---

## Request Flow

### Example: `POST /projects` (Create project)

```
1. Client
   └─> POST /projects + JWT token + {"name": "My Project"}

2. FastAPI (app/api/projects.py)
   ├─> Rate limiter (checks request limits)
   ├─> OAuth2 dependency (extracts token)
   ├─> get_current_user (validates JWT, gets user_id)
   ├─> Pydantic schema (validates body)
   └─> Calls projects_service.create_project_membership()

3. Service (app/services/projects_service.py)
   ├─> Validates business rules (max 20 projects)
   ├─> Creates Project in DB
   ├─> Creates Membership (OWNER)
   ├─> Commits transaction
   └─> Returns Project

4. FastAPI
   ├─> Serializes with ProjectResponseSchema
   └─> Returns 201 Created + JSON

5. Client
   └─> Receives response
```

---

### Error Handling

```
Service Layer raises:
  ├─> ValidationError("Max 20 projects")
  │
  ▼
Exception Handler (app/core/exceptions_handlers.py)
  ├─> Captures ValidationError
  ├─> Maps to HTTP 422
  └─> Returns {"detail": "Max 20 projects"}
  │
  ▼
Client receives 422 Unprocessable Entity
```

---

## Dependency Injection

### Dependency Pattern

```python
# 1. Database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. Authenticated user
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> dict:
    # Validate JWT
    # Fetch user from DB
    return {"id": user.id, "instance": user}

# 3. Permission validation (factory pattern)
def require_project_roles(allowed_roles: list[UserRole]):
    def dependency(
        project_id: UUID,
        current_user=Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        membership = db.query(Membership).filter(
            Membership.user_id == current_user["id"],
            Membership.project_id == project_id
        ).first()
        
        if not membership:
            raise ResourceNotFoundError("Not a member")
        
        if membership.role not in allowed_roles:
            raise InsufficientPermissionsError("Insufficient permissions")
        
        return membership
    
    return dependency
```

---

## Cross-Cutting Concerns

### 1. Exception Handling
All domain exceptions are converted into HTTP responses:
```python
# Service raises
raise InvalidCredentialsError("Wrong password")

# Handler converts
→ HTTP 401 Unauthorized
→ {"detail": "Wrong password"}
```

### 2. Logging
```python
# In services
logger.info(f"User {user_id} created project {project_id}")
logger.error(f"Failed to create project: {str(e)}", exc_info=True)
```

### 3. Rate Limiting
```python
@router.post("/projects")
@limiter.limit("10/minute")  # Max 10 projects per minute
def create_project(...):
    pass
```

### 4. Pagination
```python
# Applied in services, not routers
def get_projects(..., pagination: PaginationParams):
    query = db.query(Project).filter(...)
    
    # Apply sorting
    query = apply_sorting(query, sort_params, Project, allowed_fields)
    
    # Apply pagination
    return paginate(query, pagination, Project)
```

---

## Performance Considerations

### Indexing
```python
# Composite indexes for common queries
__table_args__ = (
    Index("idx_task_board_position", "board_id", "position"),
    Index("idx_task_status_priority", "status", "priority"),
)
```

### Pagination
```python
# Always paginate lists
# Prevents loading thousands of records into memory
response = paginate(query, page=1, page_size=20)
```

---

## Security Layers

```
1. Network → Rate Limiting (Redis)
2. API → JWT Authentication
3. Endpoint → Role-based permissions
4. Service → Business validations
5. DB → Constraints & foreign keys
```