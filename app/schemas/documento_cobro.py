from pydantic import BaseModel, Field
from datetime import datetime 
from decimal import Decimal
from typing import Optional, List
from app.schemas.detalle_cobro_equipo import DetalleCobroEquipoResponse
from app.schemas.detalle_cobro_bolsa import DetalleCobroBolsaResponse


# =============== GENERAR ============================
class GenerarDocumentoCobroRequest(BaseModel):
    """ Request para generar una remisión mensul """

    id_contrato:int 
    mes: int=Field(..., ge=1, le=12, description="Mes (1-12)")
    anio: int=Field(..., te=2020, le=2100, description="Año (YYYY)")
    descuento:Optional[Decimal]=Decimal("0")
    motivo_descuento:Optional[str]=None 
    observaciones:Optional[str]=None


# ============= VISTA PREVIA ==================
class VistaPreviaRequest(BaseModel):
    """ Request para calcular sin guardar (vista previa)"""

    id_contrato:int 
    mes:int=Field(..., ge=1, le=12)
    anio:int=Field(..., ge=2020, le=2100)
    descuento:Optional[Decimal]=Decimal("0")


# ============= ACTUALIZAR =====================
class DocumentoCobroUpdate(BaseModel):
    """ Solo se permite editar mientras está en borrador """

    descuento:Optional[Decimal]=None
    motivo_descuento:Optional[str]=None
    observaciones:Optional[str]=None


# ============== NOTAS =======================
class CrearNotaRequest(BaseModel):
    """ Request para crearuna nota de cargo o crédito """

    tipo:str=Field(..., description="nota_cargo | nota_credito")
    monto_ajuste:Decimal=Field(..., description="Positivo para cargo, negativo para crédito")
    observaciones: Optional[str]=None


# =============== RESPUESTA =======================
class DocumentoCobroResponse(BaseModel):

    id:int
    folio:str 
    tipo: str # remisio | nota_cargo | nota_credito
    id_documento_original: Optional[int]=None 

    id_contrato:int 
    id_cliente:int 

    mes:Optional[int]=None
    anio:Optional[int]=None
    periodo:Optional[str]=None

    fecha_emision:datetime 
    estado:str # borrador | emitido | cancelado

    monto_ajuste:Optional[Decimal]=None
    motivo_ajuste:Optional[str]=None
    autorizado_por:Optional[int]=None

    # Cálculos
    subtotal_renta:Decimal=Decimal("0")
    subtotal_clicks_mono:Decimal=Decimal("0")
    subtotal_clicks_color:Decimal=Decimal("0")
    subtotal_excedente_mono:Decimal=Decimal("0")
    subtotal_excedente_color:Decimal=Decimal("0")
    descuento:Decimal=Decimal("0")
    motivo_descuento:Optional[str]=None
    subtotal:Decimal=Decimal("0")
    iva:Decimal=Decimal("0")
    total:Decimal=Decimal("0")

    observaciones:Optional[str]=None
    generado_por:Optional[str]=None
    ruta_pdf:Optional[str]=None
    fecha_creadion:datetime

    # Datos enriquecidos
    cliente_nombre:Optional[str]=None
    cliente_rfc:Optional[str]=None
    contrato_numero:Optional[int]=None
    generador_nombre:Optional[str]=None
    autorizador:Optional[str]=None

    # Detalles
    detalles_equipos:List[DetalleCobroEquipoResponse]=[]
    detalles_bolsas:List[DetalleCobroBolsaResponse]=[]

    class Config:
        from_attributes=True

# ================== RESUMEN ======================
class DocumentoCobroResumenResponse(BaseModel):
    id:int 
    folio:str 
    estado:str 
    id_contrato:int 
    id_cliente:int 
    mes:Optional[int]=None
    anio:Optional[int]=None
    periodo:Optional[str]=None
    fecha_emision:datetime 
    total:Decimal=Decimal("0")
    cliente_nombre:Optional[str]=None
    contrato_numero:Optional[int]=None
    generador_nombre:Optional[str]=None

    class Config:
        from_attributes=True


# ================== VISTA PREVIO (respuesta sin guardar) =======================
class VistaPreviaResponse(BaseModel):
    """ Resultado del cálculo sin guardar BD. """

    id_contrato:int 
    id_cliente:int 
    mes:int 
    anio:int 
    periodo:str 

    # Datos enriquecidos
    cliente_nombre: Optional[str]=None
    cliente_rfc: Optional[str]=None
    contrato_numero: Optional[int]=None
    tipo_plan:Optional[str]=None

    # Cálculos
    subtotal_renta:Decimal=Decimal("0")
    subtotal_clicks_mono:Decimal=Decimal("0")
    subtotal_clicks_color:Decimal=Decimal("0")
    subtotal_excedente_mono:Decimal=Decimal("0")
    subtotal_excedente_color:Decimal=Decimal("0")
    descuento:Decimal=Decimal("0")
    subtotal:Decimal=Decimal("0")
    iva:Decimal=Decimal("0")
    total:Decimal=Decimal("0")

    # Advertencias
    advertencias:List[str]=[]
    equipos_sin_lectura:List[str]=[]

    # Detalles
    detalles_equipos:List[DetalleCobroEquipoResponse]=[]
    detalles_bolsas:List[DetalleCobroBolsaResponse]=[]
