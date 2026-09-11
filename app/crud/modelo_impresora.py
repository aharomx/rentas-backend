from sqlalchemy.orm import Session
from app.models.modelo_impresora import ModeloImpresora
from app.schemas.modelo_impresora import (
    ModeloImpresoraCreate,
    ModeloImpresoraUpdate
)
from typing import List, Optional


def get_modelo(db: Session, modelo_id: int):
    return db.query(ModeloImpresora).filter(ModeloImpresora.id == modelo_id).first()


def get_modelo_by_name(db: Session, nombre:str):
    return db.query(ModeloImpresora).filter(ModeloImpresora.nombre_modelo == nombre).first()


def get_modelos(db:Session, skip:int=0, limit:int=100, es_color:Optional[bool]=None):
    query = db.query(ModeloImpresora)
    if es_color is not None:
        query = query.filter(ModeloImpresora.es_color == es_color)

    return query.offset(skip).limit(limit).all()

def create_modelo(db:Session, modelo:ModeloImpresoraCreate):
    db_modelo = ModeloImpresora(**modelo.model_dump())
    db.add(db_modelo)
    db.commit()
    db.refresh(db_modelo)
    return db_modelo

def update_model(db:Session, modelo_id:int, modelo_update:ModeloImpresoraUpdate):
    db_modelo = get_modelo(db,modelo_id)
    if not db_modelo:
        return None

    for key, value in modelo_update.model_dump(exclude_unset=True).items():
        setattr(db_modelo, key, value)

    db.commit()
    db.refresh(db_modelo)
    return db_modelo

def delete_modelo(db: Session, modelo_id:int):
    db_modelo = get_modelo(db, modelo_id)
    if not db_modelo:
        return False
    # Verificar si hay equipos asociados
    if db_modelo.equipos:
        return False # NO se puede eliminar si tiene equipos asignados
    db.delete(db_modelo)
    db.commit()
    return True
