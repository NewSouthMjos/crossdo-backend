from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI

from app.commons.database import create_db_and_tables
from app.commons.openapi import OPENAPI_SECURITY_EXTRA
from app.courses.router import router as courses_router
from app.courses_streams.router import router as streams_router
from app.users.models import User
from app.users.schemas import UserCreate, UserRead, UserUpdate
from app.users.users import (
    SECRET,
    auth_backend,
    current_active_user,
    fastapi_users,
    google_oauth_client,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title="crossdo",
        version="0.0.0",
        description="crossdo backend",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)
app.include_router(
    fastapi_users.get_oauth_router(google_oauth_client, auth_backend, SECRET),
    prefix="/auth/google",
    tags=["auth"],
)

app.include_router(courses_router)
app.include_router(streams_router)


@app.get("/authenticated-route", openapi_extra=OPENAPI_SECURITY_EXTRA)
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
