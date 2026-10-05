from sqlalchemy.orm import Session, joinedload
from sqlalchemy import extract, func
from typing import Optional, List
from datetime import date

from app.models.movimiento_almacen import MovimientoAlmacen
from app.models.articulo import Articulo
from app.schemas.movimiento_almacen import MovimientoAlmacenCreate


# Definición de tipos y su efecto en el stock
TIPOS_SUMAN=["entrada","devolucion","ajuste_positivo"]
TIPOS_RESTAN=["salida","ajuste_negativo","desecho"]
TIPOS_VALIDOS= TIPOS_SUMAN + TIPOS_RESTAN


def get_movimiento(db:Session, movimiento_id:int) -> Optional[MovimientoAlmacen]:

    return db.query(MovimientoAlmacen).options(
        joinedload(MovimientoAlmacen.articulo),
        joinedload(MovimientoAlmacen.usuario),
    ).filter(MovimientoAlmacen.id==movimiento_id).first()


def get_movimientos(
        db:Session,
        skip:int=0,
        limit:int=100,
        id_articulo:Optional[int]=None,
        tipo:Optional[str]=None,
        mes:Optional[int]=None,
        anio:Optional[int]=None,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
) ->List[MovimientoAlmacen]:

    query=db.query(MovimientoAlmacen).options(
        joinedload(MovimientoAlmacen.articulo),
        joinedload(MovimientoAlmacen.usuario)
    )

    if id_articulo:
        query=query.filter(MovimientoAlmacen.id_articulo==id_articulo)
    if tipo:
        query=query.filter(MovimientoAlmacen.tipo==tipo)
    if mes:
        query=query.filter(extract('month',MovimientoAlmacen.fecha_movimiento)==mes)
    if anio:
        query=query.filter(extract('year',MovimientoAlmacen.fecha_movimiento)==anio)
    if fecha_inicio:
        query=query.filter(MovimientoAlmacen.fecha_movimiento>=fecha_inicio)
    if fecha_fin:
        query=query.filter(MovimientoAlmacen.fecha_movimiento<=fecha_fin)

    return query.order_by(MovimientoAlmacen.fecha_movimiento.desc()).offset(skip).limit(limit).all()


def create_movimiento(
        db:Session,
        data:MovimientoAlmacenCreate,
        registrado_por_id:Optional[int]=None,
) -> MovimientoAlmacen:
    """ Crea un moviemitno y actuliza el stock del artículo """

    # Validar tipo
    if data.tipo not in TIPOS_VALIDOS:
        raise ValueError(
            f"Tipo inválido: '{data.tipo}'."
            f"Tipos válidos: {', '.join(TIPOS_VALIDOS)}"
        )

    # Obtener el artículo (con lock para evitar race conditions )
    articulo=db.query(Articulo).filter(Articulo.id==data.id_articulo).with_for_update().first()

    if not articulo:
        raise ValueError("Articulo no encontrado")

    if not articulo.activo:
        raise ValueError(f"El artículo '{articulo.codigo}' está inactivo ")

    # Calcular nuevo stock
    stock_anterior = articulo.stock_actual or 0

    if data.tipo in TIPOS_SUMAN:
        stock_nuevo=stock_anterior + data.cantidad
    else: # tipos que restan
        stock_nuevo=stock_anterior-data.cantidad

        # validar que no quede negativo
        if stock_nuevo <=0:
            raise ValueError(
                f"Stock insuficiente. Stock actual: {stock_anterior},"
                f"intentando restar: {data.cantidad}"
            )

    # Crear el Movimiento
    db_mov=MovimientoAlmacen(
        id_articulo=data.id_articulo,
        tipo=data.tipo,
        cantidad=data.cantidad,
        numero_serie_toner=data.numero_serie_toner,
        stock_anterior=stock_anterior,
        stock_nuevo=stock_nuevo,
        motivo=data.motivo,
        referencia=data.referencia,
        id_solicitud_almacen=data.id_solicitud_almacen,
        id_mantenimiento=data.id_mantenimiento,
        observaciones=data.observaciones,
        registrado_por=registrado_por_id
    )
    db.add(db_mov)

    # Actualizar sotck del artículo
    articulo.stock_actual=stock_nuevo

    db.commit()
    db.refresh(db_mov)
    return db_mov


def get_kardex(
        db:Session,
        id_articulo:int,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
        skip:int=0,
        limit:int=500,
) -> List[MovimientoAlmacen]:
    """ Historial completo de movimientos de un artículo (kardex)."""

    return get_movimientos(
        db,
        id_articulo=id_articulo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        skip=skip,
        limit=limit
    )


def get_articulos_stock_bajo(db:Session) -> List[dict]:
    """ Articulos cuyo stock_actual es menor o igual al stock_minimo """

    articulos=db.query(Articulo).options(
        joinedload(Articulo.categoria),
    ).filter(
        Articulo.activo==True,
        Articulo.stock_actual <= Articulo.stock_minimo,
    ).order_by(Articulo.stock_actual.asc).all()

    return [
        {
            "id":a.codigo,
            "nombre":a.nombre,
            "tipo":a.tipo,
            "stock_actual":a.stock_actual,
            "stock_minimo":a.stock_minimo,
            "faltante":a.stock_minimo - a.stock_actual,
            "categoria_nombre":a.categoria.nombre if a.categoria else None
        }
        for a in articulos
    ]

def get_resumen_movimientos(
        db:Session,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
) -> dict:
    """ Resumen de movimientos en un periodo por tipo. """

    query=db.query(
        MovimientoAlmacen.tipo,
        func.count(MovimientoAlmacen.id).label("total"),
        func.sum(MovimientoAlmacen.cantidad).label("cantidad")
    )

    if fecha_inicio:
        query = query.filter(MovimientoAlmacen.fecha_movimiento >= fecha_inicio)

    if fecha_fin:
        query = query.filter(MovimientoAlmacen.fecha_movimiento <= fecha_fin)

    resultados=query.group_by(MovimientoAlmacen.tipo).all()

    resumen={tipo: 0 for tipo in TIPOS_VALIDOS}
    for tipo, _, cantidad in resultados:
        resumen[tipo]=cantidad or 0

    return resumen

