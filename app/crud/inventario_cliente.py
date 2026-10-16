from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from typing import Optional, List
from datetime import datetime

from app.models.inventario_cliente import InventarioCliente
from app.models.articulo import Articulo
from app.schemas.inventario_cliente import (
    InventarioClienteCreate,
    InventarioClienteUpdate
)

# =============== LECTURA =====================
def get_inventario_cliente(db:Session, item_id:int) -> Optional[InventarioCliente]:

    return db.query(InventarioCliente).options(
        joinedload(InventarioCliente.cliente),
        joinedload(InventarioCliente.articulo),
    ).filter(InventarioCliente.id==item_id).first()


def get_inventario_by_cliente(
        db:Session,
        id_cliente:int,
        estado:Optional[str]=None,
        id_articulo:Optional[int]=None,
) -> List[InventarioCliente]:
    """ Inventario de un cliente (opcionalmente filtrado)"""

    query=db.query(InventarioCliente).options(
        joinedload(InventarioCliente.articulo),
    ).filter(InventarioCliente.id_cliente==id_cliente)

    if estado:
        query=query.filter(InventarioCliente.estado==estado)
    if id_articulo:
        query=query.filter(InventarioCliente.id_articulo==id_articulo)

    return query.order_by(InventarioCliente.fecha_entrega.desc()).all()

def get_inventario_by_solicitud(
        db:Session,
        id_solicitud:int
) -> List[InventarioCliente]:
    """ Todo el inventario que entró al cliente por una solicitud específica """

    return db.query(InventarioCliente).options(
        joinedload(InventarioCliente.articulo),
    ).filter(
        InventarioCliente.id_solicitud_entrega==id_solicitud
    ).all()

def get_toner_by_serial(
        db:Session,
        numero_serie:str
) -> Optional[InventarioCliente]:
    """ Busca un tóner por número de serie (para saber dodne está) """

    return db.query(InventarioCliente).options(
        joinedload(InventarioCliente.cliente),
        joinedload(InventarioCliente.articulo),
    ).filter(
        InventarioCliente.numero_serie_toner==numero_serie
    ).order_by(InventarioCliente.fecha_entrega.desc()).first()


def get_resumen_por_cliente(db: Session, id_cliente: int) -> dict:
    """Resumen del inventario del cliente agrupado por artículo."""
    
    items = db.query(
        InventarioCliente.id_articulo,
        func.count(InventarioCliente.id).label("total"),
    ).filter(
        InventarioCliente.id_cliente == id_cliente,
        InventarioCliente.estado == "en_cliente",
    ).group_by(InventarioCliente.id_articulo).all()
    
    resultado = []
    total_articulos = 0
    
    for id_articulo, total in items:
        articulo = db.query(Articulo).filter(Articulo.id == id_articulo).first()
        resultado.append({
            "id_articulo": id_articulo,
            "articulo_codigo": articulo.codigo if articulo else None,
            "articulo_nombre": articulo.nombre if articulo else None,
            "articulo_tipo": articulo.tipo if articulo else None,
            "cantidad": total,
        })
        total_articulos += total
    
    return {
        "id_cliente": id_cliente,
        "total_articulos": total_articulos,
        "items": resultado,
    }

# ============= CREAR (uso interno desde solicitudes) ===============

def create_inventario_cliente(
        db:Session,
        data:InventarioCliente,
) -> InventarioCliente:
    """ Registra un artículo en el ministock del cliente """

    db_item=InventarioCliente(
        id_cliente=data.id_cliente,
        id_articulo=data.id_articulo,
        numero_serie_toner=data.numero_serie_toner,
        id_solicitud_entrega=data.id_solicitud_entrega,
        cantidad=data.cantidad,
        estado="en_cliente",
        observaciones=data.observaciones,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


# ======================= ACTUALIZAR ESTADO ======================

def macarcar_como_devuelto(
        db:Session,
        item_id:int,
        observaciones:Optional[str]=None
) -> Optional[InventarioCliente]:
    """ Marca un artículo como devuelto (regresa al almacén) """

    db_item=get_inventario_cliente(db, item_id)

    if not db_item:
        return None

    db_item.estado="devuelto"
    db_item.fecha_devolucion=datetime.now()
    if observaciones:
        db_item.observaciones=(
            (db_item.observaciones or "")+ f"\n[Devuelto] {observaciones}"
        ).strip()

    db.commit()
    db.refresh(db_item)
    return db_item


def marcar_como_desecho(
        db:Session,
        item_id:int,
        observaciones:Optional[str]=None
) -> Optional[InventarioCliente]:
    """ Marca un tóner vacío como desecho """

    db_item=get_inventario_cliente(db, item_id)

    if not db_item:
        return None

    db_item.estado="desecho"
    db_item.fecha_devolucion=datetime.now()
    if observaciones:
        db_item.observaciones=(
            (db_item.observaciones or "") + f"\n[Desecho] {observaciones}"
        ).strip()

    db.commit()
    db.refresh(db_item)
    return db_item



# =================== ACTUALIZAR GENERAL ===================

def update_inventario_cliente(
        db:Session,
        item_id:int,
        data:InventarioClienteUpdate,
) -> Optional[InventarioCliente]:
    
    db_item=get_inventario_cliente(db,item_id)

    if not db_item:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)
    return db_item


# ============== REPORTES ====================

def get_toners_pendientes_devolucion(
        db:Session,
        id_cliente:Optional[int]=None
) -> List[InventarioCliente]:
    """ Tóners que están en clietne y podrían devolverse(vacíos o por devolución) """

    query=db.query(InventarioCliente).options(
        joinedload(InventarioCliente.cliente),
        joinedload(InventarioCliente.articulo),
    ).filter(
        InventarioCliente.estado=="en_cliente",
        InventarioCliente.numero_serie_toner.isnot(None)
    )

    if id_cliente:
        query=query.filter(InventarioCliente.id_cliente==id_cliente)

    return query.order_by(InventarioCliente.fecha_entrega.asc()).all()


def get_todos_los_toners(
        db:Session,
        skip:int=0, 
        limit:int=100,
        estado:Optional[str]=None,
        id_cliente:Optional[int]=None,
) -> List[InventarioCliente]:
    """ Listado general de tóners en el sistema (con filtros)"""

    query=db.query(InventarioCliente).options(
        joinedload(InventarioCliente.cliente),
        joinedload(InventarioCliente.articulo),
    ).filter(
        InventarioCliente.numero_serie_toner.isnot(None),
    )

    if estado:
        query=query.filter(InventarioCliente.estado==estado)
    if id_cliente:
        query=query.filter(InventarioCliente.id_cliente==id_cliente)

    return query.order_by(InventarioCliente.fecha_entrega.desc()).offset(skip).limit(limit).all()



        