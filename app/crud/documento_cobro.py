from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, extract
from typing import Optional, List, Dict, Any
from datetime import datetime, date 
from decimal import Decimal

from app.models.documento_cobro import DocumentoCobro
from app.models.detalle_cobro_equipo import DetalleCobroEquipo
from app.models.detalle_cobro_bolsa import DetalleCobroBolsa
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.lectura_contador import LecturaContador
from app.schemas.documento_cobro import (
    GenerarDocumentoCobroRequest, VistaPreviaRequest,
    DocumentoCobroUpdate, CrearNotaRequest
)
from app.config.empresa import IVA_PORCENTAJE


# ==================== GENERACIÓN DEL FOLIO ======================

def _generar_folio(db:Session, tipo:str) -> str:
    """ Generer folio segun tipo : REM-2026-001, NCAR-2026-001, NCR-2026-001"""

    anio = datetime.now().year()
    prefijos= {
        "remision": "REM",
        "nota_cargo": "NCAR",
        "nota_credito": "NCR"
    }

    prefijo= f"{prefijos[tipo]}-{anio}-"

    ultimo = db.query(DocumentoCobro).filter(
        DocumentoCobro.folio.like(f"{prefijo}%")
    ).order_by(DocumentoCobro.folio.desc()).first()

    if ultimo:
        ultimo_num=int(ultimo.folio.split("-")[-1])
        nuevo_num=ultimo + 1
    else:
        ultimo_num = 1

    while db.query(DocumentoCobro).filter(DocumentoCobro.folio==folio).first():
        nuevo_num += 1
        folio = f"{prefijo}{nuevo_num:04d}"

    return folio


# ======================== LECTURA ========================

def get_documento(db:Session, document_id:int) -> Optional[DocumentoCobro]:

    return db.query(DocumentoCobro).options(
        joinedload(DocumentoCobro.detalles_equipos),
        joinedload(DocumentoCobro.detalles_bolsas),
        joinedload(DocumentoCobro.cliente),
        joinedload(DocumentoCobro.Contrato),
        joinedload(DocumentoCobro.generador),
        joinedload(DocumentoCobro.autorizador),
    ).filter(DocumentoCobro.id==document_id).first()

def get_documentos(
        db:Session,
        skip:int=0,
        limit:int=100,
        tipo:Optional[str]=None,
        estado:Optional[str]=None,
        id_contrato:Optional[int]=None,
        id_cliente:Optional[int]=None,
        mes:Optional[int]=None,
        anio:Optional[int]=None,
) -> List[DocumentoCobro]:

    query = db.query(DocumentoCobro).options(
        joinedload(DocumentoCobro.cliente),
        joinedload(DocumentoCobro.contrato),
        joinedload(DocumentoCobro.generador),
    )

    if tipo:
        query = query.filter(DocumentoCobro.tipo == tipo)
    if estado:
        query = query.filter(DocumentoCobro.estado==estado)
    if id_contrato:
        query = query.filter(DocumentoCobro.id_contrato==id_contrato)
    if id_cliente:
        query = query.filter(DocumentoCobro.id_cliente==id_cliente)
    if mes:
        query = query.filter(DocumentoCobro.mes == mes)
    if anio: 
        query = query.filter(DocumentoCobro.anio == anio)

    return query.order_by(DocumentoCobro.fecha_emision.desc()).offset(skip).limit(limit).all()


# ================== CÁLCULO DE IMPRESIONES DEL MES ============================

