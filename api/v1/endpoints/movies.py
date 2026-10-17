from fastapi import APIRouter, HTTPException, status
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from core.config import MongoConfigurationError
from core.database import MongoConnectionError, get_movies_collection
from schemas.movie import MovieCreate, MovieResponse

router = APIRouter()


@router.post(
    "",
    response_model=MovieResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva película",
    description="Registra una nueva película en el catálogo y devuelve los datos con el identificador generado.",
    responses={
        201: {"description": "Película registrada exitosamente."},
        422: {"description": "Datos de entrada inválidos o incompletos."},
        500: {"description": "Error interno al procesar en la base de datos."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def create_movie(movie_in: MovieCreate) -> MovieResponse:
    try:
        collection = get_movies_collection()
        movie_dict = movie_in.model_dump()
        result = collection.insert_one(movie_dict)
        movie_dict["id"] = str(result.inserted_id)
        return MovieResponse(**movie_dict)
    except (
        MongoConfigurationError,
        MongoConnectionError,
        ConnectionFailure,
        ServerSelectionTimeoutError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MongoDB no está disponible.",
        ) from exc
    except PyMongoError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al registrar la película.",
        ) from exc