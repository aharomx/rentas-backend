from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from app.models.articulo import Articulo
from app.models.categoria_articulo import CategoriaArticulo
from app.schemas.articulo import ArticuloCreate, ArticuloUpdate
from app.schemas.movimiento_almacen import MovimientoAlmacenCreate


def get_articulo(db:Session,articulo_id:int) -> Optional[Articulo]:

    return db.query(Articulo).options(
        joinedload(Articulo.categoria),
        joinedload(Articulo.modelo),
    ).filter(Articulo.id == articulo_id).first()


def get_articulo_by_codigo(db:Session,codigo:str) -> Optional[Articulo]:

    return db.query(Articulo).filter(Articulo.codigo == codigo).first()


def get_articulos(
        db:Session,
        skip:int=0,
        limit:int=100,
        tipo:Optional[str]=None,
        id_categoria:Optional[int]=None,
        activo:Optional[bool]=None,
        solo_stock_bajo:bool=False,
) -> List[Articulo]:

    query=db.query(Articulo).options(
        joinedload(Articulo.categoria),
        joinedload(Articulo.modelo),
    )

    if tipo:
        query=query.filter(Articulo.tipo==tipo)
    if id_categoria:
        query=query.filter(Articulo.categoria==id_categoria)
    if activo:
        query=query.filter(Articulo.activo==activo)
    if solo_stock_bajo:
        query=query.filter(Articulo.stock_actual <= Articulo.stock_minimo)


    return query.order_by(Articulo.nombre).offset(skip).limit(limit).all()


def create_articulo(
        db:Session,
        articulo:ArticuloCreate,
        creado_por_id:Optional[int]=None
) -> Articulo:
    
    """Crea un artículo. Si tiene stock inicial > 0, se genera un movimiento de entrada."""

    from app.crud import movimiento_almacen as crud_mov

    # Crear un articulo
    data=articulo.model_dump()
    stock_inicial = data.pop("stock_actual",0)

    db_articulo = Articulo(**data,stock_actual=0)
    db.add(db_articulo)
    db.flush()

    # Si hay stock inicial, crear moviemiento de entrada
    if stock_inicial > 0:
        crud_mov.create_mov(
            db,
            MovimientoAlmacenCreate(
                id_articulo=db_articulo.id,
                tipo="entrada",
                cantidad=stock_inicial,
                motivo="Stock inicial al crear artículo"
            ),
            registrado_por_id=creado_por_id,
        )
    else:
        db.commit()
        db.refresh(db_articulo)

    return db_articulo


def update_articulo(
        db:Session,
        articulo_id:int,
        articulo_update:ArticuloUpdate
) -> Optional[Articulo]:

    db_articulo=get_articulo(db,articulo_id)
    if not db_articulo:
        return None

    # No se puede modificar stock_actual desde aquí
    # Ese campo solo se modifica con un movimiento de almacén

    for key, value in articulo_update.model_dump(exclude_unset=True).items():

        setattr(db_articulo,key,value)

    db.commit()
    db.refresh(db_articulo)
    return db_articulo


def delete_articulo(db:Session, articulo_id:int) -> bool:

    db_articulo=get_articulo(db,articulo_id)
    if not db_articulo:
        return False

    # Verificar si tiene movimientos (no eliminar, solo desactivar)
    if db_articulo.movimientos:
        raise ValueError(
            "No se puede eliminar un artículo con movimientos."
            "Se puede desactivar ocn activo=False"
        )

    db.delete(db_articulo)
    db.commit()
    return True

