from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.categoria_articulo import CategoriaArticuloResponse


class ArticuloBase(BaseModel):
    codigo:str 
    nombre:str 
    tipo:str # toner, refaccion, kit
    id_categoria:Optional[int]=None
    modelo_compatible:Optional[int]=None
    stock_minimo:int=5
    unidad_medida:str="PIEZA"


class ArticuloCreate(ArticuloBase):
    stock_actual:int=0 #solo para carga inicial


class ArticuloUpdate(BaseModel):
    codigo:Optional[str]=None
    nombre:Optional[str]=None
    tipo:Optional[str]=None
    id_categoria:Optional[int]=None
    modelo_compatible:Optional[int]=None
    stock_minimo:Optional[int]=None
    unidad_medida:Optional[str]=None
    activo:Optional[bool]=None

    # No se incluye el stock actual ya que solo se modifica por movimientos


class ArticuloResponse(ArticuloBase):
    id:int
    stock_actual:int 
    activo:bool
    fecha_alta:datetime 
    fecha_actualizacion:datetime

    #Datos enriquecidos
    categoria_nombre: Optional[str]=None
    modelo_nombre:Optional[str]=None

    # Indicador de stock bajo
    stock_bajo:bool=False

    class Config:
        from_attributes=True

