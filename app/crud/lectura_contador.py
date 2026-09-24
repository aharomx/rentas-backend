from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date 
from sqlalchemy import extract
from app.models.lectura_contador import LecturaContador
from app.models.contrato_equipo import ContratoEquipo
from app.schemas.lectura_contador import LecturaContadorCreate, CorreccionLecturaRequest




def get_lectura(
        db:Session,
        lectura_id:int
)  -> Optional[LecturaContador]:

    return db.query(LecturaContador).filter(LecturaContador.id==lectura_id).first()

def get_lecturas(
        db:Session,
        skip:int=0,
        limit:int=100,
        id_contrato_equipo:Optional[int]=None,
        mes:Optional[int]=None,
        anio:Optional[int]=None
) -> List[LecturaContador]:

    query=db.query(LecturaContador)
    if id_contrato_equipo:
        query=query.filter(LecturaContador.id_contrato_equipo==id_contrato_equipo)

    if mes:
        query=query.filter(extract('month', LecturaContador.fecha_lectura)==mes)

    if anio:
        query=query.filter(extract('year', LecturaContador.fecha_lectura)==anio)

    return query.order_by(LecturaContador.fecha_lectura.desc()).offset(skip).limit(limit).all()


def get_lecturas_by_contratos(
    db: Session, 
    contrato_id: int, 
    mes: Optional[int] = None, 
    anio: Optional[int] = None
) -> List[LecturaContador]:

    query = db.query(LecturaContador).join(
            ContratoEquipo, LecturaContador.id_contrato_equipo == ContratoEquipo.id
        ).filter(ContratoEquipo.id_contrato == contrato_id)

    if mes:
        query=query.filter(extract('month',LecturaContador.fecha_lectura)==mes)

    if anio:
        query=query.filter(extract('year',LecturaContador.fecha_lectura)==anio)

    return query.order_by(LecturaContador.fecha_lectura.desc()).all()


def get_ultima_lectura(db:Session, contrato_equipo_id:int) -> Optional[LecturaContador]:
    """ Obtiene la última lectura de un contrato_equipo"""

    return db.query(LecturaContador).filter(
        LecturaContador.id_contrato_equipo==contrato_equipo_id
    ).order_by(LecturaContador.fecha_lectura.desc()).first()


def existe_lectura_en_fecha(db:Session, contrato_equipo_id:int, fecha:date) -> bool:
    """ Verifica si ya hay una lectura para ese contrato_equipo en ese mes """

    return db.query(LecturaContador).filter(
        LecturaContador.id_contrato_equipo==contrato_equipo_id,
        extract('month',LecturaContador.fecha_lectura)==fecha.month,
        extract('year',LecturaContador.fecha_lectura)==fecha.year
    ).first() is not None


def create_lectura(db:Session, lectura:LecturaContadorCreate, capturada_por_id:int) -> LecturaContador:
    """ Crea una nueva lectura de contador """

    ce=db.query(ContratoEquipo).filter(ContratoEquipo.id==lectura.id_contrato_equipo).first()

    if not ce:
        raise ValueError("Contrato-equipo no encontrado")

    # Verificar que no existe una lectura del mismo mes
    if existe_lectura_en_fecha(db, lectura.id_contrato_equipo, lectura.fecha_lectura):
        raise ValueError("Ya existe una lectura para este tipo en el mes especificado. Use corrección.")

    db_lectura=LecturaContador(
        id_contrato_equipo=lectura.id_contrato_equipo,
        id_orden_lectura=lectura.id_orden_lectura,
        fecha_lectura=lectura.fecha_lectura,
        tipo_lectura=lectura.tipo_lectura,
        contador_mono=lectura.contador_mono,
        contador_color=lectura.contador_color,
        impresiones_directas_mono=lectura.impresiones_directas_mono,
        impresiones_directas_color=lectura.impresiones_directas_color,
        porcentaje_toner_negro=lectura.porcentaje_toner_negro,
        porcentaje_toner_amarillo=lectura.porcentaje_toner_amarillo,
        porcentaje_toner_magenta=lectura.porcentaje_toner_magenta,
        porcentake_toner_cyan=lectura.porcentaje_toner_cyan,
        porcentaje_unidad_imagen=lectura.porcentaje_unidad_imagen,
        observaciones=lectura.observaciones,
        capturada_por=capturada_por_id
    )

    # Calcular impresiones del mes (solo si tipo es "contadores")
    if lectura.tipo_lectura=="contadores":
        contador_anterior=ce.contador_actual or ce.contador_inicial_contrato or 0

        db_lectura.contador_anterior_mono = contador_anterior

        if lectura.contador_mono is not None:
            if lectura.contador_mono < contador_anterior:
                raise ValueError(
                    f"El contador nuevo ({lectura.contador_mono}) no puede ser mayor"
                    f"al anterior ({contador_anterior})"
                )

            db_lectura.impresiones_mes_mono=lectura.contador_mono-contador_anterior
            ce.contador_actual=lectura.contador_mono

        if lectura.contador_color is not None:
            contador_color_anterior=ce.contador_color_actual or 0
            db_lectura.contador_anterior_color=contador_color_anterior
            if lectura.contador_color<contador_color_anterior:
                raise ValueError(
                    f"EL contador color nuevo ({lectura.contador_color}) no puede ser menor"
                    f"al anterior ({contador_color_anterior})"
                )
            db_lectura.impresiones_mes_color=lectura.contador_color-contador_color_anterior


    # Para tipo "impresiones_directas"
    elif lectura.tipo_lectura=="impresiones_directas":
        db_lectura.impresiones_mes_mono = lectura.impresiones_directas_mono or 0
        db_lectura.impresiones_mes_color = lectura.impresiones_directas_color or 0


    db.add(db_lectura)
    db.commit()
    db.refresh(db_lectura)
    return db_lectura

