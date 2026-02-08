# app/core/pagination.py
from sqlalchemy.orm import Query
from sqlalchemy import asc, desc
from app.schemas.pagination import PaginationParams, PaginatedResponse, SortParams
from typing import TypeVar

T = TypeVar('T')


def apply_sorting(query: Query, sort_params: SortParams, model, allowed_fields: list[str]) -> Query:
    """
    Apply sorting to a SQLAlchemy query.
    
    Args:
        query: SQLAlchemy query object
        sort_params: Sorting parameters
        model: SQLAlchemy model class
        allowed_fields: List of field names that can be sorted
    """
    if not sort_params.sort_by:
        return query
    
    if sort_params.sort_by not in allowed_fields:
        return query
    
    sort_column = getattr(model, sort_params.sort_by)
    
    if sort_params.sort_order == "desc":
        return query.order_by(desc(sort_column))
    else:
        return query.order_by(asc(sort_column))


def paginate(
    query: Query,
    pagination: PaginationParams,
    model_class: type[T]
) -> PaginatedResponse[T]:
    """
    Apply pagination to a query and return paginated response.
    
    Args:
        query: SQLAlchemy query (already filtered and sorted)
        pagination: Pagination parameters
        model_class: Type hint for response items
    
    Returns:
        PaginatedResponse with items and metadata
    """
    total = query.count()
    
    items = query.offset(pagination.offset).limit(pagination.limit).all()
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )