from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.inventario_cliente import (
    InventarioClienteResponse,
    InventarioClienteUpdate,
    ResumenInventarioCliente
)
from app.crud import inventario_cliente as crud_inv
from app.security import get_current_user, require_roles


router=APIRouter(prefix="/inventario-cliente", tags=["Inventario por cliente"])

@router.get("/cliente/{cliente_id}", response_model=List[InventarioClienteResponse])
def read_inventario_clietne(
    cliente_id:int,
    estado:Optional[str]=None,
    id_articulo:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Listado de inventario en poder del cliente. """

    return crud_inv.get_inventario_by_cliente(
        db, cliente_id, estado=estado, id_articulo=id_articulo
    )


@router.get("/cliente/{cliente_id}/resumen", response_model=List[InventarioClienteResponse])
def read_inventario_por_solicitud(
    solicitud_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Inventario que entró al cliente por una solicitud específica """

    return crud_inv.get_inventario_by_solicitud(db,solicitud_id)


@router.get("/toner/{numero_serie}", response_model=InventarioClienteResponse)
def read_toner_by_serial(
    numero_serie:str,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Busca un tóner por número de serie (para saber en que cliente está) """

    db_item=crud_inv.get_toner_by_serial(db,numero_serie)
    if not db_item:
        raise HTTPException(
            status_code=404,
            detail="Tóner no econtrado en inventario del cliente"
        )

    return db_item


@router.get("/", response_model=List[InventarioClienteResponse])
def read_todos_toners(
    skip:int=0,
    limit:int=100,
    estado:Optional[str]=None,
    id_cliente:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Listado general de tóners en el sistema """

    return crud_inv.get_todos_los_toners(
        db,skip=skip, limit=limit,estado=estado,id_cliente=id_cliente
    )


@router.get("/pendientes-devolucion", response_model=List[InventarioClienteResponse])
def read_pendientes_devolucion(
    id_cliente:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Tóners que están en cliente y podrían devolverse """

    return crud_inv.get_toners_pendientes_devolucion(db, id_cliente=id_cliente)


@router.get("/{item_id}", response_model=InventarioClienteResponse)
def read_item(
    item_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_item=crud_inv.get_inventario_cliente(db, item_id)
    if not db_item:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado"
        )

    return db_item

@router.post("/{item_id}/marcar-devuelto", response_model=InventarioClienteResponse)
def marcar_devuelto(
    item_id:int,
    observaciones:Optional[str]=None,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","almacenista"]))
):
    """ Marcar un articulo ocmo devuelt """

    db_item=crud_inv.macarcar_como_devuelto(db, item_id, observaciones=observaciones)
    if not db_item:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado"
        )

    return db_item

router.post("/{item_id}/marcar-desecho")
def marcar_desecho(
        item_id:int,
        observaciones:Optional[str]=None,
        db:Session=Depends(get_db),
        current_user=Depends(require_roles(["superuser","admin","almacenista"]))
):

    db_item=crud_inv.marcar_como_desecho(db,item_id, observaciones=observaciones)
    if not db_item:
        raise HTTPException(
            status_code=404,
            detail="Item no encontrado"
        )

    return db_item