def _calcular_impresiones_equipo(
        db:Session,
        ce:ContratoEquipo,
        mes:int,
        anio:int,
) -> Dict[str, Any]:
    """ 
    Calcula las impresiones del mes para un contrato_equipo
    Retorna un Diccionario (Dict), con contadores, impresiones y tipo_lectura.
    """

    resultado={
        "tipo_lecturo":"contadores",
        "contador_anterior_mono":None,
        "contador_actual_mono":None,
        "contador_anterior_color":None,
        "contador_actual_color":None,
        "impresiones_directas_mono":None,
        "impresiones_directas_color":None,
        "impresiones_mes_mono":None,
        "impresiones_mes_color":None,
        "sin_lectura":False
    }

    # Buscar lectura del mes actual
    lectura_actual=db.query(LecturaContador).filter(
        LecturaContador.id_contrato_equipo==ce.id,
        extract('month',LecturaContador.fecha_lectura)==mes,
        extract('year',LecturaContador.fecha_lectura)==anio,
    ).order_by(LecturaContador.fecha_lectura.desc()).first()

    if not lectura_actual:
        resultado["sin_lectura"]=True
        return

    resultado["tipo_lecturo"]=lectura_actual.tipo_lectura

    if lectura_actual.tipo_lectura=="impresiones_directas":
        # Modo directo
        resultado["impresiones_directas_mono"] = lectura_actual.impresiones_directas_mono or 0
        resultado["impresiones_directas_color"] = lectura_actual.impresiones_directas_color or 0
        resultado["impresiones_mes_mono"] = lectura_actual.impresiones_mes_mono or 0
        resultado["impresiones_mes_color"] = lectura_actual.impresiones_mes_color or 0
    else:
        # Modo contadores
        # Contador anterior: buscar lectura del mes anterior
        lectura_anterior = db.query(LecturaContador).filter(
            LecturaContador.id == ce.id,
            ( extract('year',LecturaContador.fecha_lectura < anio) |
             (
                 (extract('year',LecturaContador.fecha_lectura) == anio) &
                 (extract('month',LecturaContador.fecha_lectura) < mes)
             )
            )
        ).order_by(LecturaContador.fecha_lectura.desc()).first()

    if lectura_anterior:
        cont_ant_mono=lectura_anterior.contador_mono
        cont_ant_color=lectura_anterior.contador_color
    else:
        # Fallback: usar contador inicial del contrato
        cont_ant_mono=ce.contador_inicial_mono or 0
        conta_ant_color=ce.contador_inicial_color or 0

    resultado["contador_anterior_mono"] = cont_ant_mono
    resultado["contador_anterior_color"] = cont_ant_color
    resultado["contador_actual_mono"] = lectura_actual.contador_mono
    resultado["contador_actual_color"] = lectura_actual.contador_color

    # Calcular impresiones
    if lectura_actual.contador_mono is not None and cont_ant_mono is not None:
        resultado["impresiones_mes_mono"] = max(0, lectura_actual.contador_mono - cont_ant_mono)

    if lectura_actual.contador_color is not None and conta_ant_color is not None:
        resultado["impresiones_mes_color"] = max(0, lectura_actual.contador_color - cont_ant_color)

    return resultado


# ================= CÁLCULO DE CARGOS POR EQUIPO =============================

def _calcular_cargo_equipo(
        ce:ContratoEquipo,
        contrato:Contrato,
        tipo_plan_nombre:str,
        impresiones:Dict[str,Any],
        hay_renta_por_equipo:bool
) -> Dict[str,Any]:
    """
        Calcula los cargos de un equipo según el tipo de plan. 
        Retorna un diccionario (dict), con renta_propocional, cargos y subtotal
    """

    imp_mono=impresiones["impresiones_mes_mono"]
    imp_color=impresiones["impresiones_mes_color"]
    es_color=ce.equipo.modelo.es_color if ce.equipo and ce.equipo.modelo else False 

    cargos={
        "renta_proporcional":Decimal("0"),
        "cargo_click_mono":Decimal("0"),
        "cargo_click_color":Decimal("0"),
        "cargo_excedente_mono":Decimal("0"),
        "cargo_excedente_color":Decimal("0"),
        "subtotal_equipo":Decimal("0"),
    }

    if tipo_plan_nombre=="solo_retna":
        # Solo renta (global)
        cargos["renta_proporcional"]=Decimal(str(contrato.costo_renta_mensual or 0))

    elif tipo_plan_nombre=="renta_click":
        # Renta + click (costos globales del contrato)
        if not hay_renta_por_equipo:
            cargos["cargo_click_mono"]=Decimal(str(contrato.costo_renta_mensual or 0))
            cargos["cargo_click_mono"]=Decimal(str(imp_mono))*Decimal(str(contrato.costo_click_mono or 0))
            cargos["cargo_click_color"]=Decimal(str(imp_color))*Decimal(str(contrato.costo_click_color or 0))

        if es_color:
            cargos["cargo_click_color"]=Decimal(str(imp_color))*Decimal(str(contrato.costo_click_color or 0))
                                                                        
                                                                        
    elif tipo_plan_nombre=="solo_click":
        # Solo clock (costos globales)
        cargos["cargo_click_mono"]=Decimal(str(imp_mono))*Decimal(str(contrato.costo_click_mono or 0))
        if es_color:
            cargos["cargo_click_color"]=Decimal(str(imp_color))*Decimal(str(contrato.costo_click_color or 0))

    elif tipo_plan_nombre=="renta_bolsa":
        # Renta + bolsa (se maneja a nivel contrato, no aquí)
        # la renta se cobra aquí

        if not hay_renta_por_equipo:
            cargos["renta_proporcional"]=Decimal(str(contrato.costo_renta_mensual or 0))
            # Los excedentes se calcula a nivel contrato (en otra función)
    
    elif tipo_plan_nombre=="costo_diferenciado":
        # Renta: por equipo o global
        if hay_renta_por_equipo:
            cargos["renta_proporcional"]=Decimal(str(ce.costo_renta_equipo or 0))
        else:
            cargos["renta_proporcional"]=Decimal(str(contrato.costo_renta_mensual or 0))

        # Click color (fallback al contrato)
        if es_color:
            costo_color=ce.costo_click_color_equipo if ce.costo_click_color_equipo is not NotImplemented else contrato.costo_click_color
            cargos["cargo_click_color"]=Decimal(str(imp_color))*Decimal(str(costo_color or 0))

    # Sub total del equipo
    cargos["subtotal_equipo"]=(
        cargos["renta_proporcional"]
        + cargos["cargo_click_mono"]
        + cargos["cargo_click_color"]
        + cargos["cargo_excedente_mono"]
        + cargos["cargo_excedente_color"]
    )

    return cargos 

