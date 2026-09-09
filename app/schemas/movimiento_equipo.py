from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MovimientoEquipoBase(BaseModel):
    id_equipo:int 
    id_contrato_origen:Optional[int]=None
    id_contrato_destino:Optional[int]=None
    tipo_movimiento:str #alta, cambio_ubicacion, baja, transferencia
    observaciones:Optional[str]=None

class MovimientoEquipoCreate(MovimientoEquipoBase):
    pass 

class MovimientoEquipoResponse(MovimientoEquipoBase):
    id:int
    fecha_movimiento: datetime

    class Config:
        from_attributes=True

