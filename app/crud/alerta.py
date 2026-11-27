
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from datetime import datetime
from typing import Optional, List, Dict, Any

from app.models.alerta import Alerta
from app.schemas.alerta import (
    MarcarLeidaRequest,
    AtenderAlertaRequest,
    DescartarAlertaRequest,
)

def get_alerta(db:Session, alerta_id:int) -> Optional[Alerta]:

    return db.query(Alerta).options(
        joinedload(Alerta.lector),
        joinedload(Alerta.atendio),
    ).filter(Alerta.id==alerta_id).first()


def get_alertas(
        db:Session,
        skip:int=0,
        limit:int=0,
        estado:Optional[str]=None,
        tipo:Optional[str]=None,
        prioridad:Optional[str]=None,
        referencia_tipo:Optional[str]=None,
        referencia_id:Optional[int]=None,
) -> List[Alerta]:

    query=db.query(Alerta).options(
        joinedload(Alerta.lector),
        joinedload(Alerta.atendio),
    )

    if estado:
        query=query.filter(Alerta.esta==estado)
    if tipo:
        query=query.filter(Alerta.tipo==tipo)
    if prioridad:
        query=query.filter(Alerta.prioridad==prioridad)
    if referencia_tipo:
        query=query.filter(Alerta.referencia_tipo==referencia_tipo)
    if referencia_id:
        query=query.filter(Alerta.referencia_id==referencia_id)

    return query.order_by(
        Alerta.fecha_creacion.desc()
    ).offset(skip).limt(limit).all()


def get_alertas_nuevas(db:Session, limit:int=50) -> List[Alerta]:
    """ Alertas nuevas (no leidas) """

    return db.query(Alerta).options(
        joinedload(Alerta.lector),
        joinedload(Alerta.atendio),
    ).filter(
        Alerta.estado=="nueva"
    ).order_by(
        Alerta.prioridad.desc(),
        Alerta.fecha_creacion.desc()
    ).limit(limit).all()


def get_resumen_dashboard(db:Session) -> Dict[str,Any]:
    """ Resumen de alertas para el dashboard """

    from sqlalchemy import func

    # Total de nuevas
    total_nuevas=db.query(func.count(Alerta.id)).filter(
        Alerta.estado=="nueva"
    ).scalar() or 0

    # Por prioridad
    por_prioridad=db.query(
        Alerta.prioridad,
        func.count(Alerta.id)
    ).filter(
        Alerta.estado=="nueva"
    ).group_by(Alerta.prioridad).all()

    totales_por_prioridad={p: 0 for p in ["alta", "media", "baja"]}
    for p, count in por_prioridad:
        totales_por_prioridad[p]=count

    # Por tipo
    por_tipo=db.query(
        Alerta.tipo,
        func.count(Alerta.id)
    ).filter(
        Alerta.estado=="nueva"
    ).group_by(Alerta.tipo).all()

    totales_por_tipo={t:count for t, count in por_tipo}

    # Últimas 5
    ultimas_5=db.query(Alerta).filter(
        Alerta.estado=="nueva"
    ).order_by(
        Alerta.fecha_creacion.desc()
    ).limit(5).all()

    return {
        "total_nuevas":total_nuevas,
        "total_por_prioridad":totales_por_prioridad,
        "total_por_tipo":totales_por_tipo,
        "ultimas_5":ultimas_5,
    }


def marcar_leida(
        db:Session,
        alerta_id:int,
        data:MarcarLeidaRequest,
        usuario_id:int,
) -> Optional[Alerta]:
    
    db_alerta=get_alerta(db, alerta_id)
    
    if not db_alerta:
        return None

    if db_alerta.estado != "nueva":
        raise ValueError(
            f"La alerta ya fue procesada (estado: {db_alerta.estado})"
        )

    db_alerta.estado="leida"
    db_alerta.leida_por=usuario_id
    db_alerta.fecha_lectura=datetime.now()

    if data.observaciones:
        db_alerta.observaciones=data.observaciones

    db.commit()
    db.refresh(db_alerta)
    return db_alerta


def atender_alerta(
        db:Session,
        alerta_id:int,
        data:AtenderAlertaRequest,
        usuario_id:int
) -> Optional[Alerta]:

    db_alerta=get_alerta(db, alerta_id)

    if not db_alerta:
        return None

    if db_alerta.estado in ["atendida","descartada"]:
        raise ValueError(
            f"La alerta ya fue procesada (estado: {db_alerta.estado})"
        )

    db_alerta.estado="atendida"
    db_alerta.atendida_por=usuario_id
    db_alerta.fecha_atencion=datetime.now()

    if data.observaciones:
        db_alerta.observaciones=data.observaciones

    db.commit()
    db.refresh(db_alerta)
    return db_alerta


def descartar_alerta(
        db:Session,
        alerta_id:int,
        data:DescartarAlertaRequest,
        usuario_id:int,
) -> Optional[Alerta]:

    db_alerta=get_alerta(db,alerta_id)

    if not db_alerta:
        return None

    if db_alerta.estad in ["atendida","descartada"]:
        raise ValueError(
            f"La alerta ya fue procesada (estado: {db_alerta.estado})"
        )

    db_alerta.estado="descartada"
    db_alerta.atendida_por=usuario_id
    db_alerta.fecha_atencion=datetime.now()
    db_alerta.observaciones=data.motivo

    db.commit()
    db.refresh(db_alerta)

    return db_alerta


def cerrar_alerta_automatica(
        db:Session,
        tipo:str,
        referencia_tipo:str,
        referencia_id:int,
) -> int:
    """ 
        Cerrar automáticamente las alertas de un objeto cuando la condición se resuleve.
        Útil para casos como: contrato renovado, stock repuesto, etc.
    """

    alertas=db.query(Alerta).filter(
        Alerta.tipo==tipo,
        Alerta.referencia_tipo==referencia_tipo,
        Alerta.estado.in_(["nueva","leida"]),
    ).all()

    for a in alertas:
        a.estado="atendida"
        a.fecha_atencion=datetime.now()
        a.observaciones=(
            (a.observaciones or "") + "\n[Auto] Condición resuelta automáticamente."
        ).strip()

    db.commit()
    return len(alertas)

