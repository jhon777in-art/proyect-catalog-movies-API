from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from core.config import (
    MONGODB_COLLECTION,
    MongoConfigurationError,
    get_mongodb_config,
)

_client: MongoClient | None = None


class MongoConnectionError(RuntimeError):
    pass


def get_client() -> MongoClient:
    global _client
    uri, _ = get_mongodb_config()
    if _client is None:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    return _client


def get_database() -> Database:
    _, database_name = get_mongodb_config()
    return get_client()[database_name]


def get_movies_collection() -> Collection:
    return get_database()[MONGODB_COLLECTION]


def check_database_connection() -> None:
    try:
        get_client().admin.command("ping")
    except MongoConfigurationError:
        raise
    except PyMongoError as exc:
        raise MongoConnectionError("MongoDB no está disponible.") from exc