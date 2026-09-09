from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.schemas.equipo import EquipoResponse


# =========== CONTRATO EQUIPO ===================
class ContratoEquipoBase(BaseModel):
    id_equipo:int
    contador_inicial_contrato: int
    ubicacion: Optional[str]=None


class ContratoEquipoCreate(ContratoEquipoBase):
    pass

class ContratoEquipoResponse(ContratoEquipoBase):
    id:int
    id_contrato:int 
    fecha_ingreso:date 
    contador_actual:Optional[int]=None
    activo:bool 
    fecha_baja:Optional[date]=None
    equipo:Optional[EquipoResponse]=None

    class Config:
        from_attributes=True


# =========== CONTRATO ===================

class ContratoBase(BaseModel):
    id_cliente:int 
    id_tipo_plan:int 
    fecha_inicio:date 
    fecha_fin:date 
    costo_renta_mensual:Decimal=Decimal("0")
    costo_click_mono:Decimal=Decimal("0")
    costo_click_color:Decimal=Decimal("0")
    bolsa_mono:int=0
    bolsa_color:int=0
    costo_excedente_mono:Decimal=Decimal("0")
    costo_excedente_color:Decimal=Decimal("0")
    modo_captura:str="contadores"
    condiciones_especiales:Optional[str]=None
    observaciones:Optional[str]=None

class ContratoCreate(ContratoBase):
    equipos:List[ContratoEquipoCreate]=[]


class ContratoUpdate(BaseModel):
    id_tipo_plan:Optional[int]=None
    fecha_fin:Optional[date]=None
    activo:Optional[bool]=None
    costo_renta_mensual:Optional[Decimal]=None
    costo_click_mono:Optional[Decimal]=None
    costo_click_color:Optional[Decimal]=None
    costo_excedente_mono:Optional[Decimal]=None
    costo_excedente_color:Optional[Decimal]=None
    modo_captura:Optional[str]=None
    condiciones_especiales:Optional[str]=None
    observaciones:Optional[str]=None


class ContratoResponse(ContratoBase):
    id:int 
    activo:bool 
    fecha_creacion:datetime
    cliente_nombre:Optional[str]=None
    tipo_plan_nombre:Optional[str]=None
    equipos_asignados:List[ContratoEquipoResponse]

    class Config:
        from_attributes = True

