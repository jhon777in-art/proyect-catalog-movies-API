from pydantic import BaseModel, ConfigDict, Field


class Production(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    pais: str = Field(min_length=1)
    productora: str = Field(min_length=1)


class MovieCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1)
    director: str = Field(min_length=1)
    anio: int = Field(gt=1888, le=2100)
    duracion: int = Field(gt=0)
    genero: str = Field(min_length=1)
    clasificacion: str = Field(min_length=1)
    puntuacion: float = Field(ge=0, le=10)
    actores: list[str]
    produccion: Production


class MovieResponse(MovieCreate):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    id: str = Field(alias="_id")


class MovieUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str | None = Field(default=None, min_length=1)
    director: str | None = Field(default=None, min_length=1)
    anio: int | None = Field(default=None, gt=1888, le=2100)
    duracion: int | None = Field(default=None, gt=0)
    genero: str | None = Field(default=None, min_length=1)
    clasificacion: str | None = Field(default=None, min_length=1)
    puntuacion: float | None = Field(default=None, ge=0, le=10)
    actores: list[str] | None = None
    produccion: Production | None = None