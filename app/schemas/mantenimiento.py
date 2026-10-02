from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional, List
from app.schemas.mantenimiento_equipo import (
    MantenimientoEquipoCreate,
    MantenimientoEquipoResponse
)

class MantenimientoBase(BaseModel):
    id_contrato:int
    tipo:str # preventivo | correctivo
    descripcion_problema:Optional[str]=None
    observaciones:Optional[str]=None
    fecha_programada:Optional[date]=None
    tecnico_asignado:Optional[int]=None


class MantenimientoCreate(MantenimientoBase):
    equipos:List[MantenimientoEquipoCreate]=[]


class MantenimientoUpdate(BaseModel):
    descripcion_problema:Optional[str]=None
    observaciones:Optional[str]=None
    fecha_programada:Optional[date]=None
    tecnico_asignado:Optional[int]=None


# ============= ACCIONES DE ESTADO ====================

class AutorizarMantenimientoRequest(BaseModel):
    observaciones:Optional[str]=None   

class IniciarMantenimientoRequest(BaseModel):
    tecnico_inicio:Optional[int] # Si no se manda usa el usuario actual

class CompletarMantenimientoRequest(BaseModel):
    observaciones:Optional[str]=None

class CancelarMantenimientoRequest(BaseModel):
    motivo_cancelacion:str

class EsperaRefaccionesRequest(BaseModel):
    motivo_espera:str


# ===== RESPUESTA COMPLETA =================
class MantenimientoResponse(MantenimientoBase):
    id: int
    folio: str
    estado: str

    # Autorización
    autorizado_por: Optional[int] = None
    fecha_autorizacion: Optional[datetime] = None

    # Técnicos
    tecnico_inicio: Optional[int] = None
    tecnico_fin: Optional[int] = None

    # Fechas
    fecha_solicitud: datetime
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    fecha_creacion: datetime
    fecha_actualizacion: datetime

    # Motivos
    motivo_cancelacion: Optional[str] = None
    motivo_espera: Optional[str] = None

    # Datos enriquecidos
    cliente_nombre: Optional[str] = None
    cliente_id: Optional[int] = None
    contrato_numero: Optional[int] = None
    autorizador_nombre: Optional[str] = None
    tecnico_asignado_nombre: Optional[str] = None
    tecnico_inicio_nombre: Optional[str] = None
    tecnico_fin_nombre: Optional[str] = None

    # Relaciones
    equipos: List[MantenimientoEquipoResponse] = []

    class Config:
        from_attributes = True


# ============== RESPUESTA RESUMIDA PARA REPORTES ======================
class MantenimientoResumenResponse(BaseModel):
    id:int
    folio:str
    id_contrato:int 
    tipo:str 
    estado:str 
    fecha_solicitud:datetime
    fecha_programada:Optional[date]=None
    fecha_fin:Optional[date]=None
    total_equipos:Optional[int]=None
    cliente_nombre:Optional[str]=None
    tecnico_asignado_nombre:Optional[str]=None

    class Config:
        from_attributes=True

        