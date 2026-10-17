from fastapi import FastAPI, HTTPException

from api.v1.router import router as v1_router
from core.config import MongoConfigurationError
from core.database import MongoConnectionError, check_database_connection

app = FastAPI(
    title="Catálogo de Películas API",
    description=(
        "API REST para la gestión de un catálogo de películas utilizando "
        "FastAPI y MongoDB."
    ),
    version="1.0.0",
)
app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    try:
        check_database_connection()
    except MongoConfigurationError as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB no está configurado.",
        ) from exc
    except MongoConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail="MongoDB no está disponible.",
        ) from exc
    return {"status": "ok", "database": "connected"}