# app/schemas/pagination.py
from pydantic import BaseModel, Field, field_validator
from typing import Generic, TypeVar
from app.core.config import settings

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Query parameters for pagination"""
    page: int = Field(default=1, ge=1, description="Page number (starts at 1)")
    page_size: int = Field(
        default=settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description=f"Items per page (max {settings.MAX_PAGE_SIZE})"
    )
    @property
    def offset(self) -> int:
        """Calculate SQL offset"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get SQL limit"""
        return self.page_size

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper"""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Factory method to create paginated response"""
        total_pages = (total + page_size - 1) // page_size  
        
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )

class SortParams(BaseModel):
    """Query parameters for sorting"""
    sort_by: str | None = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="asc", description="Sort order: asc or desc")
    
    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value: str) -> str:
        if value.lower() not in ["asc", "desc"]:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return value.lower()