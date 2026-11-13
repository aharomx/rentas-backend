from pydantic import BaseModel
from decimal import Decimal
from typing import Optional

class DetalleCobroEquipoBase(BaseModel):
    numero_serie:str
    modelo:Optional[str]=None
    es_color:bool=False
    tipo_lectura:str="contadores" # contadores | impresiones_directas


class DetalleCobroEquipoResponse(DetalleCobroEquipoBase):
    id:int
    id_documento:int 
    id_contrato_equipo:Optional[int]=None

    # Contadores
    contador_anterior_mono:Optional[int]=None 
    contador_actual_mono:Optional[int]=None
    contador_anterior_color:Optional[int]=None
    contador_actual_color:Optional[int]=None

    # Impresiones Directas
    impresiones_mes_mono:int=0
    impresiones_mes_color:int=0

    # Cargos
    renta_proporcional:Decimal=Decimal("0")
    cargo_click_mono:Decimal=Decimal("0")
    cargo_click_color:Decimal=Decimal("0")
    cargo_excedente_mono:Decimal=Decimal("0")
    cargo_excedente_color:Decimal=Decimal("0")
    subtotal_equipo:Decimal=Decimal("0")

    class Config:
        from_attributes=True

class DetalleCobroEquipoVistaPrevia(BaseModel):
    """ Detalle de equipo para vista previa (sin ID's de documento)"""
    id_contrato_equipo:Optional[int]=None

    numero_serie:str
    modelo:Optional[str]=None
    es_color:bool=False
    tipo_lectura:str="contadores"

    # Contadores
    contador_anterior_mono:Optional[int]=None
    contador_actual_mono:Optional[int]=None
    contador_anterior_color:Optional[int]=None
    contador_actual_color:Optional[int]=None

    # Impresiones directas
    impresiones_directas_mono:Optional[int]=None
    impresiones_directas_color:Optional[int]=None

    # Impresiones del mes
    impresiones_mes_mono:int=0
    impresiones_mes_color:int=0

    # Cargos
    renta_proporcional:Decimal=Decimal("0")
    cargo_click_mono:Decimal=Decimal("0")
    cargo_click_color:Decimal=Decimal("0")
    cargo_excedente_mono:Decimal=Decimal("0")
    cargo_excedente_color:Decimal=Decimal("0")
    subtotal_equipo:Decimal=Decimal("0")

    class Config:
        from_attributes=True

class DetalleCobroBolsaVistaPrevia(BaseModel):
    """ Detalle de bolsa para vista previa """

    tipo:str
    bolsa_total:int 
    impresiones_mes:int 
    excedente:int=0
    costo_unitario:Decimal=Decimal("0")
    cargo_excedente:Decimal=Decimal("0")

    class Config:
        from_attributes=True
    