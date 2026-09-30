from pydantic import BaseModel, Field
from typing import Optional


class MantenimientoRefaccionBase(BaseModel):
    id_articulo:int
    cantidad:int=Field(...,gt=0, description="Cantidad mayor a 0")
    numero_serie_toner:Optional[str]=None
    observaciones:Optional[str]=None



class MantenimientoRefaccionCreate(MantenimientoRefaccionBase):
    pass

class MantenimientoRefaccionUpdate(BaseModel):
    id_articulo:Optional[int]=None
    cantidad:Optional[int]=Field(None,gt=0)
    numero_serie_toner:Optional[str]=None
    observaciones:Optional[str]=None

class MantenimientoRefaccionResponse(MantenimientoRefaccionBase):
    id:int
    id_mantenimiento_equipo:int
    # Datos enriquecidos
    articulo_nombre:Optional[str]=None
    articulo_codigo:Optional[str]=None

    class Config:
        from_attributes=True

        

