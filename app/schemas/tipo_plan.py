from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TipoPlanBase(BaseModel):

    nombre:str # solo_renta, renta_click, renta_bolsa, solo_click
    descripcion: Optional[str]=None


class TipoPlanCreate(TipoPlanBase):
    pass 

class TipoPlanUpdate(BaseModel):

    nombre: Optional[str]=None
    descripcion: Optional[str]=None
    activo: Optional[bool]=None

class TipoPlanResponse(TipoPlanBase):
    id:int
    activo:bool
    fecha_alta: datetime

    class Config:
        from_attributes=True

