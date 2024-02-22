from typing import List, Optional

from backend.src.models.models import (
    Image,
    Tweet,
    Users,
    followers,
    tweet_like,
)
from sqlalchemy import Column
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm.strategy_options import noload, subqueryload


async def create_tweet(
    async_session: async_sessionmaker[AsyncSession],
    tweet_data: str,
    user_id: Column[int],
    media_ids: Optional[List[Column[int]]] = None,
):
    """
    Функция создания твита
    :param async_session: Асинхронная сессия
    :param tweet_data: Содержание твита
    :param user_id: Id пользователя
    :param media_ids: Ids фотографиий к твиту
    :return: Id нового твита
    """
    new_tweet: Tweet = Tweet(data=tweet_data, user_id=user_id)
    if media_ids:
        async with async_session() as session:
            res = await session.execute(
                select(Image).filter(Image.id.in_(media_ids))
            )
            images = res.scalars().all()
            if len(images) != len(media_ids):
                return
            new_tweet.images.extend(images)
    async with async_session() as session:
        async with session.begin():
            session.add(new_tweet)
        await session.commit()
    return new_tweet.id


async def get_tweet_without_user_and_likes(
    async_session: async_sessionmaker[AsyncSession],
    tweet_id: int,
):
    """
    Функция получения объекта Tweet без загрузки связей user и likes
    :param async_session: Асинхронная сессия
    :param tweet_id: id твита
    :return: Объект модели Tweet
    """
    async with async_session() as session:
        res = await session.execute(
            select(Tweet)
            .filter(Tweet.id.in_([tweet_id]))
            .options(
                noload(Tweet.likes),
                noload(Tweet.user),
            )
        )
        await session.commit()
        tweet = res.scalars().one_or_none()
        return tweet


async def delete_tweet_db(
    async_session: async_sessionmaker[AsyncSession],
    tweet: Tweet,
):
    """
    Функция удаления твита
    :param async_session: Асинхронная сессия
    :param tweet: Объект модели Tweet
    :return: None
    """
    async with async_session() as session:
        async with session.begin():
            statement = tweet_like.delete().where(
                tweet_like.c.tweet_id == tweet.id
            )
            await session.execute(statement)
            await session.delete(tweet)
            await session.commit()


async def get_tweet_without_user(
    async_session: async_sessionmaker[AsyncSession],
    tweet_id: int,
):
    """
    Функция получения объекта Tweet без загрузки связи user
    :param async_session: Асинхронная сессия
    :param tweet_id: Id твита
    :return: Объект модели Tweet
    """
    async with async_session() as session:
        res = await session.execute(
            select(Tweet)
            .filter(Tweet.id.in_([tweet_id]))
            .options(
                subqueryload(Tweet.likes).options(
                    noload(Users.followers), noload(Users.followed)
                ),
                noload(Tweet.user),
            )
        )
        tweet = res.scalars().one_or_none()
        await session.commit()
        return tweet


async def add_like(
    async_session: async_sessionmaker[AsyncSession],
    user_id: Column[int],
    tweet_id: int,
):
    """
    Функция добавления лайка к твиту в бд
    :param async_session: Асинхронная сессия
    :param user_id: Id пользователя
    :param tweet_id: Id твита
    :return: None
    """
    statement = tweet_like.insert().values(user_id=user_id, tweet_id=tweet_id)
    async with async_session() as session:
        async with session.begin():
            await session.execute(statement)
        await session.commit()


async def delete_like_db(
    async_session: async_sessionmaker[AsyncSession],
    user_id: Column[int],
    tweet_id: int,
):
    """
    Функция удаления лайка с твита
    :param async_session: Асинхронная сессия
    :param user_id: Id пользователя
    :param tweet_id: Id твита
    :return: None
    """
    statement = tweet_like.delete().where(
        tweet_like.c.tweet_id == tweet_id, tweet_like.c.user_id == user_id
    )
    async with async_session() as session:
        async with session.begin():
            await session.execute(statement)
        await session.commit()


async def get_tweets(
    async_session: async_sessionmaker[AsyncSession],
    user: Users,
):
    """
    Функция получения из бд твитов для ленты
    :param async_session: Асинхронная сессия
    :param user: Объект модели Users
    :return: Список объектов Tweet
    """
    async with async_session() as session:
        ids = [u.id for u in user.followed] + [user.id]
        res_1 = await session.execute(
            select(Tweet)
            .filter(Tweet.user_id.in_(ids))
            .order_by(Tweet.id.desc())
            .options(
                subqueryload(Tweet.likes).options(
                    noload(Users.followers), noload(Users.followed)
                ),
                subqueryload(Tweet.user).options(
                    noload(Users.followers), noload(Users.followed)
                ),
            )
        )
        try:
            user_tweets = res_1.scalars().all()
        except NoResultFound:
            user_tweets = []
        return user_tweets


async def get_following_user(
    async_session: async_sessionmaker[AsyncSession],
    following_id: int,
):
    """
    Получения пользователя по id
    :param async_session: Асинхронная сессия
    :param following_id: Id пользователя, на которого подписываются
    :return: Объект модели Users
    """
    async with async_session() as session:
        following_user: Users | None = await session.get(Users, following_id)
    return following_user


async def follow_user_db(
    async_session: async_sessionmaker[AsyncSession],
    user_id: Column[int],
    following_id: int,
):
    """
    Функция добавления в бд записи подписки одного пользователя на другого
    :param async_session: Асинхронная сессия
    :param user_id: Id пользователя, который подписывается
    :param following_id: Id пользователя, на которого подписываются
    :return: None
    """
    async with async_session() as session:
        async with session.begin():
            statement = followers.insert().values(
                user_id=user_id, follower_id=following_id
            )
            await session.execute(statement)
        await session.commit()


async def remove_follow_db(
    async_session: async_sessionmaker[AsyncSession],
    user_id: Column[int],
    following_id: int,
):
    """
    Функция удаления подписки
    :param async_session: Асинхронная сессия
    :param user_id: Id пользователя, который подписывается
    :param following_id: Id пользователя, на которого подписываются
    :return: None
    """
    async with async_session() as session:
        async with session.begin():
            statement = followers.delete().where(
                followers.c.user_id == user_id,
                followers.c.follower_id == following_id,
            )
            await session.execute(statement)
        await session.commit()


async def get_user(
    async_session: async_sessionmaker[AsyncSession],
    user_id: int,
):
    """
    Функция получения пользователя по id
    :param async_session: Асинхронная сессия
    :param user_id: Id искомого пользователя
    :return: Объект модели Users
    """
    async with async_session() as session:
        user: Users | None = await session.get(Users, user_id)
    return user


async def add_image(
    async_session: async_sessionmaker[AsyncSession], image: Image
):
    """
    Функция добавления картинки в бд.
    :param async_session: Асинхронная сессия
    :param image: Объект модели Image
    :return: None
    """
    async with async_session() as session:
        async with session.begin():
            session.add(image)
