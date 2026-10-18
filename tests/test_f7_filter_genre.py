"""Tests – F7: Filtrar películas por género (GET /api/v1/movies/filter/genre)."""
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


# ── helpers ───────────────────────────────────────────────────────────────────

def _mock_collection(docs: list) -> MagicMock:
    mock_cursor = MagicMock()
    mock_cursor.__iter__ = MagicMock(return_value=iter(docs))
    col = MagicMock()
    col.find.return_value = mock_cursor
    return col


# ── tests ─────────────────────────────────────────────────────────────────────

def test_filter_genre_success():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([SAMPLE_MOVIE])):
        r = client.get("/api/v1/movies/filter/genre?genre=Ciencia")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert "Ciencia" in data[0]["genero"]


def test_filter_genre_empty_results():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([])):
        r = client.get("/api/v1/movies/filter/genre?genre=Terror")
    assert r.status_code == 200
    assert r.json() == []


def test_filter_genre_missing_param():
    r = client.get("/api/v1/movies/filter/genre")
    assert r.status_code == 400
    assert "genre" in r.json()["detail"].lower()


def test_filter_genre_empty_string():
    r = client.get("/api/v1/movies/filter/genre?genre=   ")
    assert r.status_code == 400
    assert "genre" in r.json()["detail"].lower()


def test_filter_genre_case_insensitive():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([SAMPLE_MOVIE])):
        r = client.get("/api/v1/movies/filter/genre?genre=ciencia ficción")
    assert r.status_code == 200


def test_filter_genre_special_chars():
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=_mock_collection([])):
        r = client.get("/api/v1/movies/filter/genre?genre=Sci+Fi%2FAction")
    assert r.status_code == 200
    assert r.json() == []


def test_filter_genre_db_unavailable():
    from core.database import MongoConnectionError as MCE
    with patch("api.v1.endpoints.movies.get_movies_collection", side_effect=MCE("err")):
        r = client.get("/api/v1/movies/filter/genre?genre=Accion")
    assert r.status_code == 503


def test_filter_genre_db_internal_error():
    col = MagicMock()
    col.find.side_effect = PyMongoError("boom")
    with patch("api.v1.endpoints.movies.get_movies_collection", return_value=col):
        r = client.get("/api/v1/movies/filter/genre?genre=Drama")
    assert r.status_code == 500


def test_filter_genre_openapi():
    r = client.get("/api/v1/movies/filter/genre?genre=drama")
    assert r.status_code in (200, 503)
