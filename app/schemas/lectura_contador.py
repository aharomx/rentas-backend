from pydantic import BaseModel, Field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional


class LecturaContadorBase(BaseModel):
    id_contrato_equipo:int
    id_orden_lectura:Optional[int]=None
    fecha_lectura:date
    tipo_lectura:str="contadores" # contadores, impresiones_directas

    # Para tipo "contadores"
    contador_mono:Optional[int]=None
    contador_color:Optional[int]=None

    # Para tipo "impresiones_directas
    impresiones_directas_mono:Optional[int]=None
    impresiones_directas_color:Optional[int]=None

    # Porcentajes (Opcionales)
    porcentaje_toner_negro=Optional[Decimal]=None
    porcentaje_toner_amarillo=Optional[Decimal]=None
    porcentaje_toner_magenta=Optional[Decimal]=None
    porcentaje_toner_cyan=Optional[Decimal]=None
    porcentaje_unidad_imagen=Optional[Decimal]=None

    observaciones:Optional[str]=None


class LecturaContadorCreate(LecturaContadorBase):
    pass 


class LecturaContadorUpdate(BaseModel):
    contador_mono:Optional[int]=None
    contador_color:Optional[int]=None
    impresiones_directas_mono:Optional[int]=None
    impresiones_directas_color:Optional[int]=None
    porcentaje_toner_negro:Optional[Decimal]=None
    porcentaje_toner_amarillo:Optional[Decimal]=None
    porcentaje_toner_magenta:Optional[Decimal]=None
    porcentaje_toner_cyan:Optional[Decimal]=None
    porcentaje_unidad_imagen:Optional[Decimal]=None
    observaciones:Optional[str]=None


class LecturaContadorResponse[LecturaContadorBase]:
    id:int
    contador_anterior_mono:Optional[int]=None
    contador_anterior_color:Optional[int]=None
    impresiones_mes_mono:Optional[int]=None
    impresiones_color_mono:Optional[int]=None
    capturada_por:Optional[int]=None
    fecha_captura:datetime
    es_correccion:bool
    lectura_original_id:Optional[int]=None
    motivo_correccion:Optional[str]=None

    # Datos enriquecidos
    equipo_serie:Optional[str]=None
    equipo_modelo:Optional[str]=None
    ubicacion:Optional[str]=None

    class Config:
        from_attributes=True


class CorreccionLecturaRequest(BaseModel):
    """ Para corregir lectura existente """

    contador_mono:Optional[int]=None
    contador_color:Optional[int]=None
    impresiones_directas_mono:Optional[int]=None
    impresiones_directas_color:Optional[int]=None
    porcentaje_toner_negro:Optional[Decimal]=None
    porcentaje_toner_amarillo:Optional[Decimal]=None
    porcentaje_toner_magenta:Optional[Decimal]=None
    porcentaje_toner_cyan:Optional[Decimal]=None
    porcentaje_unidad_imagen:Optional[Decimal]=None
    observaciones:Optional[str]=None
    motivo_correcion:str

