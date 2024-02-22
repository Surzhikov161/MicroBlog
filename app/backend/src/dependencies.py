from backend.src.models.models import Users
from fastapi import HTTPException, Request


async def token_required(request: Request):
    api_token = request.headers.get("api-key", None)
    if api_token is None:
        raise HTTPException(
            status_code=400,
            detail={
                "result": False,
                "msg": "Valid api-token token is missing",
            },
        )
    current_user = await Users.get_by_token(api_token)
    if current_user is None:
        raise HTTPException(
            status_code=400,
            detail={
                "result": False,
                "msg": "Sorry. Wrong api-key token. This user does not exist.",
            },
        )
    request.state.current_user = current_user
    return request.state.current_user
