import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, foreign, relationship
from sqlalchemy.sql import func

from app.commons.database import Base
from app.users.models import User


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    created_by: UUID = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    course_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(
        primaryjoin=(foreign(User.id) == created_by),
        lazy="selectin",
    )
    course_streams = relationship("CourseStream", back_populates="course")
    reviews: Mapped[list["Review"]] = relationship(back_populates="course")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    course = relationship("Course", back_populates="reviews")
    user = relationship("User")
