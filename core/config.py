import os

from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "").strip()
MONGODB_COLLECTION = "peliculas"


class MongoConfigurationError(RuntimeError):
    pass


def get_mongodb_config() -> tuple[str, str]:
    if not MONGODB_URI:
        raise MongoConfigurationError("La configuración de MongoDB está incompleta.")
    if not MONGODB_DATABASE:
        raise MongoConfigurationError("La configuración de MongoDB está incompleta.")
    return MONGODB_URI, MONGODB_DATABASE