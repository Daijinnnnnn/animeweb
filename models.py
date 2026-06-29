
from datetime import datetime
import enum 
from typing import List,Optional
from sqlalchemy import BigInteger, ForeignKey, String, Enum,func
from sqlalchemy.orm import Mapped, relationship,mapped_column,relationship,DeclarativeBase
from database import Base



class WatchStatus(enum.Enum):
    WATCHING = "смотрю"
    WATCHED = "просмотрено"
    PLANNED = "в планах"
    DROPPED = "брошено"


class User(Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(25))
    fullname: Mapped[str | None] = mapped_column()
    login: Mapped[str] = mapped_column(String(20))
    email_address: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    registered_at: Mapped[datetime] = mapped_column(server_default=func.now())
    anime_associations: Mapped[List["UserAnimeList"]] = relationship(
        back_populates="user", cascade= 'all,delete-orphan'
        )


class Anime(Base):

    __tablename__ = "anime_list"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,autoincrement=False)
    name_anime: Mapped[str] = mapped_column(nullable=False)
    user_associations: Mapped[List["UserAnimeList"]] = relationship(
        back_populates='anime',cascade="all, delete-orphan"
        )
    


class UserAnimeList(Base):

    __tablename__ = "user_anime_list"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id", ondelete="CASCADE"))
    anime_id: Mapped[int] = mapped_column(ForeignKey("anime_list.id", ondelete="CASCADE"))
    status: Mapped[WatchStatus] = mapped_column(Enum(WatchStatus), default=WatchStatus.PLANNED)
    user: Mapped["User"] = relationship(back_populates="anime_associations")
    anime: Mapped["Anime"] = relationship(back_populates="user_associations")

