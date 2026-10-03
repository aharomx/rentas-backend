from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CategoriaArticuloBase(BaseModel):
    nombre:str
    descripcion:Optional[str]=None


class CategoriaArticuloCreate(CategoriaArticuloBase):
    pass


class CategoriaArticuloUpdate(BaseModel):
    nombre:Optional[str]=None
    descripcion:Optional[str]=None
    activo:Optional[bool]=None


class CategoriaArticuloResponse(CategoriaArticuloBase):
    id:int
    activo:bool
    fecha_alta:datetime


    class Config:
        from_attributes=True

