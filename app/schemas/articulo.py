from pydantic import BaseModel
from typing import Optional


class ArticuloBase(BaseModel):
    codigo:str
    nombre:str 
    tipo:Optional[str]=None # toner, refaccion, kit
    modelo_compatible:Optional[int]=None
    stock_minimo:int=3
    unidad_medida:str="PIEZA"


class ArticuloCreate(ArticuloBase):
    pass


class ArticuloUpdate(BaseModel):
    codigo:Optional[str]=None
    nombre:Optional[str]=None
    tipo:Optional[str]=None
    modelo_compatible:Optional[int]=None
    stock_minimo:Optional[int]=None
    unidad_medida:Optional[str]=None

class ArticuloResponse(ArticuloBase):
    id:int

    class Config:
        from_attributes=True
        