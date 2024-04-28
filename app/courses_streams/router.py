import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.commons.database import get_async_session
from app.commons.openapi import OPENAPI_SECURITY_EXTRA
from app.commons.schemas import Pagination
from app.courses import models as courses_models
from app.courses_streams import models as streams_models
from app.users.models import User
from app.users.users import current_active_user

from .schemas import StreamCreate, StreamRead, StreamUpdate


router = APIRouter(prefix="/streams", tags=["Streams"])
COURSE_STREAMS_SECURITY_MESSAGE = "Available only for course stream creator"


def construct_stream(user_id, course_title, new_stream):
    return StreamRead(
        id=new_stream.id,
        course_id=new_stream.course_id,
        name=new_stream.name,
        description=new_stream.description,
        total_cost=new_stream.total_cost,
        min_participants=new_stream.min_participants,
        max_participants=new_stream.max_participants,
        duration_weeks=new_stream.duration_weeks,
        schedule=new_stream.schedule,
        leader_id=user_id,
        course_name=course_title,
        start_date=new_stream.start_date,
        created_at=new_stream.created_at,
        updated_at=new_stream.updated_at,
        has_started=new_stream.has_started,
        participants=[p.user_id for p in new_stream.participants],
    )


@router.post(
    "/",
    response_model=StreamRead,
    status_code=status.HTTP_201_CREATED,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
)
async def create_stream(
    stream: StreamCreate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    course = await db.get(courses_models.Course, stream.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    new_stream = streams_models.CourseStream(
        **stream.model_dump(),
        created_by=user.id,
        # course_id=course_id,
        start_date=None,
    )
    db.add(new_stream)
    await db.commit()
    await db.refresh(new_stream)
    return construct_stream(user.id, course.title, new_stream)


@router.get("/", response_model=Pagination[StreamRead], openapi_extra=OPENAPI_SECURITY_EXTRA)
async def read_streams(
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
    page: int = Query(default=1, ge=1, description="Page number starting from 1"),
    per_page: int = Query(default=10, ge=1, le=100, description="Number of items per page"),
):
    total = (await db.scalars(select(func.count()).select_from(streams_models.CourseStream))).one()

    offset = (page - 1) * per_page

    streams = (
        await db.scalars(
            select(streams_models.CourseStream)
            .order_by(streams_models.CourseStream.created_at.desc())
            .offset(offset)
            .limit(per_page)
        )
    ).all()

    return Pagination[StreamRead](
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
        total=total,
        items=[construct_stream(s.course.user.id, s.course.title, s) for s in streams],
    )


@router.get(
    "/{stream_id}",
    response_model=StreamRead,
    status_code=status.HTTP_200_OK,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
)
async def read_stream(stream_id: int, db: AsyncSession = Depends(get_async_session)):
    stmt = select(streams_models.CourseStream).where(streams_models.CourseStream.id == stream_id)
    result = await db.execute(stmt)
    stream = result.scalars().first()

    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    return construct_stream(stream.course.user.id, stream.course.title, stream)


@router.put(
    "/{stream_id}",
    response_model=StreamRead,
    status_code=status.HTTP_200_OK,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
)
async def update_stream(
    stream_id: int,
    stream_data: StreamUpdate,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    stmt = select(streams_models.CourseStream).where(streams_models.CourseStream.id == stream_id)
    result = await db.execute(stmt)
    stream = result.scalars().first()

    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    if stream.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this stream")

    for key, value in stream_data.dict(exclude_unset=True).items():
        setattr(stream, key, value)

    if stream_data.has_started is True:
        stream.start_date = datetime.datetime.utcnow()
        stream.has_started = True

    db.add(stream)
    await db.commit()
    await db.refresh(stream)

    return construct_stream(stream.course.user.id, stream.course.title, stream)


@router.delete(
    "/{stream_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
    description=COURSE_STREAMS_SECURITY_MESSAGE,
)
async def delete_stream(
    stream_id: int,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    stmt = select(streams_models.CourseStream).where(streams_models.CourseStream.id == stream_id)
    result = await db.execute(stmt)
    stream = result.scalars().first()

    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    if stream.created_by != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this stream")

    if stream.has_started:
        raise HTTPException(status_code=400, detail="Cant delete already started stream")

    stmt = delete(streams_models.Participant).where(streams_models.Participant.stream_id == stream.id)
    await db.execute(stmt)
    stmt = delete(streams_models.CourseStream).where(streams_models.CourseStream.id == stream_id)
    result = await db.execute(stmt)
    await db.commit()
    return


@router.post(
    "/{stream_id}/participate",
    status_code=status.HTTP_201_CREATED,
    openapi_extra=OPENAPI_SECURITY_EXTRA,
)
async def participate_in_stream(
    stream_id: int,
    user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    stream = await db.get(streams_models.CourseStream, stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Stream not found")

    existing_participant = await db.execute(
        select(streams_models.Participant).where(
            streams_models.Participant.user_id == user.id, streams_models.Participant.stream_id == stream_id
        )
    )
    if existing_participant.scalars().first():
        raise HTTPException(status_code=400, detail="User already participates in this stream")

    new_participant = streams_models.Participant(user_id=user.id, stream_id=stream_id)
    db.add(new_participant)
    await db.commit()

    return Response(status_code=status.HTTP_201_CREATED)
