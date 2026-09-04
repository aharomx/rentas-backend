from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ModeloImpresoraBase(BaseModel):
    nombre_modelo: str
    es_color: bool = False
    velocidad_ppm = Optional[int] = None
    rendimiento_toner_negro = Optional[int] = None
    rendimiento_toner_color = Optional[int] = None


class ModeloImpresoraCreate(ModeloImpresoraBase):
    pass


class ModeloImpresoraUpdate(ModeloImpresoraBase):
    nombre_modelo: Optional[str] = None
    es_color: Optional[bool] = None
    velocidad_ppm: Optional[int] = None
    rendimiento_toner_negro: Optional[int] = None
    rendimiento_toner_color: Optional[int] = None


class ModeloImpresoraResponse(ModeloImpresoraBase):
    id:int
    fecha_alta: datetime

    class Config:
        from_attributes = True

        
