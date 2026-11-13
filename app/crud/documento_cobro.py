from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, extract, or_
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
        "tipo_lectura":"contadores",
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

    resultado["tipo_lectura"]=lectura_actual.tipo_lectura

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
            LecturaContador.id_contrato_equipo==ce.id,
            or_(
                extract('year', LecturaContador.fecha_lectura)<anio,
                and_(
                    extract('year',LecturaContador.fecha_lectura)==anio,
                    extract('month',LecturaContador.fecha_lectura)<mes
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

    if lectura_actual.contador_color is not None and cont_ant_color is not None:
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

    from app.models.equipo import Equipo

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

    tipo_plan_nombre = contrato.tipo_plan.nombre if contrato.tipo_plan else "solo_renta"

    # Verificar si hay renta por equipo (solo para costos diferenciados)
    hay_renta_por_equipo = (
        tipo_plan_nombre == "costo_diferenciado"
        and any(ce.costo_renta_equipo is not None for ce in equipos)
    ) 

    # Calcular por equipo
    detalles_equipos_data=[]
    equipos_impresiones=[]
    equipos_sin_lectura=[]
    advertencias=[]

    for ce in equipos:
        impresiones = _calcular_impresiones_equipo(db, ce, data.mes, data.anio)

        if impresiones["sin_lectura"]:
            equipos_sin_lectura.append(ce.equipo.numero_serie if ce.equipo else f"ID {ce.id_equipo}")

            advertencias.append(
                f"Equipo {ce.equipo.numero_serie if ce.equipo else ce.id_equipo}"
                f"no tiene lectura en {data.mes}/{data.anio}"
            )

        cargos = _calcular_cargo_equipo(
            ce,
            ce.contrato, 
            tipo_plan_nombre, 
            impresiones, 
            hay_renta_por_equipo,
        )

        equipos_impresiones.append(impresiones)

        detalles_equipos_data.append({
            "id_contrato_equipo":ce.id,
            "numero_serie":ce.equipo.numero_serie if ce.equipo else "",
            "modelo":ce.equipo.modelo.nombre_modelo if ce.equipo and ce.equipo.modelo else None,
            "es_color":ce.equipo.modelo.es_color if ce.equipo and ce.equipo.modelo else False,
            "tipo_lectura":impresiones["tipo_lectura"],

            # Contadores
            "contador_anterior_mono":impresiones["contador_anterior_mono"],
            "contador_actual_mono":impresiones["contador_actual_mono"],
            "contador_anterior_color":impresiones["contador_anterior_color"],
            "contador_actual_color":impresiones["contador_actual_color"],

            # Impresiones directas
            "impresiones_directas_mono":impresiones["impresiones_directas_mono"],
            "impresiones_directas_color":impresiones["impresiones_directas_color"],

            # Impresiones del mes
            "impresiones_mes_mono":impresiones["impresiones_mes_mono"],
            "impresiones_mes_color":impresiones["impresiones_mes_color"],

            # Cargos
            "renta_proporcional":cargos["renta_proporcional"],
            "cargo_click_mono":cargos["cargo_click_mono"],
            "cargo_click_color":cargos["cargo_click_color"],
            "cargo_excedente_mono":cargos["cargo_excedente_mono"],
            "cargo_excedente_color":cargos["cargo_excedente_color"],
            "subtotal_equipo":cargos["subtotal_equipo"],
        })

    # Calculer bolsas (Solo para plan renta_bolsa)
    bolsas_data=[]
    if tipo_plan_nombre == "renta_bolsa":
        bolsas_data = _calcular_bolsas(contrato, equipos_impresiones, [])

    # Totales
    subtotal_renta = sum(d["renta_proporcional"] for d in detalles_equipos_data)
    subtotal_clicks_mono = sum(d["cargo_click_mono"] for d in detalles_equipos_data)
    subtotal_clicks_color = sum(d["cargo_click_color"] for d in detalles_equipos_data)
    subtotal_excedente_mono = sum(b["cargo_excedente"] for b in bolsas_data if b["tipo"]=="mono")
    subtotal_excedente_color = sum(b["cargo_excedente"] for b in bolsas_data if b["tipo"]=="color" )

    descuento = Decimal(str(data.descuento or 0))

    subtotal_antes_iva = (
        subtotal_renta
        + subtotal_clicks_mono
        + subtotal_clicks_color
        + subtotal_excedente_mono
        + subtotal_excedente_color
        - descuento
    )

    iva = subtotal_antes_iva * Decimal(str(IVA_PORCENTAJE)) / Decimal("100")

    total = subtotal_antes_iva + iva

    # Periodo
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
             "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    periodo = f"{meses[data.mes - 1]} {data.anio}"

    return {
        "id_contrato": contrato.id,
        "id_cliente": contrato.id_cliente,
        "mes": data.mes,
        "anio": data.anio,
        "periodo": periodo,
        "cliente_nombre": contrato.cliente.razon_social if contrato.cliente else None,
        "cliente_rfc": contrato.cliente.rfc if contrato.cliente else None,
        "contrato_numero": contrato.id,
        "tipo_plan": tipo_plan_nombre,
        "subtotal_renta": subtotal_renta,
        "subtotal_clicks_mono": subtotal_clicks_mono,
        "subtotal_clicks_color": subtotal_clicks_color,
        "subtotal_excedente_mono": subtotal_excedente_mono,
        "subtotal_excedente_color": subtotal_excedente_color,
        "descuento": descuento,
        "subtotal": subtotal_antes_iva,
        "iva": iva,
        "total": total,
        "advertencias": advertencias,
        "equipos_sin_lectura": equipos_sin_lectura,
        "detalles_equipos": detalles_equipos_data,
        "detalles_bolsas": bolsas_data,
    }

# ================ GENERAR DOCUMENTO =============================

def generar_documento_cobro(
        db:Session,
        data: GenerarDocumentoCobroRequest,
        generado_por_id:int,
) -> DocumentoCobro:
    """ Ganera una remision mensual """

    # Verificar que no exista ya
    existente = db.query(DocumentoCobro).filter(
        DocumentoCobro.id_contrato == data.id_contrato,
        DocumentoCobro.mes == data.mes,
        DocumentoCobro.anio == data.anio,
        DocumentoCobro.tipo == "remision",
        DocumentoCobro.estado != "cancelado",
    ).first()

    if existente:
        raise ValueError(
            f"Ya existe una remisión para este contrato en {data.mes}/{data.anio}"
            f"folio: {existente.folio}. Elimínala o usa unanota de ajuste"
        )

    # Calcular vista previa
    vista = calcular_vista_previa(
        db,
        VistaPreviaRequest(
            id_contrato=data.id_contrato,
            mes=data.mes,
            anio=data.anio,
            descuento=data.descuento,
        )
    )

    # Generar folio
    folio = _generar_folio(db,"remision")

    # Crear documento
    db_doc = DocumentoCobro(
        folio=folio,
        tipo="remision",
        id_contrato=vista["id_contrato"],
        id_cliente=vista["id_cliente"],
        mes=data.mes,
        anio=data.anio,
        estado="borrador",
        subtotal_renta=vista["subtotal_renta"],
        subtotal_clicks_mono=vista["subtotal_clicks_mono"],
        subtotal_clicks_color=vista["subtotal_clicks_color"],
        subtotal_excedente_mono=vista["subtotal_excedente_mono"],
        subtotal_excedente_color=vista["subtotal_excedente_color"],
        descuento=vista["descuento"],
        motivo_descuento=data.motivo_descuento,
        subtotal=vista["subtotal"],
        iva=vista["iva"],
        total=vista["total"],
        observaciones=data.observaciones,
        generado_por=generado_por_id
    )
    db.add(db_doc)
    db.flush()

    # Crear detalles de equipos
    for det_data in vista["detalles_equipos"]:
        db_det = DetalleCobroEquipo(
            id_documento=db_doc.id,
            id_contrato_equipo=det_data["id_contrato_equipo"],
            numero_serie=det_data["numero_serie"],
            modelo=det_data["modelo"],
            es_color=det_data["es_color"],
            tipo_lectura=det_data["tipo_lectura"],
            contador_anterior_mono=det_data["contador_anterior_mono"],
            contador_actual_mono=det_data["contador_actual_mono"],
            contador_anterior_color=det_data["contador_anterior_color"],
            contador_actual_color=det_data["contador_actual_color"],
            impresiones_directas_mono=det_data["impresiones_directas_mono"],
            impresiones_directas_color=det_data["impresiones_directas_color"],
            impresiones_mes_mono=det_data["impresiones_mes_mono"],
            impresiones_mes_color=det_data["impresiones_mes_color"],
            renta_proporcional=det_data["renta_proporcional"],
            cargo_click_mono=det_data["cargo_click_mono"],
            cargo_click_color=det_data["cargo_click_color"],
            cargo_excedente_mono=det_data["cargo_excedente_mono"],
            cargo_excedente_color=det_data["cargo_excedente_color"],
            subtotal_equipo=det_data["subtotal_equipo"],
        )
        db.add(db_det)

    # Crear detalles de bolsas
    for bolsa_data in vista["detalle_bolsas"]:
        db_bolsa = DetalleCobroBolsa(
            id_documento=db_doc.id,
            tipo=bolsa_data["tipo"],
            bolsa_total=bolsa_data["bolsa_total"],
            impresiones_mes=bolsa_data["impresiones_mes"],
            excedente=bolsa_data["excedente"],
            costo_unitario=bolsa_data["costo_unitario"],
            cargo_excedente=bolsa_data["cargo_excedente"],
        )
        db.add(db_bolsa)

    db.commit()
    db.refresh(db_doc)
    return db_doc


# ===================== ACTUALIZAR ===============================
def update_documento(
        db:Session,
        documento_id:int,
        data:DocumentoCobroUpdate
) -> Optional[DocumentoCobro]:
    """ Actualiza un documento (solo si está en borrador)"""

    db_doc = get_documento(db, documento_id)
    if not db_doc:
        return None

    if db_doc.estado != "borrador":
        raise ValueError(f"No se puede editar un documento en estado '{db_doc.estado}' ")

    # Si se actualiza el descuento, recalcular
    if data.descuento is not None:
        db_doc.descuento = data.descuento
        db_doc.motivo_descuento = data.motivo_descuento

        # Recalcular subtotal, IVA y total
        subtotal_antes_iva = (
            db_doc.subtotal_renta
            + db_doc.subtotal_clicks_mono
            + db_doc.subtotal_clicks_color
            + db_doc.subtotal_excedente_mono
            + db_doc.subtotal_excedente_color
            - db_doc.descuento
        )
        db_doc.subtotal = subtotal_antes_iva
        db_doc.iva = subtotal_antes_iva * Decimal(str(IVA_PORCENTAJE))/Decimal("100")
        db_doc.tota = db_doc.subtotal + db_doc.iva

    if data.observaciones is not None:
        db_doc.observaciones = data.observaciones

    if data.motivo_descuento is not None:
        db_doc.motivo_descuento = data.motivo_descuento

    db.commit()
    db.refresh(db_doc)
    return db_doc 


# ====================== EMITIR / CANCELAR ========================

def emitir_documento(db:Session, documento_id:int) -> Optional[DocumentoCobro]:
    """ Camnio de estado de borrador a emitido """

    db_doc = get_documento(db, documento_id)
    if not db_doc:
        return None

    if db_doc.estado != "borrador":
        raise ValueError(f"No se puede emitir. Estado actual: '{db_doc.estado}' ")

    db_doc.estado = "emitido"
    db.commit()
    db.refresh(db_doc)
    return db_doc

def cancelar_documento(db:Session, documento_id:int) -> Optional[DocumentoCobro]:
    """ Cancela un documento (borrador o emitido)"""

    db_doc = get_documento(db, documento_id)
    if not db_doc:
        return None

    if db_doc.estado=="cancelado":
        raise ValueError("El documento ya está cancelado")

    db_doc.estado="cancelado"
    db.commit()
    db.refresh(db_doc)
    return db_doc

# ================= NOTAS DE CARGO / CRÉDITO ========================

def crear_nota(
        db:Session,
        documento_id:int,
        data:CrearNotaRequest,
        autorizado_por_id:int,
) -> DocumentoCobro:
    """ 
        Crea unanota de cargo o crédito asociada a un documento existente. 
        Solo admin/superuser pueden crear notas (validar en el router)
    """

    # Validar tipo
    if data.tipo not in ["nota_cargp","nota_credito"]:
        raise ValueError("Tipo inválido, Debe ser 'nota_cargo' o 'nota_credito' ")

    # Validar monto
    monto = Decimal(str(data.monto_ajuste))
    if data.tipo == "nota_cargo" and monto <= 0:
        raise ValueError("Nota de cargo debe tener monto positivo")
    if data.tipo == "nota_credito" and monto >= 0:
        raise ValueError("Nota de crédito debe tener monto negativo")

    # Buscar documento original
    documento_original = get_documento(db, documento_id)
    if not documento_original:
        raise ValueError("Solo se pueden crear notas a partir de remisiones")
    if documento_original.tipo != "remision":
        raise ValueError("Solo se pueden crear notas a partir de remisiones")
    if documento_original.estado == "cancelado":
        raise ValueError("No se puede crear nota a un documento cancelado")

    # Generar folio
    folio = _generar_folio(db, data.tipo)

    # Calcular valores de la nota
    monto_abs = abs(monto)
    subtotal_nota=monto_abs if data.tipo=="nota_cargo" else -monto_abs
    iva_nota = subtotal_nota * Decimal(str(IVA_PORCENTAJE)) / Decimal("100")
    total_nota = subtotal_nota + iva_nota

    # Crear nota
    db_nota = DocumentoCobro(
        folio=folio,
        tipo=data.tipo,
        id_documento_original=documento_original.id,
        id_contrato=documento_original.id_contrato,
        id_cliente=documento_original.id_cliente,
        mes=documento_original.mes,
        anio=documento_original.anio,
        estado="emitido", # Las notas nacen emitidas
        monto_ajuste=monto,
        motivo_ajuste=data.motivo_ajuste,
        autorizado_por=autorizado_por_id,
        subtota=subtotal_nota,
        observaciones=data.observaciones,
        generado_por=autorizado_por_id
    )
    db.add(db_nota)
    db.commit()
    db.refresh(db_nota)
    return db_nota

# =================== ELIMINAR =======================

def delete_documento(db:Session, documento_id:int) -> bool:
    """ Elimina un documento (solo si está en borrador) """

    db_doc = get_documento(db, documento_id)
    if not db_doc:
        return False

    if db_doc.estado != "borrador":
        raise ValueError(f"No se puede eliminar un documento en estado '{db_doc.estado}' ")

    db.delete(db_doc)
    db.commit()
    return True


# ======================= NOTAS POR DOCUMENTO =====================

def get_notas_por_documento(db:Session, documento_id:int) -> List[DocumentoCobro]:
    """ Obtiene todas las notas asociadas a un documento """

    return db.query(DocumentoCobro).options(
        joinedload(DocumentoCobro.generador),
        joinedload(DocumentoCobro.autorizador),
    ).filter(
        DocumentoCobro.id_documento_original == documento_id
    ).order_by(DocumentoCobro.fecha_emision.desc()).all()
