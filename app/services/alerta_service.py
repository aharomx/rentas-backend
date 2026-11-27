""" 
    Servicio de generación de alertas automáticas 
    Contiene la lógica para detectar situaciones que requieren atención
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List

from app.models.alerta import Alerta
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.equipo import Equipo    
from app.models.articulo import Articulo
from app.models.lectura_contador import LecturaContador
from app.models.documento_cobro import DocumentoCobro
from app.models.cliente import Cliente

def _existe_alerta_pendiente(
        db:Session, tipo:str, referencia_tipo:str, referencia_id:int
) -> bool:
    """ Verifica si ya existe una alerta pendiente para el mismo objeto """
    return db.query(Alerta).filter(
        Alerta.tipo==tipo,
        Alerta.referencia_tipo==referencia_tipo,
        Alerta.referencia_id==referencia_id,
        Alerta.estado.in_(["nueva","leida"]),
    ).first() is not None

def _crear_alerta(
        db:Session,
        tipo:str,
        prioridad:str,
        titulo:str, 
        mensaje:str,
        referencia_tipo:str, 
        referencia_id:int 
) -> Alerta:
    """ Crea una nueva alerta (asumiendo que no existe duplicado) """
    alerta=Alerta(
        tipo=tipo,
        prioridad=prioridad,
        titulo=titulo,
        mensaje=mensaje,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        estado="nueva",
    )
    db.add(alerta)
    return alerta

# =========================  ALERTA CONTRATOS POR VENCER ===================

def _generar_alertas_contratos_por_vencer(db:Session) -> Dict[str, int]:
    """ Generar alertas para contratos que vencen en los próximos 30 días """

    hoy = date.today()
    fecha_limite=hoy+timedelta(days=30)

    contratos = db.query(Contrato).filter(
        Contrato.activo==True,
        Contrato.fecha_fin >= hoy,
        Contrato.fecha_fin <= fecha_limite
    ).all()

    generadas=0
    omitidas=0

    for contrato in contratos:
        if _existe_alerta_pendiente(db, "contrato_por_vencer","contrato",contrato.id):
            omitidas += 1
            continue

        cliente=db.query(Cliente).filter(Cliente.id==contrato.id_cliente).first()
        dias_restantes=(contrato.fecha_fin - hoy).days 

        _crear_alerta(
            db,
            tipo="contrato_por_vencer",
            titulo=f"Contrato #{contrato.id} vence en {dias_restantes} días",
            mensaje=(
                f"El contrato del cliente '{cliente.razon_social if cliente else 'N/A'}'"
                f"vence el {contrato.fecha_fin.strftime('%d/%m/%Y')}.  "
                f"Es necesario renovarlo o dar de baja los equipos."
            ),
            referencia_tipo="contrato",
            referencia_id=contrato.id,
        )
        generadas += 1

    return {"generadas": generadas, "omitidas":omitidas}

# ======================= ALERTA: CONTRATOS VENCIDOS ======================

def _generar_alertas_contratos_vencidos(db:Session) -> Dict[str,Any]:
    """ Genera alerats par contratos vencidos que siguen activos """
    hoy=date.today()

    contratos=db.query(Contrato).filter(
        Contrato.activo==True,
        Contrato.fecha_fin<hoy,
    ).all()

    generadas = 0
    omitidas = 0

    for contrato in contratos:
        if _existe_alerta_pendiente(db,"contrato_vencido","contrato",contrato.id):
            omitidas += 1
            continue

        cliente=db.query(Cliente).filter(Cliente.id==contrato.cliente).first()

        dias_vencido=(hoy-contrato.fecha_fin).days

        _crear_alerta(
            db,
            tipo="contrato_vencido",
            titulo=f"Contrato #{contrato.id} vencido hace {dias_vencido} días",
            mensaje=(
                f"El contrato del cliente '{cliente.razon_social if cliente else 'N/A'}'"
                f"venció el {contrato.fecha_fin.strftime('%d/%m/%Y')} y sigue activo."
                f"Requiere renovación urgente."
            ),
            referencia_tipo="contrato",
            referencia_id=contrato.id,
        )
        generadas += 1

    return {"generadas":generadas, "omitidas":omitidas}

# =========================  ALERTA: STOCK BAJO =======================

def _generar_alertas_stock_bajo(db:Session) -> Dict[str,int]:
    """ Genera alertas para artículos con stock bajo o nulo """
    articulos=db.query(Articulo).filter(
        Articulo.activo==True,
        Articulo.stock_actual<=Articulo.stock_minimo,
    ).all()

    generadas=0
    omitidas=0

    for art in articulos:
        if _existe_alerta_pendiente(db,"stock_bajo","articulo",art.id):
            omitidas+=1
            continue

        faltante=art.stock_minimo-art.stock_actual
        prioridad="alta" if art.stock_actual == 0 else "media"

        _crear_alerta(
            db,
            tipo="stock_bajo",
            prioridad=prioridad,
            titulo=f"Stock {'AGOTADO' if art.stock_actual == 0 else 'bajo'}: {art.codigo}",
            mensaje=(
                f"El artículo '{art.nombre}' tiene stock actua de {art.stock_actual}"
                f"(mínimo: {art.stock_minimo}). Faltan {faltante} unidades."
                f"Es necesario registrar una entrada al almacén."
            ),
            referencia_tipo="articulo",
            referencia_id=art.id,
        )
        generadas += 1

    return {"generadas":generadas, "omitidas":omitidas}


# =================== ALERTA: TÓNER BAJO EN EQUIPOS============================

def _generar_alertas_toner_bajo(db:Session) -> Dict[str,int]:
    """ Generar alertas para equipos con % de tóner bajo (<20%) """
    # Busca la última lectura de cada contrato_equipo
    hoy=date.today()
    mes_actual=hoy.month
    anio_actua=hoy.year

    # Subquery: Última lectura por cotrato_equipo
    subq=db.query(
        LecturaContador.id_contrato_equipo,
        func.max(LecturaContador.fecha_lectura).label("max_fecha")
    ).group_by(LecturaContador.id_contrato_equipo).subquery()

    lecturas=db.query(LecturaContador).join(
        subq,
        and_(
            LecturaContador.id_contrato_equipo==subq.c.id_contrato_equipo,
            LecturaContador.fecha_lectura==subq.c.max_fecha,
        )
    ).all()

    generadas=0
    omitidas=0

    for lectura in lecturas:
        ce=db.query(ContratoEquipo).filter(
            ContratoEquipo.id==lectura.id_contrato_equipo
        ).first()

        if not ce or not ce.activo:
            continue

        # Verificar % de tóner
        toner_bajo=[]
        if lectura.porcentaje_toner_negro is not None and lectura.porcentaje_toner_negro<20:
            toner_bajo.append(f"Negro: {lectura.porcentaje_toner_negro}%")
        if lectura.porcentaje_toner_cyan is not None and lectura.porcentaje_toner_cyan<20:
            toner_bajo.append(f"Cyan: {lectura.porcentaje_toner_cyan}%")
        if lectura.porcentaje_toner_magenta is not None and lectura.porcentaje_toner_magenta<20:
            toner_bajo.append(f"Magenta: {lectura.porcentaje_toner_magenta}%")
        if lectura.porcentaje_toner_amarillo is not None and lectura.porcentaje_toner_amarillo <20:
            toner_bajo.append(f"Amarillo: {lectura.porcentaje_toner_amarillo}%")

        if not toner_bajo:
            continue

        if _existe_alerta_pendiente(db, "toner_bajo", "equipo". ce.id_equipo):
            omitidas += 1
            continue

        equipo_serie=ce.equipo.numero_serie if ce.equipo else f"ID {ce.id_equipo}"

        _crear_alerta(
            db,
            tipo="toner_bajo",
            prioridad="media",
            titulo=f"Tóner bajo en equipo {equipo_serie}",
            mensaje=(
                f"El equipo {equipo_serie} tiene niveles de tóner bajos: "
                f"{', '.join(toner_bajo)}. Considerar envío de tóner."
            ),
            referencia_tipo="equipo",
            referencia_id=ce.id_equipo,
        )
        generadas += 1

    return {"generadas":generadas, "omitidas":omitidas}

# ==================== ALERTA; EQUIPOS SIN LECTURA =========================

def _generar_alertas_equipos_sin_lectura(db:Session) -> Dict[str,int]:
    """ Genera alertas para equipos que no tienen lectura este mes """

    hoy=date.today()
    mes_actual=hoy.month
    anio_actual=hoy.year

    # Equipos activos en contratos
    equipos_activos=db.query(ContratoEquipo).filter(
        ContratoEquipo.activo==True
    ).all()

    generadas=0
    omitidas=0

    for ce in equipos_activos:
        # Verificar si tiene lectura este mes
        tiene_lectura=db.query(LecturaContador).filter(
            LecturaContador.id_contrato_equipo==ce.id,
            extract('month', LecturaContador.fecha_lectura)==mes_actual,
            extract('year', LecturaContador.fecha_lectura)==anio_actual,
        ).first() is not None

        if tiene_lectura:
            continue

        if _existe_alerta_pendiente(
            db,
            "equipo_sin_lectura",
            "contrato_equipo",
            ce.id,
        ):
            omitidas += 1
            continue

        equipo_serie = ce.equipo.numero_serie if ce.equipo else f"ID {ce.id_equipo}"

        _crear_alerta(
            db,
            tipo="equipo_sin_lectura",
            prioridad="media",
            titulo=f"Equipo {equipo_serie} sin lectura este mes",
            mensaje=(
                f"No se ha capturado la lectura del equipo {equipo_serie} "
                f"para el mes actua ({mes_actual}/{anio_actual}). "
                f"Es necesario realizar la toma de contadores."
            ),
            referencia_tipo="contrato-equipo",
            referencia_id=ce.id,
        )
        generadas += 1

    return {"generadas":generadas, "omitidas":omitidas}


# ==================== ALERTA: MANTENIMIENTO VENCIDO ==============

def _generar_alertas_mantenimiento_vencido(db:Session) -> Dict[str,int]:
    """ Genera alertas para equipos cuyo próximo mantenimiento ya pasó """

    hoy=date.today()

    equipos=db.query(Equipo).filter(
        Equipo.estado=="rentado",
        Equipo.proximo_mantenimiento_fecha.isnot(None),
        Equipo.proximo_mantenimiento_fecha < hoy,
    ).all()

    generadas=0
    omitidas=0

    for equipo in equipos:
        if _existe_alerta_pendiente(db,
                                    "mantenimiento_vencido",
                                    "equipo",
                                    equipo.id):
            omitidas += 1
            continue

        dias_vencido=(hoy - equipo.proximo_mantenimiento_fecha).days()

        _crear_alerta(
            db,
            tipo="mantenimiento_vencido",
            prioridad="media",
            titulo=f"Mantenimiento vencido en equipo {equipo.numero_serie}",
            mensaje=(
                f"El equipo {equipo.numero_serie} tenía programado mantenimiento"
                f"el {equipo.proximo_mantenimiento_fecha.strftime('%d/%m/%Y')} "
                f"(hace {dias_vencido} días). Programar mantenimiento preventivo."
            ),
            referencia_tipo="equipo",
            referencia_id=equipo.id
        )
        generadas += 1

    return {"generadas":generadas, "omitidas":omitidas}


# ===================== ALERTA: DOCUMENTO SIN PAGAR =======================

def _generar_alertas_documentos_sin_pagar(db:Session) -> Dict[str,int]:
    """ Genera alertas para documentos emitidos hace más de 30 días sin pagar. """

    hoy=date.today()
    fecha_limite= hoy - timedelta(days=30)

    documentos=db.query(DocumentoCobro).filter(
        DocumentoCobro.tipo=="remision",
        DocumentoCobro.estado=="emitido",
        func.date(DocumentoCobro.fecha_emision) <= fecha_limite,
    ).all()

    generadas=0
    omitidas=0

    for doc in documentos:
        if _existe_alerta_pendiente(
            db,
            "documentos_sin_pagar",
            "documento",
            doc.id
        ):
            omitidas += 1
            continue

        cliente=db.query(Cliente).filter(Cliente.id==doc.id_cliente).first()

        dias=(hoy - doc.fecha_emision.date()).days

        _crear_alerta(
            db,
            tipo="documento_sin_pagar",
            prioridad="media",
            titulo=f"Documento {doc.folio} sin pagar",
            mensaje=(
                f"El documento {doc.folio} del cliente "
                f"'{cliente.razon_social if cliente else 'N/A'}' "
                f"por ${doc.total:,.2f} lleva {dias} días sin pagar."
                f"Gestionar cobro."
            ),
            referencia_tipo="documento",
            referencia_id=doc.id,
        )
        generadas += 1

    return {"generadas":generadas, "omitidas":omitidas}

# ==================== FUNCIÓN PRINCIPAL ====================

def generar_todas_las_alertas(db:Session) -> Dict[str,Any]:
    """ 
        Ejecuta todos los generadores de alertas.
        Retorna el resumen del proceso.
    """
    resultados={
        "contratos_por_vencer":_generar_alertas_contratos_por_vencer(db),
        "contrato_vencido":_generar_alertas_contratos_vencidos(db),
        "stock_bajo":_generar_alertas_stock_bajo(db),
        "toner_bajo":_generar_alertas_toner_bajo(db),
        "equipo_sin_lectura":_generar_alertas_equipos_sin_lectura(db),
        "mantenimiento_vencido":_generar_alertas_mantenimiento_vencido(db),
        "documento_sin_pagar":_generar_alertas_documentos_sin_pagar(db),
    }

    db.commit()

    total_generadas=sum(r["generadas"] for r in resultados.values())
    total_omitidas=sum(r["omitidas"] for r in resultados.values())

    return {
        "total_generadas":total_generadas,
        "total_omitidas_duplicadas":total_omitidas,
        "detalle_por_tipo":resultados,
    }