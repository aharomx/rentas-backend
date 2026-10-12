from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class SolicitudAlmacenDetalleBase(BaseModel):
    id_articulo:int
    cantidad:int=Field(...,gt=0,description="Cantidad mayor a 0")
    numero_serie_toner:Optional[str]=None
    observaciones:Optional[str]=None


class SolicitudAlmacenDetalleCreate(SolicitudAlmacenDetalleBase):
    pass


class SolicitudAlmacenDetalleUpdate(BaseModel):
    cantidad:Optional[int]=Field(None,gt=0)
    numero_serie_toner:Optional[str]=None
    observaciones:Optional[str]=None

    # No se puede cambiar un artículo una vez creado


class SolicitudAlmacenDetallResponse(SolicitudAlmacenDetalleBase):
    id:int
    id_solicitud:int
    estado: str # reservado | entregado | devuelto | desecho
    fecha_estado:datetime
    # Datos enriquecidos
    articulo_codigo:Optional[str]=None
    articulo_nombre:Optional[str]=None
    articulo_tipo:Optional[str]=None

    class Config:
        from_attributes=True


