from backend.src.database.database import Base, async_session, engine
from backend.src.models.models import Users
from backend.src.routers import media, tweets, users
from fastapi import FastAPI

app = FastAPI()


@app.on_event("startup")
async def startapp():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        user = await session.get(Users, 1)
        await session.commit()
        if not user:
            async with session.begin():
                new_user = Users(name="test", nickname="test", api_key="test")
                session.add(new_user)
            session.commit()


# Для тестирования без front-end


# @app.middleware("http")
# async def add_process_time_header(request: Request, call_next):
#     new_headers = request.headers.mutablecopy()
#     new_headers["api-key"] = "test"
#     request._headers = new_headers
#     request.scope.update(headers=request.headers.raw)
#     response = await call_next(request)
#     return response


app.include_router(tweets.router)
app.include_router(media.router)
app.include_router(users.router)
