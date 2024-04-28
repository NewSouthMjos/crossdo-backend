from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class Pagination(BaseModel, Generic[T]):
    page: int
    per_page: int
    total_pages: int
    total: int
    items: List[T]

    class Config:
        arbitrary_types_allowed = True
