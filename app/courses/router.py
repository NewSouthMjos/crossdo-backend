from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func

from app.commons.database import get_async_session
from app.commons.openapi import OPENAPI_SECURITY_EXTRA
from app.commons.schemas import Pagination
from app.courses import models
from app.users.models import User
from app.users.users import current_active_user

from .schemas import CourseCreate, CourseRead, CourseUpdate, ReviewCreate, ReviewRead


router = APIRouter(prefix="/courses", tags=["Courses"])

COURSE_SECURITY_MESSAGE = "Available only for course creator"


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED, openapi_extra=OPENAPI_SECURITY_EXTRA)
async def create_course(
    course: CourseCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    db_course = models.Course(
        **course.model_dump(),
        created_by=user.id,
    )
    db.add(db_course)
    await db.commit()
    await db.refresh(db_course)
    return db_course


@router.get("/", response_model=Pagination[CourseRead], openapi_extra=OPENAPI_SECURITY_EXTRA)
async def read_courses(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(default=1, ge=1, description="Page number starting from 1"),
    per_page: int = Query(default=10, ge=1, le=100, description="Number of items per page"),
):
    total = (await db.scalars(select(func.count()).select_from(models.Course))).one()

    offset = (page - 1) * per_page

    courses = (
        await db.scalars(select(models.Course).order_by(models.Course.created_at.desc()).offset(offset).limit(per_page))
    ).all()

    return Pagination[CourseRead](
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
        total=total,
        items=[CourseRead.model_validate(c) for c in courses],
    )


@router.get(
    "/{course_id}",
    response_model=CourseRead,
    status_code=status.HTTP_200_OK,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
)
async def read_course(
    course_id: int, user: User = Depends(current_active_user), db: AsyncSession = Depends(get_async_session)
):
    stmt = select(models.Course).options(selectinload(models.Course.reviews)).filter(models.Course.id == course_id)
    result = await db.execute(stmt)
    course = result.scalars().first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.put(
    "/{course_id}", response_model=CourseRead, status_code=status.HTTP_200_OK, openapi_extra=OPENAPI_SECURITY_EXTRA
)
async def update_course(
    course_id: int,
    course_data: CourseUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    stmt = select(models.Course).where(models.Course.id == course_id)
    result = await db.execute(stmt)
    course = result.scalars().first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this course")

    for key, value in course_data.dict(exclude_unset=True).items():
        setattr(course, key, value)

    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


@router.post(
    "/{course_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
)
async def create_review(
    course_id: int,
    review_data: ReviewCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    course = await db.get(models.Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    review = models.Review(course_id=course_id, user_id=user.id, rating=review_data.rating, comment=review_data.comment)
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return review


@router.get(
    "/{course_id}/reviews",
    response_model=List[ReviewRead],
    status_code=status.HTTP_200_OK,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
)
async def read_reviews(course_id: int, db: AsyncSession = Depends(get_async_session)):
    course = await db.get(models.Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    stmt = select(models.Review).where(models.Review.course_id == course_id).order_by(models.Review.created_at.desc())
    result = await db.execute(stmt)
    reviews = result.scalars().all()

    return reviews
