from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.cliente import (
    ClienteCreate,
    ClienteUpdate,
    ClienteResponse
)
from app.crud import cliente as crud_cliente

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("/", response_model=List[ClienteResponse])
def read_clientes(
    skip:int=0,
    limit:int=100,
    activo:Optional[bool]=None,
    db:Session=Depends(get_db)
):
    """ Obtener lista de clientes con paginación y filtro por estado """
    return crud_cliente.get_clientes(db, skip=skip, limit=limit, activo=activo)

@router.get("/{cliente_id}", response_model=Depends(get_db))
def read_cliente(cliente_id:int, db:Session=Depends(get_db)):
    """ Obtener un cliente por su ID """
    db_cliente = crud_cliente.get_cliente(db, cliente_id)
    if not db_cliente:
        raise HTTPException(
            status_code=status.HTTP_404,
            detail="Cliente no encontrado"
        )
    return db_cliente

@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(cliente:ClienteCreate, db:Session=Depends(get_db)):
    """ Crear un nuevo cliente """

    # Verificar si ya esta registrado el rfc
    if cliente.rfc:
        existing=crud_cliente.get_cliente_by_rfc(db, cliente.rfc)
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Cliente ya existe con ese RFC"
            )
        return crud_cliente.create_cliente(db,cliente)


@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(cliente_id, cliente_update:ClienteUpdate, db:Session=Depends(get_db)):
    """ Actualizar un cliente existente """

    db_cliente = crud_cliente.update_cliente(db, cliente_id, cliente_update)
    if not db_cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )
    return db_cliente

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(cliente_id:int, db:Session=Depends(get_db)):
    """ Eliminar un cliente (Borrado Físico )"""
    success = crud_cliente.delete_cliente(db, cliente_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )
    return None

