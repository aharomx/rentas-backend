from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.equipo import EquipoCreate, EquipoUpdate, EquipoResponse
from app.crud import equipo as crud_equipo
from app.crud import modelo_impresora as crud_modelo
from app.security import get_current_user,require_roles


router = APIRouter(prefix="/equipos", tags=["Equipos"])

@router.get("/", response_model=List[EquipoResponse])
def read_equipos(
    skip:int=0,
    limit:int=100,
    estado:Optional[str]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Obtener una lista de equipos con paginación y filtro por estad """
    return crud_equipo.get_equipos(db, skip=skip, limit=limit, estado=estado)

@router.get("/{equipo_id}", response_model=EquipoResponse)
def read_equipo(
    equipo_id:int, 
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Obtener un equipo por us id """

    db_equipo = crud_equipo.get_equipo(db, equipo_id)
    if not db_equipo:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado"
        )

    return db_equipo

@router.post("/", response_model=EquipoResponse, status_code=status.HTTP_201_CREATED)
def create_equipo(
    equipo:EquipoCreate, 
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Crear un nuevo equipo (dar de alta en inventario)"""

    # Verificar que el modelo existe
    modelo = crud_modelo.get_modelo(db, equipo.id_modelo)
    if not modelo:
        raise HTTPException(
            status_code=404, 
            detail="Modelo de impresora no encontrado"
        )

    # Verificar que el número de serie no esté duplicado
    existing = crud_equipo.get_equipo_by_serie(db, equipo.numero_serie)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un equipo con ese número de serie"
        )

    return crud_equipo.create_equipo(db, equipo)

@router.put("/{equipo_id}", response_model=EquipoResponse)
def update_equipo(
    equipo_id:int, 
    equipo_update:EquipoUpdate, 
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Actualizar un equipo existente (estado o fecha de baja)"""

    db_equipo = crud_equipo.update_equipo(db, equipo_id, equipo_update)
    if not db_equipo:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado"
        )

    return db_equipo


@router.delete("/{equipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_equipo(
    equipo_id:int, 
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin"]))
):
    """ Eliminar un equipo (borrado físico) """

    success = crud_equipo.delete_equipo(db, equipo_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado"
        )
    return None

