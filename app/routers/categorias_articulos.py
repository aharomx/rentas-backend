from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session
from typing import List,Optional

from app.database import get_db
from app.schemas.categoria_articulo import (
    CategoriaArticuloCreate,
    CategoriaArticuloUpdate,
    CategoriaArticuloResponse
)
from app.crud import categoria_articulo as crud_cat
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/categoria-articulo", tags=["Categorías de Artículos"])

@router.get("/", response_model=List[CategoriaArticuloResponse])
def read_categorias(
        skip:int=0,
        limit:int=100,
        activo:Optional[bool]=None,
        db:Session=Depends(get_db),
        current_user=Depends(get_current_user),
):

    return crud_cat.get_categorias(db, skip=skip, limit=limit, activo=activo)

@router.get("/{catagoria_id}", response_model=CategoriaArticuloResponse)
def read_categoria(
    categoria_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_cat=crud_cat.get_categoria(db, categoria_id)
    if not db_cat:
        raise HTTPException(
            status_code=404,
            detail="Categoria no encontrada"
        )

    return db_cat

@router.post("/", response_model=CategoriaArticuloResponse, status_code=status.HTTP_201_CREATED)
def create_categoria(
    categoria:CategoriaArticuloCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","almacenista"])),
):

    existente = crud_cat.get_categoria_by_nombre(db, categoria.nombre)
    if existente:
        raise HTTPException(
            status_code=404,
            detail="Ya existe una categoría con este nombre"
        )

    return crud_cat.create_categoria(db,categoria)


@router.put("/{categoria_id}", response_model=CategoriaArticuloResponse)
def update_categoria(
    categoria_id: int,
    categoria_update: CategoriaArticuloUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin", "almacenista"])),
):
    db_cat = crud_cat.update_categoria(db, categoria_id, categoria_update)
    if not db_cat:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return db_cat



@router.delete("/{categoria_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_categoria(
    categoria_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):
    try:
        success=crud_cat.delete_categoria(db,categoria_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Categoría no encontrdada"
            )

        return None
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )