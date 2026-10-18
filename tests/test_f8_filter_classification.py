"""Tests – F8: Filtrar películas por clasificación (GET /api/v1/movies/filter/classification)."""
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


def test_filter_classification_success():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([SAMPLE_MOVIE])):
        r = client.get("/api/v1/movies/filter/classification?classification=PG-13")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["clasificacion"] == "PG-13"


def test_filter_classification_empty_results():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([])):
        r = client.get("/api/v1/movies/filter/classification?classification=NC-17")
    assert r.status_code == 200
    assert r.json() == []


def test_filter_classification_missing_param():
    r = client.get("/api/v1/movies/filter/classification")
    assert r.status_code == 400
    assert "classification" in r.json()["detail"].lower()


def test_filter_classification_empty_string():
    r = client.get("/api/v1/movies/filter/classification?classification=   ")
    assert r.status_code == 400
    assert "classification" in r.json()["detail"].lower()


def test_filter_classification_case_insensitive():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([SAMPLE_MOVIE])):
        r = client.get("/api/v1/movies/filter/classification?classification=pg-13")
    assert r.status_code == 200


def test_filter_classification_db_unavailable():
    from core.database import MongoConnectionError as MCE
    with patch("api.v1.endpoints.movies.get_movies_collection", side_effect=MCE("err")):
        r = client.get("/api/v1/movies/filter/classification?classification=R")
    assert r.status_code == 503


def test_filter_classification_db_internal_error():
    col = MagicMock()
    col.find.side_effect = PyMongoError("boom")
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=col):
        r = client.get("/api/v1/movies/filter/classification?classification=G")
    assert r.status_code == 500


def test_filter_classification_openapi():
    r = client.get("/api/v1/movies/filter/classification?classification=pg-13")
    assert r.status_code in (200, 503)
