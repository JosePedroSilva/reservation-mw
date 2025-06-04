import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
  AsyncSession,
  create_async_engine,
  async_sessionmaker,
)
from sqlalchemy.exc import SQLAlchemyError

DATABASE_URL = os.getenv(
  "DATABASE_URL",
  "postgresql+asyncpg://user:password@db:5432/reservations",
)

engine = create_async_engine(
  DATABASE_URL,
  echo=False,
  pool_pre_ping=True,
)

async_session = async_sessionmaker(
  bind=engine,
  expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
  async with async_session() as session:
    try:
      yield session
    except SQLAlchemyError:
      await session.rollback()
      raise
    finally:
      await session.close()


async def init_models() -> None:
  from .models import Base  
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)
  
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
