from typing import Optional

from backend.src.database.database import Base, async_session
from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Table,
    Uuid,
)
from sqlalchemy.future import select
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = "users"

    id = Column(
        Integer, Sequence("users_id_seq"), primary_key=True, nullable=False
    )
    name = Column(String(50), nullable=False)
    nickname = Column(String(50), nullable=False)
    api_key = Column(String(), nullable=False, unique=True)
    followers = relationship(
        "Users",
        secondary="followers",
        primaryjoin="Users.id==followers.c.follower_id",
        secondaryjoin="Users.id==followers.c.user_id==id",
        back_populates="followers",
        lazy="joined",
        join_depth=2,
    )
    followed = relationship(
        "Users",
        secondary="followers",
        primaryjoin="Users.id==followers.c.user_id",
        secondaryjoin="Users.id==followers.c.follower_id",
        back_populates="followed",
        lazy="joined",
        join_depth=2,
        overlaps="followers",
    )

    @classmethod
    async def get_by_token(cls, token) -> Optional["Users"]:
        async with async_session() as session:
            result = await session.execute(
                select(Users).where(Users.api_key == token)
            )

            user = result.unique().scalars().one_or_none()
            return user


followers = Table(
    "followers",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey(Users.id),
        primary_key=True,
    ),
    Column(
        "follower_id",
        Integer,
        ForeignKey(Users.id),
        primary_key=True,
    ),
)


tweet_like = Table(
    "tweet_like",
    Base.metadata,
    Column(
        "tweet_id",
        Integer,
        ForeignKey("tweet.id", ondelete="CASCADE"),
    ),
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
    ),
)


class Tweet(Base):
    __tablename__ = "tweet"

    id = Column(
        Integer, Sequence("tweet_id_seq"), primary_key=True, nullable=False
    )

    data = Column(String(500), nullable=False)
    images = relationship(
        "Image",
        backref="tweets",
        single_parent=True,
        cascade="all,delete-orphan",
        lazy="selectin",
    )
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("Users", backref="tweets", lazy="selectin")
    likes = relationship(
        "Users",
        secondary="tweet_like",
        backref="likes",
        lazy="selectin",
    )


class Image(Base):
    __tablename__ = "image"

    id = Column(
        Integer, Sequence("image_id_seq"), primary_key=True, nullable=False
    )
    image_name = Column(Uuid, nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweet.id"))
