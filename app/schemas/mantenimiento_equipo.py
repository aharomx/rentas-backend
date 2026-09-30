from pydantic import BaseModel
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from app.schemas.mantenimiento_refaccion import (
    MantenimientoRefaccionCreate,
    MantenimientoRefaccionResponse,
)


class MantenimientoEquipoBase(BaseModel):
    id_equipo:int
    contador_mono:Optional[int]=None
    contador_color:Optional[int]=None
    porcentaje_toner_negro:Decimal[Decimal]=None
    porcentaje_toner_amarillo:Decimal[Decimal]=None
    porcentaje_toner_magenta:Decimal[Decimal]=None
    porcentaje_toner_cyan:Decimal[Decimal]=None
    porcentaje_unidad_imagen:Decimal[Decimal]=None
    trabajos_realizados:Optional[str]=None
    proximo_mantenimiento_fecha:Optional[date]=None
    proximo_mantenimiento_contador:Optional[int]=None


class MantenimientoEquipoCreate(MantenimientoEquipoBase):
    refacciones:Optional[List[MantenimientoRefaccionCreate]]=[]


class MantenimientoEquipoUpdate(BaseModel):
    contador_mono:Optional[int]=None
    contador_color:Optional[int]=None
    porcentaje_toner_negro:Decimal[Decimal]=None
    porcentaje_toner_amarillo:Decimal[Decimal]=None
    porcentaje_toner_magenta:Decimal[Decimal]=None
    porcentaje_toner_cyan:Decimal[Decimal]=None
    porcentaje_unidad_imagen:Decimal[Decimal]=None
    trabajos_realizados:Optional[str]=None
    observaciones:Optional[str]=None
    proximo_mantenimiento_fecha:Optional[date]=None
    proximo_mantenimiento_contador:Optional[int]=None

class MantenimientoEquipoResponse(MantenimientoEquipoBase):
    id:int
    id_mantenimiento:int
    fecha_registro:datetime
    # Datos enriquecidos
    equipo_serie:Optional[str]=None
    equipo_modelo:Optional[str]=None
    ubicacion:Optional[str]=None
    refacciones:List[MantenimientoRefaccionResponse]=[]

    class Config:
        from_attributes=True
