from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.cliente import (
    ClienteCreate, ClienteUpdate, ClienteResponse,
    DireccionCreate, DireccionResponse,
    ContactoCreate, ContactoResponse
)
from app.crud import cliente as crud_cliente
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# ========== CLIENTES ==========
@router.get("/", response_model=List[ClienteResponse])
def read_clientes(
    skip: int = 0,
    limit: int = 100,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    return crud_cliente.get_clientes(db, skip=skip, limit=limit, activo=activo)

@router.get("/{cliente_id}", response_model=ClienteResponse)
def read_cliente(
    cliente_id:int, 
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    db_cliente = crud_cliente.get_cliente(db, cliente_id)

    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db_cliente


@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def create_cliente(
    cliente:ClienteCreate, 
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin", "coordinador"]))
):
    if cliente.rfc:
        existing = crud_cliente.get_cliente_by_rfc(db, cliente.rfc)
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe un cliente con este RFC")
    return crud_cliente.create_cliente(db, cliente)


@router.put("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(
    cliente_id: int, 
    cliente_update: ClienteUpdate, 
    db: Session = Depends(get_db),
    get_current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    db_cliente = crud_cliente.update_cliente(db, cliente_id, cliente_update)
    if not db_cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return db_cliente

@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cliente(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))):
    success = crud_cliente.delete_cliente(db, cliente_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return None

# ========== DIRECCIONES ==========
@router.get("/{cliente_id}/direcciones", response_model=List[DireccionResponse])
def read_direcciones(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return crud_cliente.get_direcciones_by_cliente(db, cliente_id)

@router.post("/{cliente_id}/direcciones", response_model=DireccionResponse, status_code=status.HTTP_201_CREATED)
def create_direccion(
    cliente_id: int, 
    direccion: DireccionCreate, 
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    # Verificar que el cliente existe
    cliente = crud_cliente.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return crud_cliente.create_direccion(db, cliente_id, direccion)

@router.delete("/direcciones/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_direccion(
    direccion_id: int, 
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    success = crud_cliente.delete_direccion(db, direccion_id)
    if not success:
        raise HTTPException(status_code=404, detail="Dirección no encontrada")
    return None

# ========== CONTACTOS ==========
@router.get("/{cliente_id}/contactos", response_model=List[ContactoResponse])
def read_contactos(
    cliente_id: int, 
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return crud_cliente.get_contactos_by_cliente(db, cliente_id)

@router.get("/{cliente_id}/contactos/rol/{rol}", response_model=List[ContactoResponse])
def read_contactos_by_role(
    cliente_id: int, 
    rol: str, 
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return crud_cliente.get_contactos_by_role(db, cliente_id, rol)

@router.post("/{cliente_id}/contactos", response_model=ContactoResponse, status_code=status.HTTP_201_CREATED)
def create_contacto(
    cliente_id: int, 
    contacto: ContactoCreate, 
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(require_roles(["superuser","admin","coordinador"])))
):
    cliente = crud_cliente.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return crud_cliente.create_contacto(db, cliente_id, contacto)

@router.delete("/contactos/{contacto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contacto(
    contacto_id: int, 
    db: Session = Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    success = crud_cliente.delete_contacto(db, contacto_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return None