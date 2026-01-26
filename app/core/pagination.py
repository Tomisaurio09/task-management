# app/core/pagination.py
from sqlalchemy.orm import Query
from sqlalchemy import asc, desc
from app.schemas.pagination import PaginationParams, PaginatedResponse, SortParams
from typing import TypeVar

#representa un generic que esta definido en schemas/pagination.py
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
    #retorna si no hay algun campo para ordenar
    if not sort_params.sort_by:
        return query
    
    #en caso de que el usuario intente ordenar por un campo que no esta permitido
    if sort_params.sort_by not in allowed_fields:
        # Silently ignore invalid fields or raise ValidationError
        return query
    
    # Get the model attribute
    #busca dentro de la clase model el atributo con ese nombre y lo devuelve.
    sort_column = getattr(model, sort_params.sort_by)
    
    # Apply sort direction
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
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    items = query.offset(pagination.offset).limit(pagination.limit).all()
    
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size
    )