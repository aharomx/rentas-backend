from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.categoria_articulo import CategoriaArticulo
from app.schemas.categoria_articulo import CategoriaArticuloCreate,CategoriaArticuloUpdate


def get_categoria(db:Session,categori_id:int) -> Optional[CategoriaArticulo]:

    return db.query(CategoriaArticulo).filter(CategoriaArticulo.id==categori_id).first()

def get_categoria_by_nombre(db:Session,nombre:str) -> Optional[CategoriaArticulo]:

    return db.query(CategoriaArticulo).filter(CategoriaArticulo.nombre==nombre).first()

def get_categorias(
        db:Session,
        skip:int=0,
        limit:int=100,
        activo:Optional[bool]=None
) -> List[CategoriaArticulo]:

    query=db.query(CategoriaArticulo)
    if activo is not None:
        query=query.filter(CategoriaArticulo.activo==activo)

    return query.offset(skip).limit(limit).all()


def create_categoria(
        db:Session,
        categoria:CategoriaArticuloCreate
) -> List[CategoriaArticulo]:

    db_cat=CategoriaArticulo(**categoria.model_dump())
    db.add(db_cat)
    db.commit()
    db.refresh(db_cat)
    return db_cat


def update_categoria(
        db:Session,
        categoria_id:int,
        categoria_update:CategoriaArticuloUpdate
) -> Optional[CategoriaArticulo]:

    db_cat = get_categoria(db, categoria_id)
    if not db_cat:
        return None

    for key, value in categoria_update.model_dump(exclude_unset=True).items():
        setattr(db_cat,key,value)

    db.commit()
    db.refresh(db_cat)
    return db_cat


def delete_categoria(db:Session,categoria_id:int) ->bool:

    db_cat=get_categoria(db,categoria_id)
    if not db_cat:
        return False

    # Verificar que no tenga artículos
    if db_cat.articulos:
        raise ValueError ("No se puede eliminar la categoría porque tenía artículos asociados")

    db.delete(db_cat)
    db.commit()
    return True

