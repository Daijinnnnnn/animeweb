from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import func, Integer
from config import setting
from datetime import datetime


DATABASE_URL = setting.get_db_url()


engine = create_async_engine(url=DATABASE_URL)
async_sessionmaker = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs,DeclarativeBase):
    __abstract__ = True


    create_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"


async def get_db():
    async with async_sessionmaker() as session:
        yield session 