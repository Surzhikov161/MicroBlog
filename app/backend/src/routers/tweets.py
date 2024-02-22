from backend.src.config_data.config import IMAGE_PATH, IMAGE_TYPE
from backend.src.database.database import async_session
from backend.src.database.utils import (
    add_like,
    create_tweet,
    delete_like_db,
    delete_tweet_db,
    get_tweet_without_user,
    get_tweet_without_user_and_likes,
    get_tweets,
)
from backend.src.dependencies import token_required
from backend.src.models.models import Users
from backend.src.models.schemas import (
    ErrorModel,
    FeedModel,
    ReturnModel,
    ReturnModelWithMsg,
    TweetModel,
    TweetResult,
)
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/api/tweets",
    tags=["tweets"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(token_required)],
)


@router.post("/", response_model=ReturnModelWithMsg | TweetResult)
async def add_tweet(tweet: TweetModel, request: Request):
    """
    Route создания твита
    :param tweet: json для создания твита
    :param request:
    :return:
    """
    user: Users = request.state.current_user
    tweet_data = tweet.model_dump()
    new_tweet_id = await create_tweet(
        async_session,
        tweet_data["tweet_data"],
        user.id,
        tweet_data["tweet_media_ids"],
    )
    if new_tweet_id:
        return {"result": True, "tweet_id": new_tweet_id}

    return JSONResponse(
        status_code=404,
        content={
            "result": False,
            "msg": "Not found images with given ids",
        },
    )


@router.delete("/{tweet_id}", response_model=ReturnModelWithMsg | ReturnModel)
async def delete_tweet(tweet_id: int, request: Request):
    """
    Route удаления твита
    :param tweet_id: Id твита
    :param request:
    :return:
    """
    user: Users = request.state.current_user
    tweet = await get_tweet_without_user_and_likes(async_session, tweet_id)
    if tweet:
        if tweet.user_id != user.id:
            return JSONResponse(
                status_code=403,
                content={"result": False, "msg": "This user is not author"},
            )
        await delete_tweet_db(async_session, tweet)
        return {"result": True}
    return JSONResponse(
        status_code=404,
        content={"result": False, "msg": "This tweet doesn't exist"},
    )


@router.post(
    "/{tweet_id}/likes", response_model=ReturnModelWithMsg | ReturnModel
)
async def to_like_a_tweet(tweet_id: int, request: Request):
    """
    Route добавления лайка
    :param tweet_id: Id твита
    :param request:
    :return:
    """
    user: Users = request.state.current_user
    tweet = await get_tweet_without_user(async_session, tweet_id)

    if tweet:
        if user.id in [like.id for like in tweet.likes]:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "msg": "This tweet is already liked",
                },
            )
        await add_like(async_session, user.id, tweet.id)
        return {"result": True}
    return JSONResponse(
        status_code=404,
        content={"result": False, "msg": "This tweet doesn't exist"},
    )


@router.delete(
    "/{tweet_id}/likes", response_model=ReturnModelWithMsg | ReturnModel
)
async def delete_like(tweet_id: int, request: Request):
    """
    Route удаления лайка
    :param tweet_id: Id твита
    :param request:
    :return:
    """
    user: Users = request.state.current_user
    tweet = await get_tweet_without_user(async_session, tweet_id)

    if tweet:
        if user.id not in [user_like.id for user_like in tweet.likes]:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "msg": "This tweet is not liked",
                },
            )
        await delete_like_db(async_session, user.id, tweet.id)
        return {"result": True}
    return JSONResponse(
        status_code=404,
        content={"result": False, "msg": "This tweet doesn't exist"},
    )


@router.get("/", response_model=FeedModel | ErrorModel)
async def get_tweet_feed(request: Request):
    """
    Route получения ленты твитов пользователя
    :param request:
    :return:
    """
    try:
        user: Users = request.state.current_user
        user_tweets = await get_tweets(async_session, user)

        return {
            "result": True,
            "tweets": [
                {
                    "id": tweet.id,
                    "content": tweet.data,
                    "attachments": [
                        f"{IMAGE_PATH}{image.image_name}{IMAGE_TYPE}"
                        for image in tweet.images
                    ],
                    "author": {
                        "id": tweet.user_id,
                        "name": tweet.user.nickname,
                    },
                    "likes": [
                        {
                            "user_id": u.id,
                            "name": u.nickname,
                        }
                        for u in tweet.likes
                    ],
                }
                for tweet in user_tweets
            ],
        }

    except Exception as error:
        return {
            "result": False,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
