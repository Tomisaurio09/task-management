# app/api/projects.py
from uuid import UUID
from fastapi import APIRouter, Depends, status, Body, Query, Request
from sqlalchemy.orm import Session

from app.schemas.project_schema import ProjectCreateSchema, ProjectUpdateSchema, ProjectResponseSchema
from app.schemas.membership_schema import AddMemberSchema, ChangeRoleMemberSchema, MemberResponseSchema
from app.schemas.pagination import PaginationParams, PaginatedResponse, SortParams
from app.core.dependencies import get_db, get_current_user, require_project_roles
from app.core.rate_limit import limiter
from app.models.membership import UserRole
from app.services import project_service, membership_service

router = APIRouter(tags=["projects"])

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ProjectResponseSchema)
@limiter.limit("10/minute")  # Max 10 projects created per minute
def create_project(
    request: Request,
    project_data: ProjectCreateSchema = Body(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new project. Creator becomes OWNER automatically."""
    return project_service.create_project_membership(
        project_details=project_data,
        user_id=current_user["id"],
        db=db,
    )


@router.get("/", response_model=PaginatedResponse[ProjectResponseSchema])
@limiter.limit("60/minute")
def get_projects(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    # Pagination
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    # Sorting
    sort_by: str | None = Query(None, description="Sort by: name, created_at"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    # Filters
    name: str | None = Query(None, description="Filter by project name (case-insensitive)")
):
    """List all projects where user is a member (paginated, sortable, filterable)."""
    pagination = PaginationParams(page=page, page_size=page_size)
    sort_params = SortParams(sort_by=sort_by, sort_order=sort_order)
    
    return project_service.get_projects(
        user_id=current_user["id"],
        pagination=pagination,
        sort_params=sort_params,
        name_filter=name,
        db=db
    )


@router.get("/{project_id}", response_model=ProjectResponseSchema)
@limiter.limit("120/minute")
def get_project(
    request: Request,
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """Get a specific project."""
    return project_service.get_project_by_id(project_id, db)


@router.patch("/{project_id}", response_model=ProjectResponseSchema)
@limiter.limit("30/minute")
def update_project(
    request: Request,
    project_id: UUID,
    project_data: ProjectUpdateSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR]))
):
    """Update project name."""
    return project_service.update_project(project_id, project_data, db)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
def delete_project(
    request: Request,
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
):
    """Delete project (only OWNER)."""
    project_service.delete_project(project_id, db)


# --- Membership endpoints ---

@router.get("/{project_id}/members", response_model=list[MemberResponseSchema])
@limiter.limit("60/minute")
def list_members(
    request: Request,
    project_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER, UserRole.EDITOR, UserRole.VIEWER]))
):
    """List all project members."""
    return project_service.get_project_members(project_id, db)


@router.post("/{project_id}/members/add/{user_id}", status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def add_member(
    request: Request,
    project_id: UUID,
    user_id: UUID,
    body: AddMemberSchema,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
):
    """Add a member to the project (only OWNER)."""
    return membership_service.add_member(
        project_id, user_id, body.role, current_user["id"], db
    )


@router.delete("/{project_id}/members/remove/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
def remove_member(
    request: Request,
    project_id: UUID,
    user_id: UUID,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
):
    """Remove a member from the project (only OWNER)."""
    membership_service.remove_member(project_id, user_id, db)


@router.patch("/{project_id}/members/change-role/{user_id}")
@limiter.limit("30/minute")
def change_member_role(
    request: Request,
    project_id: UUID,
    user_id: UUID,
    body: ChangeRoleMemberSchema,
    db: Session = Depends(get_db),
    membership=Depends(require_project_roles([UserRole.OWNER]))
):
    """Change a member's role (only OWNER)."""
    return membership_service.change_member_role(project_id, user_id, body.role, db)