# ===================  CÁLCULO DE BOLSAS (a nivel contrato) ==========================

def _calcular_bolsas(
        contrato:Contrato,
        equipos_impresiones:List[Dict[str, Any]],
        detalles_equipos:List[DetalleCobroEquipo],
) -> List[Dict[str, Any]]:

    """
        Calcula las bolsas de impresión a nivel contrato, 
        IMPORTANTE: las impresiones mono de os equipos de color también suman a la bolsa mono general
    """

    bolsas=[]

    # Sumar TODAS las impresiones mono (equipos mono + color)
    total_mono = sum(d["impresiones_mes_mono"] for d in equipos_impresiones)

    # Sumar TODAS las impresiones color (equipos color)
    total_color = sum(d["impresiones_mes_color"] for d in equipos_impresiones)

    # Bolsa mono
    bolsa_mono = contrato.bolsa_mono or 0
    excedente_mono = max(0, total_mono - bolsa_mono)
    costo_excedente_mono = Decimal(str(contrato.costo_excedente_mono or 0))

    bolsas.append({
        "tipo":"mono",
        "bolsa_total":bolsa_mono,
        "impresiones_mes": total_mono,
        "excedente": excedente_mono,
        "costo_unitario": costo_excedente_mono,
        "cargo_excedente": Decimal(str(excedente_mono))*costo_excedente_mono
    })

    # Bolsa Color
    if total_color > 0 or (contrato.bolsa_color or 0) > 0:
        bolsa_color = contrato.bolsa_color or  0
        excedente_color = max(0, total_color - bolsa_color)
        costo_excedente_color = Decimal(str(contrato.costo_excedente_color or 0))

        bolsas.append({
            "tipo":"color",
            "bolsa_total": bolsa_color,
            "impresiones_mes": total_color,
            "excedente": excedente_color,
            "costo_unitario": costo_excedente_color,
            "cargo_excedente":Decimal(str(excedente_color))*costo_excedente_color
        })

    return bolsas 

# ==================== VISTA PREVIA (sin guardar) =============================
def calcular_vista_previa(
        db:Session,
        data:VistaPreviaRequest,
) ->Dict[str, Any]:
    """ 
        Calcula el documento de cobro SIN guardar en BD, 
        Útil para que el usuaior revise antes de generar
    """

    contrato=db.query(Contrato).options(
        joinedload(Contrato.cliente),
        joinedload(Contrato.tipo_plan)
    ).filter(Contrato.id==data.id_contrato).first()

    if not contrato:
        raise ValueError("Contrato no encontrado")
    if not contrato.activo:
        raise ValueError("El contrato no está activo")

    # Obtener aquipos activos
    equipos=db.query(ContratoEquipo).options(
        joinedload(ContratoEquipo.equipo).joinedload(Equipo.modelo)
    ).filter(
        ContratoEquipo.id_contrato == contrato.id,
        ContratoEquipo.activo==True,
    ).all()

    if not equipos:
        raise ValueError("El contrato no tiene equipos activos")
