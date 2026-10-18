import re
from bson import ObjectId
from fastapi import APIRouter, HTTPException, status
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from core.config import MongoConfigurationError
from core.database import MongoConnectionError, get_movies_collection
from schemas.movie import MovieCreate, MovieResponse, MovieUpdate
from utils.mongo import (
    is_valid_object_id,
    serialize_mongo_document,
    serialize_mongo_documents,
)

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


@router.get(
    "",
    response_model=list[MovieResponse],
    status_code=status.HTTP_200_OK,
    summary="Listar todas las películas",
    description="Obtiene todas las películas registradas en el catálogo. Devuelve una lista vacía si no existen registros.",
    responses={
        200: {"description": "Lista de películas obtenida exitosamente."},
        500: {"description": "Error interno al consultar la base de datos."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def list_movies() -> list[MovieResponse]:
    try:
        collection = get_movies_collection()
        cursor = collection.find()
        documents = list(cursor)
        serialized = serialize_mongo_documents(documents)
        return [MovieResponse(**doc) for doc in serialized]
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
            detail="Error interno al consultar las películas.",
        ) from exc


@router.get(
    "/search",
    response_model=list[MovieResponse],
    status_code=status.HTTP_200_OK,
    summary="Buscar películas por título o director",
    description="Busca películas aplicando coincidencias parciales e insensibles a mayúsculas/minúsculas sobre el título o director. Se debe proporcionar al menos un parámetro.",
    responses={
        200: {"description": "Resultados de búsqueda obtenidos exitosamente."},
        400: {"description": "Parámetros de búsqueda inválidos o ausentes."},
        500: {"description": "Error interno al realizar la búsqueda."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def search_movies(
    title: str | None = None,
    director: str | None = None,
) -> list[MovieResponse]:
    clean_title = title.strip() if title and title.strip() else None
    clean_director = director.strip() if director and director.strip() else None

    if not clean_title and not clean_director:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos un parámetro de búsqueda ('title' o 'director') no vacío.",
        )

    criteria = []
    if clean_title:
        criteria.append(
            {"titulo": {"$regex": re.escape(clean_title), "$options": "i"}}
        )
    if clean_director:
        criteria.append(
            {"director": {"$regex": re.escape(clean_director), "$options": "i"}}
        )

    query = {"$or": criteria} if len(criteria) > 1 else criteria[0]

    try:
        collection = get_movies_collection()
        cursor = collection.find(query)
        documents = list(cursor)
        serialized = serialize_mongo_documents(documents)
        return [MovieResponse(**doc) for doc in serialized]
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
            detail="Error interno al buscar películas.",
        ) from exc


# ── F7 ────────────────────────────────────────────────────────────────────────


@router.get(
    "/filter/genre",
    response_model=list[MovieResponse],
    status_code=status.HTTP_200_OK,
    summary="Filtrar películas por género",
    description=(
        "Devuelve todas las películas cuyo campo `genero` coincida parcialmente "
        "con el valor indicado (insensible a mayúsculas/minúsculas). "
        "El parámetro `genre` es obligatorio y no puede estar vacío."
    ),
    responses={
        200: {"description": "Lista de películas con el género indicado."},
        400: {"description": "Parámetro 'genre' ausente o vacío."},
        500: {"description": "Error interno al filtrar películas."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def filter_by_genre(genre: str | None = None) -> list[MovieResponse]:
    clean_genre = genre.strip() if genre and genre.strip() else None
    if not clean_genre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'genre' es obligatorio y no puede estar vacío.",
        )
    try:
        collection = get_movies_collection()
        cursor = collection.find(
            {"genero": {"$regex": re.escape(clean_genre), "$options": "i"}}
        )
        documents = list(cursor)
        serialized = serialize_mongo_documents(documents)
        return [MovieResponse(**doc) for doc in serialized]
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
            detail="Error interno al filtrar películas por género.",
        ) from exc


# ── F8 ────────────────────────────────────────────────────────────────────────


@router.get(
    "/filter/classification",
    response_model=list[MovieResponse],
    status_code=status.HTTP_200_OK,
    summary="Filtrar películas por clasificación",
    description=(
        "Devuelve todas las películas cuyo campo `clasificacion` coincida exactamente "
        "con el valor indicado (coincidencia exacta, insensible a mayúsculas/minúsculas). "
        "El parámetro `classification` es obligatorio y no puede estar vacío ni contener "
        "únicamente espacios en blanco. "
        "Devuelve una lista vacía cuando no existen coincidencias."
    ),
    responses={
        200: {"description": "Lista de películas con la clasificación indicada (puede ser vacía)."},
        400: {"description": "Parámetro 'classification' ausente o vacío."},
        500: {"description": "Error interno al filtrar películas por clasificación."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def filter_by_classification(classification: str | None = None) -> list[MovieResponse]:
    clean_cls = classification.strip() if classification and classification.strip() else None
    if not clean_cls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'classification' es obligatorio y no puede estar vacío.",
        )
    try:
        collection = get_movies_collection()
        cursor = collection.find(
            {"clasificacion": {"$regex": f"^{re.escape(clean_cls)}$", "$options": "i"}}
        )
        documents = list(cursor)
        serialized = serialize_mongo_documents(documents)
        return [MovieResponse(**doc) for doc in serialized]
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
            detail="Error interno al filtrar películas por clasificación.",
        ) from exc


# ── F9 ────────────────────────────────────────────────────────────────────────


@router.get(
    "/filter/year",
    response_model=list[MovieResponse],
    status_code=status.HTTP_200_OK,
    summary="Filtrar películas por año de estreno",
    description=(
        "Devuelve todas las películas cuyo `anio` de estreno coincida exactamente "
        "con el valor entero indicado. El parámetro `year` es obligatorio; debe ser un "
        "entero entre 1888 y el año en curso (inclusive). Se rechazan valores negativos, "
        "cero y años futuros. Devuelve lista vacía si no hay coincidencias."
    ),
    responses={
        200: {"description": "Lista de películas del año indicado (puede ser vacía)."},
        400: {"description": "Parámetro 'year' ausente, negativo, cero o futuro."},
        500: {"description": "Error interno al filtrar películas por año."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def filter_by_year(year: int | None = None) -> list[MovieResponse]:
    from datetime import datetime

    if year is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'year' es obligatorio.",
        )
    current_year = datetime.now().year
    if year < 1888 or year > current_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El año debe estar entre 1888 y {current_year}.",
        )
    try:
        collection = get_movies_collection()
        cursor = collection.find({"anio": year})
        documents = list(cursor)
        serialized = serialize_mongo_documents(documents)
        return [MovieResponse(**doc) for doc in serialized]
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
            detail="Error interno al filtrar películas por año.",
        ) from exc


# ── F10 ───────────────────────────────────────────────────────────────────────


@router.get(
    "/filter/rating",
    response_model=list[MovieResponse],
    status_code=status.HTTP_200_OK,
    summary="Filtrar películas por puntuación",
    description=(
        "Devuelve todas las películas cuya `puntuacion` esté dentro del rango indicado. "
        "Se puede usar `min_rating`, `max_rating` o ambos simultáneamente; al menos uno "
        "es obligatorio. Ambos valores deben estar entre 0.0 y 10.0. "
        "Si se proporcionan ambos, `min_rating` no puede ser mayor que `max_rating`. "
        "Los valores límite se incluyen en los resultados (operadores $gte / $lte). "
        "Devuelve lista vacía si no hay coincidencias."
    ),
    responses={
        200: {"description": "Lista de películas dentro del rango de puntuación (puede ser vacía)."},
        400: {"description": "Parámetros ausentes, fuera de rango, o min_rating > max_rating."},
        500: {"description": "Error interno al filtrar películas por puntuación."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def filter_by_rating(
    min_rating: float | None = None,
    max_rating: float | None = None,
) -> list[MovieResponse]:
    if min_rating is None and max_rating is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos uno de los parámetros: 'min_rating' o 'max_rating'.",
        )
    if min_rating is not None and not (0.0 <= min_rating <= 10.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'min_rating' debe estar entre 0.0 y 10.0.",
        )
    if max_rating is not None and not (0.0 <= max_rating <= 10.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'max_rating' debe estar entre 0.0 y 10.0.",
        )
    if min_rating is not None and max_rating is not None and min_rating > max_rating:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El parámetro 'min_rating' no puede ser mayor que 'max_rating'.",
        )
    rating_filter: dict = {}
    if min_rating is not None:
        rating_filter["$gte"] = min_rating
    if max_rating is not None:
        rating_filter["$lte"] = max_rating
    try:
        collection = get_movies_collection()
        cursor = collection.find({"puntuacion": rating_filter})
        documents = list(cursor)
        serialized = serialize_mongo_documents(documents)
        return [MovieResponse(**doc) for doc in serialized]
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
            detail="Error interno al filtrar películas por puntuación.",
        ) from exc


# ── F3 ────────────────────────────────────────────────────────────────────────


@router.get(
    "/{movie_id}",
    response_model=MovieResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar película por identificador",
    description="Obtiene los detalles de una película específica a partir de su ObjectId.",
    responses={
        200: {"description": "Película encontrada exitosamente."},
        400: {"description": "Identificador de película inválido."},
        404: {"description": "Película no encontrada."},
        500: {"description": "Error interno al consultar la base de datos."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def get_movie(movie_id: str) -> MovieResponse:
    if not is_valid_object_id(movie_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de película inválido.",
        )
    try:
        collection = get_movies_collection()
        doc = collection.find_one({"_id": ObjectId(movie_id)})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Película no encontrada.",
            )
        serialized = serialize_mongo_document(doc)
        return MovieResponse(**serialized)
    except HTTPException:
        raise
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
            detail="Error interno al consultar la película.",
        ) from exc


@router.put(
    "/{movie_id}",
    response_model=MovieResponse,
    status_code=status.HTTP_200_OK,
    summary="Modificar una película",
    description="Actualiza uno o varios campos permitidos de una película existente en el catálogo.",
    responses={
        200: {"description": "Película actualizada exitosamente."},
        400: {"description": "Identificador de película inválido."},
        404: {"description": "Película no encontrada."},
        422: {"description": "Datos de entrada inválidos."},
        500: {"description": "Error interno al actualizar la película."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def update_movie(movie_id: str, movie_in: MovieUpdate) -> MovieResponse:
    if not is_valid_object_id(movie_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de película inválido.",
        )
    update_data = movie_in.model_dump(exclude_unset=True)
    update_data.pop("_id", None)
    update_data.pop("id", None)

    try:
        collection = get_movies_collection()
        oid = ObjectId(movie_id)
        if update_data:
            result = collection.update_one({"_id": oid}, {"$set": update_data})
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Película no encontrada.",
                )
        doc = collection.find_one({"_id": oid})
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Película no encontrada.",
            )
        serialized = serialize_mongo_document(doc)
        return MovieResponse(**serialized)
    except HTTPException:
        raise
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
            detail="Error interno al actualizar la película.",
        ) from exc


@router.delete(
    "/{movie_id}",
    status_code=status.HTTP_200_OK,
    summary="Eliminar una película",
    description="Elimina físicamente una película del catálogo a partir de su ObjectId.",
    responses={
        200: {"description": "Película eliminada exitosamente."},
        400: {"description": "Identificador de película inválido."},
        404: {"description": "Película no encontrada."},
        500: {"description": "Error interno al eliminar la película."},
        503: {"description": "Servicio de base de datos no disponible o tiempo de espera agotado."},
    },
)
def delete_movie(movie_id: str) -> dict[str, str]:
    if not is_valid_object_id(movie_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador de película inválido.",
        )
    try:
        collection = get_movies_collection()
        result = collection.delete_one({"_id": ObjectId(movie_id)})
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Película no encontrada.",
            )
        return {"message": "Película eliminada exitosamente.", "id": movie_id}
    except HTTPException:
        raise
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
            detail="Error interno al eliminar la película.",
        ) from exc