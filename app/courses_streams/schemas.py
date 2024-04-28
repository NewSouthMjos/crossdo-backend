from datetime import datetime
from typing import Optional
from uuid import UUID

from annotated_types import Ge, Le
from pydantic import BaseModel, HttpUrl, NonNegativeInt, PositiveInt, StringConstraints
from typing_extensions import Annotated


class StreamBase(BaseModel):
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    description: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    total_cost: NonNegativeInt
    min_participants: Annotated[int, Ge(2), Le(100)]
    max_participants: Annotated[int, Ge(2), Le(100)]
    duration_weeks: PositiveInt
    schedule: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]


class StreamCreate(StreamBase):
    course_id: PositiveInt


class StreamUpdate(StreamBase):
    has_started: bool


class StreamRead(StreamBase):
    id: PositiveInt
    leader_id: UUID
    course_id: PositiveInt
    course_name: str
    has_started: bool
    start_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    participants: list[UUID]

    class Config:
        orm_mode = True


class ParticipantBase(BaseModel):
    user_id: UUID


class ParticipantCreate(ParticipantBase):
    pass


class ParticipantRead(ParticipantBase):
    id: PositiveInt
    stream_id: PositiveInt
    registered_at: datetime

    class Config:
        orm_mode = True
