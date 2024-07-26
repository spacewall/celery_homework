from cachetools import cached
from celery import Celery
from celery.result import AsyncResult
from dotenv import dotenv_values
from gridfs import GridFS
from pymongo import MongoClient
from bson.objectid import ObjectId

from upscale import upscale

POSTGRES_USER = dotenv_values(".env")["POSTGRES_USER"]
POSTGRES_PASSWORD = dotenv_values(".env")["POSTGRES_PASSWORD"]
POSTGRES_HOST = dotenv_values(".env")["POSTGRES_HOST"]
POSTGRES_PORT = dotenv_values(".env")["POSTGRES_PORT"]
POSTGRES_DB = dotenv_values(".env")["POSTGRES_DB"]

REDIS_HOST = dotenv_values(".env")["REDIS_HOST"]
REDIS_PORT = dotenv_values(".env")["REDIS_PORT"]
REDIS_DB = dotenv_values(".env")["REDIS_DB"]

MONGO_USER = dotenv_values(".env")["MONGO_USER"]
MONGO_PASSWORD = dotenv_values(".env")["MONGO_PASSWORD"]
MONGO_HOST = dotenv_values(".env")["MONGO_HOST"]
MONGO_PORT = dotenv_values(".env")["MONGO_PORT"]

POSTGRES_DSN = f"db+postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
REDIS_DSN = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
MONGO_DSN = f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/files?authSource=admin"

APP_NAME = dotenv_values(".env")["APP_NAME"]


celery_app = Celery(
    APP_NAME,
    broker=REDIS_DSN,
    backend=POSTGRES_DSN,
    broker_connection_retry_on_startup=True
)


def get_task(task_id: str) -> AsyncResult:
    return AsyncResult(task_id, app=celery_app)

@cached({})
def get_fs() -> GridFS:
    mongo = MongoClient(MONGO_DSN)
    return GridFS(mongo["files"])

@celery_app.task
def upscaler(image_id: str) -> str:
    files = get_fs()

    with files.get(ObjectId(image_id)) as file:
        format = f".{file.filename.split(".")[-1]}"

        upscaled_image = upscale(
            file.read(),
            format
        )
    
    return str(files.put(upscaled_image, filename=f"upscaled_{file.filename}"))
