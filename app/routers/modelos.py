from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.modelo_impresora import (
    ModeloImpresoraCreate, 
    ModeloImpresoraUpdate, 
    ModeloImpresoraResponse
)
from app.crud import modeo_impresora as crud_modelo

router = APIRouter(prefix="/modelos", tags=["Modelos de Impresoras"])

@router.get("/", response_model=List[ModeloImpresoraResponse])
def read_modelos(
    skip:int=0,
    limit:int=100,
    es_color:Optional[bool]=None,
    db:Session=Depends(get_db)
):
    """ Obtener lista de modelos con paginacion y filtro por tipo """

    return crud_modelo.get_modelos(db, skip=skip, limit=limit, es_color=es_color)


@router.get("/{modelo_id}", response_model=ModeloImpresoraResponse)
def read_modelo(modelo_id:int, db:Session=Depends(get_db)):
    """ Obtener un modelo por su id """
    db_modelo = crud_modelo.get_modelo(db, modelo_id)
    if not db_modelo:
        raise HTTPException(
            status_code=404,
            detail="Modelo no encontrado"
        )
    return db_modelo


@router.post("/", response_model=ModeloImpresoraResponse, status_code=status.HTTP_201_CREATED)
def create_modelo(modelo:ModeloImpresoraCreate, db:Session=Depends(get_db)):
    """ Crear un nuevo modelo de impresora """
    existing=crud_modelo.get_modelo_by_name(db, modelo.nombre_modelo)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un modelo con ese nombre"
        )
    return crud_modelo.create_modelo(db, modelo)

@router.put("/{modelo_id}", response_model=ModeloImpresoraResponse)
def update_modelo(modelo_id:int, modelo_update:ModeloImpresoraUpdate, db:Session=Depends(get_db)):
    """ Actualizar un modelo existente """
    db_modelo= crud_modelo.update_model(db, modelo_id, modelo_update)
    if not db_modelo:
        raise HTTPException(
            status_code=404,
            detail="Modelo no encontrado"
        )
    return db_modelo

@router.delete("/{modelo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_modelo(modelo_id:int, db:Session=Depends(get_db)):
    """ Eliminar un modelo (solo si no tiene equipos asociados)"""
    success = crud_modelo.delete_modelo(db, modelo_id)
    if not succes:
        raise HTTPException(
            status_code=400,
            detail="No se puede elimiar el modelo porque tiene equipos asociados"
        )
    return None
