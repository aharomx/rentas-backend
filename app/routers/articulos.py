from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.articulo import (
    ArticuloCreate,
    ArticuloUpdate,
    ArticuloResponse
)
from app.crud import articulo as crud_articulo
from app.security import get_current_user, require_roles

router=APIRouter(prefix="/articulos",tags=["Articulos"])

@router.get("/",response_model=List[ArticuloResponse])
def read_articulos(
    skip:int=0,
    limit:int=100,
    tipo:Optional[str]=None,
    id_categoria:Optional[int]=None,
    activo:Optional[bool]=None,
    solo_stock_bajo:bool=False,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    return crud_articulo.get_articulos(
        db,
        skip=skip,
        limit=limit,
        tipo=tipo,
        id_categoria=id_categoria,
        activo=activo,
        solo_stock_bajo=solo_stock_bajo
    )

@router.get("/{articulo_id}", response_model=ArticuloResponse)
def read_articulos(
    articulo_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    db_articulo=crud_articulo.get_articulo(db, articulo_id)
    if not db_articulo:
        raise HTTPException(
            status_code=404,
            detail="Articulo no encontrado"
        )
    return db_articulo

@router.post("/", response_model=ArticuloResponse, status_code=status.HTTP_201_CREATED)
def create_articulo(
    articulo: ArticuloCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin", "almacenista"])),
):
    existente = crud_articulo.get_articulo_by_codigo(db, articulo.codigo)
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un artículo con este código")
    return crud_articulo.create_articulo(db, articulo, creado_por_id=current_user.id)


@router.put("/{articulo_id}", response_model=ArticuloResponse)
def update_articulo(
    articulo_id:int,
    articulo_update:ArticuloUpdate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","almacenista"]))
):
    db_articulo=crud_articulo.update_articulo(db, articulo_id,articulo_update)
    if not db_articulo:
        raise HTTPException(
            status_code=404,
            detail="Articulo no encontrado"
        )

    return db_articulo


@router.delete("/{articulo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_articulo(
    articulo_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):

    success = crud_articulo.delete_articulo(db, articulo_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Articulo no encontrado"
        )

    return None