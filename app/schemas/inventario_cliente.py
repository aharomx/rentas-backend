from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class InventarioClienteBase(BaseModel):
    id_cliente:int
    id_articulo:int 
    numero_serie_toner:Optional[str]=None
    cantidad: int=1
    Observaciones:Optional[str]=None


class InventarioClienteCreate(InventarioClienteBase):
    id_solicitud:Optional[int]=None


class InventarioClienteUpdate(BaseModel):
    estado:Optional[str]=None
    Observaciones:Optional[str]=None


class InventarioClienteResponse(InventarioClienteBase):
    id:int 
    id_solictud_entrega:Optional[int]=None
    fecha_entrega:datetime
    estado:str # en_cliente | devuelto | desecho
    fecha_devolucion:Optional[datetime]=None

    # Datos enriquecidos
    cliente_nombre:Optional[str]=None
    articulo_codigo:Optional[str]=None
    articulo_nombre:Optional[str]=None
    articulo_tipo:Optional[str]=None

    class Config:
        from_attributes=True


# ================ RESUMEN POR CLIENTE ==================
class ResumenInventarioCliente(BaseModel):
    """ Resumen del inventario de un cliente agrupado por artículo """

    id_cliente:int
    cliente_nombre:Optional[str]=None
    total_articulos:int 
    items:list[dict]=[]


# =============== INVENTARIO POR TONER ================
class TonerEnCliente(BaseModel):
    """ Tóner específio en poder del cliente (por serial) """
    id:int 
    numero_serie_toner:str 
    articulo_codigo:Optional[str]=None
    articulo_nombre:Optional[str]=None
    fecha_entrega:datetime 
    estado:str 

    class Config:
        from_attributes=True

        