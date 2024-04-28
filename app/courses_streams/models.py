from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, foreign, relationship
from sqlalchemy.sql import func

from app.commons.database import Base
from app.courses.models import Course
from app.users.models import User


class CourseStream(Base):
    __tablename__ = "course_streams"

    id = Column(Integer, primary_key=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, nullable=True)
    has_started = Column(Boolean, nullable=False, server_default="false")
    total_cost = Column(Integer, nullable=False)
    min_participants = Column(Integer, nullable=False)
    max_participants = Column(Integer, nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    schedule = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # course = relationship("Course", back_populates="course_streams")
    course: Mapped[list["Course"]] = relationship(back_populates="course_streams", lazy="selectin")
    participants: Mapped[list["Participant"]] = relationship(back_populates="stream", lazy="selectin")

    class Config:
        orm_mode = True


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    stream_id = Column(Integer, ForeignKey("course_streams.id"), nullable=False)

    # Определение обратной связи
    user: Mapped["User"] = relationship(
        primaryjoin=(foreign(User.id) == user_id),
        lazy="selectin",
    )
    stream: Mapped["CourseStream"] = relationship("CourseStream", back_populates="participants")
