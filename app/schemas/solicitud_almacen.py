from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.schemas.solicitud_almacen_detalle import (
    SolicitudAlmacenDetalleCreate,
    SolicitudAlmacenDetallResponse
)



# ========== CREAR ==============
class SolcitudAlmacenBase(BaseModel):
    id_cliente:int
    id_contrato:Optional[int]=None
    tipo:str  # entrega | recoleccion
    chofer:Optional[str]=None
    observaciones:Optional[str]=None


class SolicitudAlmacenCreate(SolcitudAlmacenBase):
    detalle:List[SolicitudAlmacenDetalleCreate]


# ============ ACTUALIZAR ===================
class SolcitudAlmacenUpdate(BaseModel):
    chofer:Optional[str]=None
    observaciones:Optional[str]=None


# =========== ACCIONES DE ESTADO ==============
class AutorizarSolicitudRequest(BaseModel):
    observaciones:Optional[str]=None


class EntregarSolicitudRequest(BaseModel):
    """ Datos para marcar como entregado. Puede incluir devoluciones en el momento"""
    chofer:Optional[str]=None
    observaciones:Optional[str]=None
    #ID's de detalles que el cliente No se quedó(Se devuelven a almacén)
    ids_detalle_devueltos:Optional[List[int]]=[]
    motivo_devolucion:Optional[str]=None

class CompletarRecoleccionRequest(BaseModel):
    """ Datos para completar la recolección de vacíoc """
    observaciones:Optional[BaseModel]=None
    # Id´s de los detalles que efectivamente se recolectaron
    ids_detalle_recogidos:Optional[List[int]]=None

class DevolucionPosteriorRequest(BaseModel):
    """ Devolución posterior de una entrega completada """
    ids_detalle_devueltos:List[int]
    motivo_devolucion:str
    observaciones:Optional[str]=None

class CancelarSolicitudRequest(BaseModel):
    motivo_cancelacion:str


# ============= RESPUESTA =======================
class SolicitudAlmacenResponse(SolcitudAlmacenBase):
    id:int
    folio:str
    estado:str
    requiere_autorizacion:bool

    #Fechas
    fecha_solicitud:datetime
    fecha_entrega:Optional[datetime]=None
    fecha_recoleccion:Optional[datetime]=None
    fecha_creacion:datetime

    # Autorización
    autorizado_por:Optional[int]=None
    fecha_autorizacion:Optional[datetime]=None

    # Auditoria
    procesado_por:Optional[int]=None
    registrado_por:Optional[int]=None

    # Motivos
    motivo_cancelacion:Optional[str]=None

    # Datos enriquecidos
    cliente_nombre:Optional[str]=None
    contrato_numero:Optional[int]=None
    autorizador_nombre:Optional[str]=None
    procesador_nombre:Optional[str]=None
    registrador_nombre:Optional[str]=None
    total_articulos:Optional[int]=None

    # Detalle
    detalle:List[SolicitudAlmacenDetallResponse]=[]

    class Config:
        from_attributes=True


# ============ RESPuESTA RESUMIDA (para listados) ======================
class SolicitudAlmacenResumenResponse(BaseModel):
    id:int
    folio:str 
    tipo:str 
    estado:str 
    id_cliente:int 
    cliente_nombre:Optional[str]=None
    contrato_numero:Optional[int]=None
    fecha_solicitud:datetime
    fecha_entrega:Optional[datetime]=None
    fecha_recoleccion:Optional[datetime]=None
    total_articulos:Optional[int]=None
    chofer:Optional[str]=None

    class Config:
        from_attributes=True


# ============== REPORTES ======================
class ReporteDevolucionesItem(BaseModel):
    """ Item del reporte de devoluciones """
    id_solicitud:int
    folio:str
    tipo:str
    estado:str 
    id_cliente:int
    cliente_nombre:Optional[str]=None
    fecha_solicitud:datetime
    fecha_entrega:Optional[datetime]=None
    total_devueltas:int 
    detalle_devuelto:List[SolicitudAlmacenDetallResponse]=[]

    class Config:
        from_attributes=True


class ResumenDevoluciones(BaseModel):
    """ Resumen de devoluciones por periodo """
    total_parciales:int 
    total_totales:int 
    total_articlos_devueltos:int 
    devoluciones:List[ReporteDevolucionesItem]=[]

    
