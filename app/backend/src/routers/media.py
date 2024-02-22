import os
import uuid

from backend.src.config_data.config import IMAGE_SAVE_PATH
from backend.src.database.database import async_session
from backend.src.database.utils import add_image
from backend.src.models.models import Image
from backend.src.models.schemas import MediaModel
from fastapi import APIRouter, UploadFile

router = APIRouter(
    prefix="/api/medias",
    tags=["media"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=MediaModel)
async def load_media(file: UploadFile):
    """
    Route сохранения картинки
    :param file: Файл картинки
    :return:
    """
    uuid_name = uuid.uuid4()
    file.filename = f"{uuid_name}.jpg"
    content = await file.read()
    new_image: Image = Image(image_name=uuid_name)
    await add_image(async_session, new_image)
    with open(os.path.join(IMAGE_SAVE_PATH, file.filename), "wb") as f:
        f.write(content)

    return {"result": True, "media_id": new_image.id}
