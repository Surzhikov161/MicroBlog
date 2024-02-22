import pytest
from backend.src.database.database import async_session
from backend.src.main import app
from backend.src.models.models import (
    Image,
    Tweet,
    Users,
    followers,
    tweet_like,
)
from fastapi.testclient import TestClient

client = TestClient(app, headers={"api-key": "test"})


@pytest.mark.asyncio
async def test_create_tweet():
    json = {"tweet_data": "tweet_data", "tweet_media_ids": []}
    response = client.post("/api/tweets/", json=json)
    assert response.status_code == 200
    assert "tweet_id" in response.json()
    async with async_session() as session:
        new_tweet = await session.get(Tweet, response.json()["tweet_id"])
        await session.commit()
        assert new_tweet

    fail_json_1 = {"data": "tweet_data", "tweet_media_ids": []}
    fail_response_1 = client.post("/api/tweet/", json=fail_json_1)
    assert fail_response_1.status_code == 404

    fail_json_2 = {
        "tweet_data": "tweet_data",
        "tweet_media_ids": [
            0,
        ],
    }
    fail_response_2 = client.post("/api/tweets/", json=fail_json_2)
    assert fail_response_2.json() == {
        "result": False,
        "msg": "Not found images with given ids",
    }

    async with async_session() as session:
        async with session.begin():
            await session.delete(new_tweet)
        await session.commit()


@pytest.mark.asyncio
async def test_delete_tweet():
    new_tweet = Tweet(data="test", user_id=1)
    async with async_session() as session:
        async with session.begin():
            session.add(new_tweet)
        tweet_id = new_tweet.id
        await session.commit()

    response = client.delete(f"/api/tweets/{tweet_id}")
    assert response.status_code == 200
    assert response.json() == {"result": True}
    async with async_session() as session:
        tweet = await session.get(Tweet, tweet_id)
        assert not tweet

    fail_response = client.delete("/api/tweets/0")
    assert fail_response.json() == {
        "result": False,
        "msg": "This tweet doesn't exist",
    }


@pytest.mark.asyncio
async def test_like():
    new_tweet = Tweet(data="test", user_id=1)
    async with async_session() as session:
        async with session.begin():
            session.add(new_tweet)
        tweet_id = new_tweet.id
        await session.commit()

    response = client.post(f"/api/tweets/{tweet_id}/likes")
    assert response.status_code == 200
    assert response.json() == {"result": True}
    select_stmt = tweet_like.select().where(tweet_like.c.tweet_id == tweet_id)
    async with async_session() as session:
        like = (await session.execute(select_stmt)).scalars().one_or_none()
        assert like
        await session.commit()

    fail_response_1 = client.post("/api/tweets/0/likes")
    assert fail_response_1.status_code == 404
    assert fail_response_1.json() == {
        "result": False,
        "msg": "This tweet doesn't exist",
    }

    fail_response_2 = client.post(f"/api/tweets/{tweet_id}/likes")
    assert fail_response_2.status_code == 404
    assert fail_response_2.json() == {
        "result": False,
        "msg": "This tweet is already liked",
    }

    async with async_session() as session:
        async with session.begin():
            await session.delete(new_tweet)
        await session.commit()


def test_get_feed():
    response = client.get("api/tweets/")
    assert response.status_code == 200
    assert "tweets" in response.json()


@pytest.mark.asyncio
async def test_add_follow():
    new_user = Users(name="name", nickname="nickname", api_key="api_key")
    async with async_session() as session:
        async with session.begin():
            session.add(new_user)
        user_id = new_user.id
        await session.commit()
    response = client.post(f"api/users/{user_id}/follow")
    assert response.status_code == 200
    assert response.json() == {"result": True}

    fail_response_1 = client.post(f"api/users/{user_id}/follow")
    assert fail_response_1.json() == {
        "result": False,
        "msg": "This user is already followed",
    }

    fail_response_2 = client.post("api/users/0/follow")
    assert fail_response_2.json() == {
        "result": False,
        "msg": "This user doesn't exist",
    }
    async with async_session() as session:
        async with session.begin():
            await session.delete(new_user)
        await session.commit()


@pytest.mark.asyncio
async def test_remove_follow():
    new_user = Users(name="name", nickname="nickname", api_key="api_key")
    async with async_session() as session:
        async with session.begin():
            session.add(new_user)
        user_id = new_user.id
        await session.commit()
    client.post(f"api/users/{user_id}/follow")

    response = client.delete(f"api/users/{user_id}/follow")
    assert response.json() == {"result": True}
    async with async_session() as session:
        stmt = followers.select().where(
            followers.c.user_id == 1, followers.c.follower_id == user_id
        )
        follow = (await session.execute(stmt)).scalars().one_or_none()
        assert not follow

    fail_response_1 = client.delete(f"api/users/{user_id}/follow")
    assert fail_response_1.json() == {
        "result": False,
        "msg": "This user is not followed",
    }

    fail_response_2 = client.post("api/users/0/follow")
    assert fail_response_2.json() == {
        "result": False,
        "msg": "This user doesn't exist",
    }
    async with async_session() as session:
        async with session.begin():
            await session.delete(new_user)
        await session.commit()


def test_get_me():
    response = client.get("api/users/me")
    assert response.status_code == 200
    assert "user" in response.json()


@pytest.mark.asyncio
async def test_get_user_by_id():
    new_user = Users(name="name", nickname="nickname", api_key="api_key")
    async with async_session() as session:
        async with session.begin():
            session.add(new_user)
        user_id = new_user.id
        await session.commit()

    response = client.get(f"api/users/{user_id}")
    assert response.status_code == 200
    assert "user" in response.json()

    fail_response = client.get("api/users/0")
    assert fail_response.json() == {
        "result": False,
        "msg": "This user doesn't exist",
    }

    async with async_session() as session:
        async with session.begin():
            await session.delete(new_user)
        await session.commit()


@pytest.mark.asyncio
async def test_upload_image():
    with open("tests/test_images/cat.jpg", "rb") as f:
        response = client.post("api/medias", files={"file": f})
        assert response.status_code == 200
        assert "media_id" in response.json()
        async with async_session() as session:
            image = await session.get(Image, response.json()["media_id"])
            assert image
            await session.commit()
            async with session.begin():
                await session.delete(image)
            await session.commit()
