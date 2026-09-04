from sqlalchemy.orm import Session
from app.models.equipo import Equipo
from app.schemas.equipo import (
    EquipoCreate,
    EquipoUpdate,
    EquipoResponse
)
from typing import List, Optional


def get_equipo(db: Session, equipo_id:int):
    return db.query(Equipo).filter(Equipo.id == equipo_id).first()


def get_equipo_by_serie(db:Session, numero_serie:str):
    return db.query(Equipo).filter(Equipo.numero_serie == numero_serie).first()


def get_equipos(db:Session, skip:int=0, limit:int=100, estado:Optional[str]=None):
    query = db.query(Equipo)
    if estado:
        query = query.filter(Equipo.estado == estado)
    return query.offset(skip).limit(limit).all()

def create_equipo(db:Session, equipo:EquipoCreate):
    db_equipo = Equipo(**equipo.model_dump())
    db.add(db_equipo)
    db.commit()
    db.refresh(db_equipo)
    return db_equipo

def update_equipo(db:Session, equipo_id:int, equipo_update:EquipoUpdate):
    db_equipo = get_equipo(db, equipo_id)
    if not db_equipo:
        return None
    for key, value in equipo_update.model_dump(exclude_unset=True).items():
        setattr(db_equipo, key, value)
    db.commit()
    db.refresh(db_equipo)
    return db_equipo

def delete_equipo(db:Session, equipo_id:int):
    db_equipo = get_equipo(db, equipo_id)
    if not db_equipo:
        return False
    db.delete(db_equipo)
    db.commit()
    return True

