from datetime import datetime
from typing import Optional
from uuid import UUID

from annotated_types import Ge, Le
from pydantic import BaseModel, PositiveInt, StringConstraints
from typing_extensions import Annotated


class CourseBase(BaseModel):
    title: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    description: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    course_url: str


class CourseCreate(CourseBase):
    pass


class CourseUpdate(CourseBase):
    pass


class CourseRead(CourseBase, from_attributes=True):
    id: PositiveInt
    # rating: float
    created_at: datetime
    updated_at: datetime


class ReviewBase(BaseModel):
    rating: Annotated[int, Ge(1), Le(5)]
    comment: Optional[Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]]


class ReviewCreate(ReviewBase):
    pass


class ReviewRead(ReviewBase):
    id: PositiveInt
    course_id: PositiveInt
    user_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
