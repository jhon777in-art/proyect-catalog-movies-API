from fastapi import APIRouter

from api.v1.endpoints import movies

router = APIRouter()
router.include_router(movies.router, prefix="/movies", tags=["movies"])