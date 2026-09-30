from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.articulo import Articulo
from app.schemas.articulo import ArticuloCreate, ArticuloUpdate


def get_articulo(
        db:Session,
        articulo_id:int
) -> Optional[Articulo]:
    return db.query(Articulo).filter(Articulo.id==articulo_id).first()


def get_articulo_by_codigo(
        db:Session,
        codigo:str
) -> Optional[Articulo]:
    return db.query(Articulo).filter(Articulo.codigo==codigo).first()

def get_articulos(
        db:Session,
        skip:int=0,
        limit:int=100,
        tipo:Optional[str]=None
) -> Optional[Articulo]:

    query=db.query(Articulo)
    if tipo:
        query=query.filter(Articulo.tipo==tipo)

    return query.offset(skip).limit(limit).all()

def create_articulo(
        db:Session,
        articulo:ArticuloCreate
) -> Optional[Articulo]:

    db_articulo=Articulo(**articulo.model_dump())
    db.add(db_articulo)
    db.commit()
    db.refresh(db_articulo)
    return db_articulo

def update_articulo(
        db:Session,
        articulo_id:int,
        articulo_update:ArticuloUpdate
) -> Optional[Articulo]:

    db_articulo=get_articulo(db, articulo_id)
    if not db_articulo:
        return None

    for key, value in articulo_update.model_dump(exclude_unset=True).items():
        setattr(db_articulo,key,value)

    db.commit()
    db.refresh(db_articulo)
    return db_articulo

def delete_articulo(
        db:Session, 
        articulo_id:int
) -> bool:

    db_articulo=get_articulo(db,articulo_id)

    if not db_articulo:
        return False

    db.delete(db_articulo)
    db.commit()
    return True

