from typing import TypeVar, Generic, List
from sqlalchemy.orm import Query

T = TypeVar("T")


def paginate(query: Query, page: int = 1, page_size: int = 20) -> dict:
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
