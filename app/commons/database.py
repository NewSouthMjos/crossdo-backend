from typing import AsyncGenerator

from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.commons.settings import get_settings


settings = get_settings()


database_url = make_url(settings.DATABASE_URL)
database_url = database_url.set(drivername=f"{database_url.drivername}+asyncpg")


class Base(DeclarativeBase):
    pass


engine = create_async_engine(database_url)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
