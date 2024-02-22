import os

try:
    DATABASE_URI = os.environ["DATABASE_URI"]
except KeyError:
    DATABASE_URI = "postgresql+asyncpg://admin:admin@localhost/postgres"
IMAGE_SAVE_PATH = os.path.join("backend", "attachments")
IMAGE_PATH = "attachments/"
IMAGE_TYPE = ".jpg"
