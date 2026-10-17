from datetime import datetime
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class Production(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    pais: str = Field(min_length=1)
    productora: str = Field(min_length=1)


class MovieCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str = Field(min_length=1)
    director: str = Field(min_length=1)
    anio: int = Field(gt=1888)
    duracion: int = Field(gt=0)
    genero: str = Field(min_length=1)
    clasificacion: str = Field(min_length=1)
    puntuacion: float = Field(ge=0, le=10)
    actores: list[str]
    produccion: Production

    @field_validator("anio")
    @classmethod
    def validate_anio(cls, value: int) -> int:
        current_year = datetime.now().year
        if value < 1888 or value > current_year:
            raise ValueError(
                f"El año debe estar entre 1888 y el año actual ({current_year})."
            )
        return value

    @field_validator("actores")
    @classmethod
    def validate_actores(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("La lista de actores no puede estar vacía.")
        cleaned = []
        for actor in value:
            if not isinstance(actor, str) or not actor.strip():
                raise ValueError(
                    "Los nombres de los actores no pueden estar vacíos ni contener solo espacios."
                )
            cleaned.append(actor.strip())
        return cleaned


class MovieResponse(MovieCreate):
    model_config = ConfigDict(str_strip_whitespace=True, populate_by_name=True)

    id: str = Field(validation_alias=AliasChoices("id", "_id"))


class MovieUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    titulo: str | None = Field(default=None, min_length=1)
    director: str | None = Field(default=None, min_length=1)
    anio: int | None = Field(default=None, gt=1888)
    duracion: int | None = Field(default=None, gt=0)
    genero: str | None = Field(default=None, min_length=1)
    clasificacion: str | None = Field(default=None, min_length=1)
    puntuacion: float | None = Field(default=None, ge=0, le=10)
    actores: list[str] | None = None
    produccion: Production | None = None

    @field_validator("anio")
    @classmethod
    def validate_update_anio(cls, value: int | None) -> int | None:
        if value is not None:
            current_year = datetime.now().year
            if value < 1888 or value > current_year:
                raise ValueError(
                    f"El año debe estar entre 1888 y el año actual ({current_year})."
                )
        return value

    @field_validator("actores")
    @classmethod
    def validate_update_actores(cls, value: list[str] | None) -> list[str] | None:
        if value is not None:
            if not value:
                raise ValueError("La lista de actores no puede estar vacía.")
            cleaned = []
            for actor in value:
                if not isinstance(actor, str) or not actor.strip():
                    raise ValueError(
                        "Los nombres de los actores no pueden estar vacíos ni contener solo espacios."
                    )
                cleaned.append(actor.strip())
            return cleaned
        return value