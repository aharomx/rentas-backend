from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# =============== RESPUESTA ===================
class AlertaResponse(BaseModel):
    id:int
    tipo:str
    prioridad:str 
    titulo:str 
    mensaje:Optional[str]=None
    referencia_tipo:Optional[str]=None
    referencia_id:Optional[int]=None
    estado:str 
    leida_por:Optional[int]=None
    fecha_lectura:Optional[datetime]=None
    atendida_por:Optional[int]=None
    fecha_atencion:Optional[datetime]=None
    observaciones:Optional[str]=None
    fecha_creacion:datetime
    fecha_actualizacion:datetime

    # Datos enriquecidos
    leida_por_nombre:Optional[str]=None
    atendida_por_nombre:Optional[str]=None

    class Config:
        from_attributes=True

# =============== RESUMEN (para listados) ==================
class AlertaResumenResponse(BaseModel):
    id:int
    tipo:str 
    prioridad:str 
    titulo:str 
    estado:str 
    referecia_tipo:Optional[str]=None
    referencia_id:Optional[int]=None
    fecha_creacion:datetime

    class Config:
        from_attributes=True

# ==================== ACCIONES =======================
class MarcarLeidaRequest(BaseModel):
    observaciones:Optional[str]=None

class AtenderAlertaRequest(BaseModel):
    observaciones:Optional[str]=None 

class DescartarAlertaRequest(BaseModel):
    motivo:str


# =================== RESULTADO DE GENERACION ===============
class GenerarAlertaResponse(BaseModel):
    """ Resultadodel proceso de generació de alertas """
    total_generadas:int
    total_admitidas_duplicadas:int 
    alertas_por_tipo:dict={}
    mensaje:str


# =============== RESUMEN PARA DASHBOARD ======================
class ResumenAlertasDashboard(BaseModel):
    total_nuevas:int 
    total_por_prioridad:dict={}
    total_por_tipo:dict={}
    ultimas_5:List[AlertaResumenResponse]=[]
