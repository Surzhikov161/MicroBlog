from backend.src.database.database import async_session
from backend.src.database.utils import (
    follow_user_db,
    get_following_user,
    get_user,
    remove_follow_db,
)
from backend.src.dependencies import token_required
from backend.src.models.models import Users
from backend.src.models.schemas import (
    ReturnModel,
    ReturnModelWithMsg,
    UserModel,
)
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
    dependencies=[Depends(token_required)],
)


@router.post(
    "/{user_id}/follow", response_model=ReturnModelWithMsg | ReturnModel
)
async def follow_user(user_id: int, request: Request):
    """
    Route добавления подписки к пользователю
    :param user_id: Id твита
    :param request:
    :return:
    """
    current_user: Users = request.state.current_user
    following_user = await get_following_user(async_session, user_id)

    if following_user:
        if following_user.id in [
            follower.id for follower in current_user.followed
        ]:
            return JSONResponse(
                status_code=404,
                content={
                    "result": False,
                    "msg": "This user is already followed",
                },
            )
        elif current_user.id == following_user.id:
            return JSONResponse(
                status_code=403,
                content={"result": False, "msg": "Cannot follow yourself"},
            )
        await follow_user_db(async_session, current_user.id, user_id)
        return {"result": True}

    return JSONResponse(
        status_code=404,
        content={"result": False, "msg": "This user doesn't exist"},
    )


@router.delete(
    "/{user_id}/follow", response_model=ReturnModelWithMsg | ReturnModel
)
async def remove_follow(user_id: int, request: Request):
    """
    Route удаления подписки с пользователя
    :param user_id: Id пользователя
    :param request:
    :return:
    """
    current_user: Users = request.state.current_user
    following_user = await get_following_user(async_session, user_id)

    if following_user:
        if following_user.id not in [
            follower.id for follower in current_user.followed
        ]:
            return JSONResponse(
                status_code=403,
                content={"result": False, "msg": "This user is not followed"},
            )

        await remove_follow_db(async_session, current_user.id, user_id)
        return {"result": True}

    return JSONResponse(
        status_code=404,
        content={"result": False, "msg": "This user doesn't exist"},
    )


@router.get("/me", response_model=UserModel)
async def get_current_user(request: Request):
    """
    Route получения залогиненного пользователя
    :param request:
    :return:
    """
    current_user: Users = request.state.current_user
    return {
        "result": True,
        "user": {
            "id": current_user.id,
            "name": current_user.nickname,
            "followers": [
                {"id": follower.id, "name": follower.nickname}
                for follower in current_user.followers
            ],
            "following": [
                {"id": follower.id, "name": follower.nickname}
                for follower in current_user.followed
            ],
        },
    }


@router.get("/{user_id}", response_model=ReturnModelWithMsg | UserModel)
async def get_user_by_id(user_id: int):
    """
    Route получения пользователя по id
    :param user_id: Id пользователя
    :return:
    """
    user = await get_user(async_session, user_id)
    if user:
        return {
            "result": True,
            "user": {
                "id": user.id,
                "name": user.nickname,
                "followers": [
                    {"id": follower.id, "name": follower.nickname}
                    for follower in user.followers
                ],
                "following": [
                    {"id": follower.id, "name": follower.nickname}
                    for follower in user.followed
                ],
            },
        }
    return JSONResponse(
        status_code=404,
        content={"result": False, "msg": "This user doesn't exist"},
    )
