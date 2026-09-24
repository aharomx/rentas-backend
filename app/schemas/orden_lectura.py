from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List


class OrdenLecturaBase(BaseModel):
    id_contrato:int
    fecha_limite:Optional[date]=None
    observaciones:Optional[str]=None

class OrdenLecturaCreate(OrdenLecturaBase):
    pass

class OrdenLecturaUpdate(BaseModel):
    estado:Optional[str]=None
    fecha_limite:Optional[date]=None
    observaciones:Optional[str]=None

class OrdenLecturaResponse(OrdenLecturaBase):
    id:int
    fecha_generacion:datetime
    estado:str
    generada_por:Optional[int]=None
    completada_en:Optional[datetime]=None

    # Datos enriquecidos

    cliente_nombre:Optional[str]=None
    contrato_numero:Optional[int]=None
    total_equipos:Optional[int]=None
    equipos_con_lectura:Optional[int]=None

    class Config:
        from_attributes=True

    