from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date 
from app.models.orden_lectura import OrdenLectura
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.schemas.orden_lectura import OrdenLecturaCreate, OrdenLecturaUpdate


def get_orden(db:Session, orden_id:int) ->Optional[OrdenLectura]:

    return db.query(OrdenLectura).filter(OrdenLectura.id==orden_id).first()

def get_ordenes(
        db:Session,
        skip:int=0,
        limit:int=100,
        estado:Optional[str]=None,
        id_contrato:Optional[int]=None
) -> List[OrdenLectura]:

    query=db.query(OrdenLectura)
    if estado:
        query=query.filter(OrdenLectura.estado==estado)
    if id_contrato:
        query=query.filter(OrdenLectura.id_contrato==id_contrato)

    return query.order_by(OrdenLectura.fecha_generacion.desc()).offset(skip).limit(limit).all()


def create_orden(
        db:Session,
        orden:OrdenLecturaCreate,
        generada_por_id:int,
) -> OrdenLectura:

    db_orden = OrdenLectura(
        id_contrato=orden.id_contrato,
        fecha_limite=orden.fecha_limite,
        observaciones=orden.observaciones,
        generada_por=generada_por_id,
        estado="pendiente"
    )

    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    return db_orden


def update_orden(
        db:Session,
        orden_id:int,
        orden_update:OrdenLecturaUpdate
) -> Optional[OrdenLectura]:

    db_orden=get_orden(db, orden_id)
    if not db_orden:
        return None

    for key, value in orden_update.model_dump(exclude_unset=True).items():
        setattr(db_orden, key, value)

    db.commit()
    db.refresh(db_orden)
    return db_orden


def delete_orden(
        db:Session,
        orden_id:int
) -> bool:

    db_orden = get_orden(db, orden_id)
    if not db_orden:
        return False
    db.delete(db_orden)
    db.commit()
    return True


def verificar_completada(
        db:Session, 
        orden_id:int
) -> bool:
    """ Verificar si todos los equipos del contrato ya tienen lectura """

    from app.models.lectura_contador import LecturaContador

    db_orden = get_orden(db, orden_id)
    if not db_orden:
        return False

    # Equipos activos en el contrato
    equipos_activos = db.query(ContratoEquipo).filter(
        ContratoEquipo.id_contrato == db_orden.id_contrato,
        ContratoEquipo.activo == True
    ).all()

    # Equipos con lectura
    equipos_con_lectura=db.query(LecturaContador).filter(
        LecturaContador.id_orden_lectura==orden_id
    ).count()

    return equipos_con_lectura >= len(equipos_activos)


def marcar_completada(
        db:Session,
        orden_id:int,
) -> Optional[OrdenLectura]:

    from sqlalchemy.sql import func

    db_orden=get_orden(db, orden_id)
    if not db_orden:
        return None

    db_orden.estado="completado"
    db_orden.completada_en=func.now()
    db.commit()
    db.refresh(db_orden)
    return db_orden