def corregir_lectura(
        db:Session,
        lectura_id:int,
        correcion:CorreccionLecturaRequest,
        capturada_por_id:int
) -> LecturaContador:
    """ Corrige una lectura existente creando una nueva con auditoría """

    lectura_original=get_lectura(db, lectura_id)
    if not lectura_original:
        raise ValueError("Lectura original no encontrada")

    # Crear una nueva lectura basada en la original
    nueva_lectura=LecturaContador(
        id_contrato_equipo=lectura_original.id_contrato_equipo,
        id_orden_lectura=lectura_original.id_orden_lectura,
        fecha_lectura=lectura_original.fecha_lectura,
        tipo_lectura=lectura_original.tipo_lectura,
        contador_mono=correcion.contador_mono or lectura_original.contador_mono,
        contador_color=correcion.contador_color or lectura_original.contador_color,
        impresiones_directas_mono=correcion.impresiones_directas_mono or lectura_original.impresines_directas_mono,
        impresiones_directas_color=correcion.impresiones_directas_color or lectura_original.impresiones_directas_color,
        porcentaje_toner_negro=correcion.porcentaje_toner_negro or lectura_original.porcentaje_toner_negro,
        porcentaje_toner_amarillo=correcion.porcentaje_toner_amarillo or lectura_original.porcentaje_toner_amarillo,
        porcentaje_toner_magenta=correcion.porcentaje_toner_magenta or lectura_original.porcentaje_toner_magenta,
        porcentaje_toner_cyan=correcion.porcentaje_toner_cyan or lectura_original.porcentaje_toner_cyan,
        porcentaje_unidad_imagen=correcion.porcentaje_unidad_imagen or lectura_original.porcentake_unidad_imagen,
        observaciones=correcion.observaciones or lectura_original.observaciones,
        capturada_por=capturada_por_id,
        es_correccion=True,
        lectura_original_id=lectura_id,
        motivo_correccion=correcion.motivo_correcion,
        contador_anterio_mono=lectura_original.contador_anterior_mono,
        contador_anterior_color=lectura_original.contador_anterior_color
    )

    # Recalcular impresiones
    if nueva_lectura.tipo_lectura=="contadores":
        if nueva_lectura.contador_mono and nueva_lectura.contador_anterior_mono:
            nueva_lectura.impresiones_mes_mono = nueva_lectura.contador_mono - nueva_lectura.contador_anterior_mono

        if nueva_lectura.contador_color and nueva_lectura.contador_anterior_color:
            nueva_lectura.impresiones_mes_color = nueva_lectura.contador_color - nueva_lectura.contador_anterior_color
    else:
        nueva_lectura.impresiones_mes_mono=nueva_lectura.impresines_directas_mono or 0
        nueva_lectura.impresiones_mes_color=nueva_lectura.impresiones_directas_color or 0

    db.add(nueva_lectura)
    db.commit()
    db.refresh(nueva_lectura)
    return nueva_lectura


def get_equipos_sin_lectura(
        db:Session,
        mes:int,
        anio:int
) -> List[ContratoEquipo]:
    """ Obtiene equipos activos que no tienen lectura en el mes específico """

    from sqlalchemy import and_, not_, exists

    subquery=db.query(LecturaContador.id_contrato_equipo).filter(
        extract('month',LecturaContador.fecha_lectura)==mes,
        extract('year',LecturaContador.fecha_lectura)==anio
    ).subquery()

    return db.query(ContratoEquipo).filter(
        ContratoEquipo.activo==True,
        ContratoEquipo.id.in_(subquery)
    ).all()