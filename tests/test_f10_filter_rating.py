"""Tests – F10: Filtrar películas por calificación mínima (GET /api/v1/movies/filter/rating)."""
from unittest.mock import MagicMock, patch

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pymongo.errors import PyMongoError

from main import app

client = TestClient(app)

MOVIE_ID = str(ObjectId())
SAMPLE_MOVIE = {
    "_id": ObjectId(MOVIE_ID),
    "titulo": "Inception",
    "director": "Christopher Nolan",
    "anio": 2010,
    "genero": "Ciencia Ficción",
    "duracion": 148,
    "clasificacion": "PG-13",
    "puntuacion": 8.8,
    "actores": ["Leonardo DiCaprio"],
    "produccion": {"productora": "Warner Bros.", "pais": "EE.UU."},
}


def _mock_collection(docs: list) -> MagicMock:
    mock_cursor = MagicMock()
    mock_cursor.__iter__ = MagicMock(return_value=iter(docs))
    col = MagicMock()
    col.find.return_value = mock_cursor
    return col


def test_filter_rating_success():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([SAMPLE_MOVIE])):
        r = client.get("/api/v1/movies/filter/rating?min_rating=8.0")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["puntuacion"] >= 8.0


def test_filter_rating_empty_results():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([])):
        r = client.get("/api/v1/movies/filter/rating?min_rating=10.0")
    assert r.status_code == 200
    assert r.json() == []


def test_filter_rating_missing_param():
    r = client.get("/api/v1/movies/filter/rating")
    assert r.status_code == 400
    assert "min_rating" in r.json()["detail"].lower()


def test_filter_rating_below_minimum():
    r = client.get("/api/v1/movies/filter/rating?min_rating=-0.1")
    assert r.status_code == 400
    assert "0.0" in r.json()["detail"]


def test_filter_rating_above_maximum():
    r = client.get("/api/v1/movies/filter/rating?min_rating=10.1")
    assert r.status_code == 400
    assert "10.0" in r.json()["detail"]


def test_filter_rating_boundary_zero():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([SAMPLE_MOVIE])):
        r = client.get("/api/v1/movies/filter/rating?min_rating=0.0")
    assert r.status_code == 200


def test_filter_rating_boundary_ten():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([])):
        r = client.get("/api/v1/movies/filter/rating?min_rating=10.0")
    assert r.status_code == 200


def test_filter_rating_not_float():
    r = client.get("/api/v1/movies/filter/rating?min_rating=excellent")
    assert r.status_code == 422


def test_filter_rating_db_unavailable():
    from core.database import MongoConnectionError as MCE
    with patch("api.v1.endpoints.movies.get_movies_collection", side_effect=MCE("err")):
        r = client.get("/api/v1/movies/filter/rating?min_rating=7.0")
    assert r.status_code == 503


def test_filter_rating_db_internal_error():
    col = MagicMock()
    col.find.side_effect = PyMongoError("boom")
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=col):
        r = client.get("/api/v1/movies/filter/rating?min_rating=5.0")
    assert r.status_code == 500


def test_filter_rating_openapi():
    r = client.get("/api/v1/movies/filter/rating?min_rating=7.5")
    assert r.status_code in (200, 503)
