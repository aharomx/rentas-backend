from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.tipo_plan import TipoPlanCreate, TipoPlanUpdate, TipoPlanResponse
from app.crud import tipo_plan as crud_tipo_plan

router=APIRouter(prefix="/tipos-plan", tags=["Tipos de Plan"])

@router.get("/", response_model=List[TipoPlanResponse])
def read_tipos_plan(
    skip:int=0,
    limit:int=100,
    activo:Optional[bool]=None,
    db:Session=Depends(get_db)
):
    return crud_tipo_plan.get_tipos_plan(db, skip=skip, limit=limit, activo=activo)

@router.get("/{tipo_plan_id}", response_model=TipoPlanResponse)
def read_tipo_plan(tipo_plan_id:int, db:Session=Depends(get_db)):
    db_tipo_plan=crud_tipo_plan.get_tipo_plan(db, tipo_plan_id)
    if not db_tipo_plan:
        raise HTTPException(
            status_code=404,
            detail="Tipo de plan no encontrado"
        )
    return db_tipo_plan

@router.post("/", response_model=TipoPlanResponse, status_code=status.HTTP_201_CREATED)
def create_tipo_plan(tipo_plan:TipoPlanCreate, db:Session=Depends(get_db)):
    existing=crud_tipo_plan.get_tipo_plan_by_name(db, tipo_plan.nombre)
    if existing:
        raise HTTPException(
            status_code=404,
            detail="Ya existe un tipo de plan con este nombre"
        )
    return crud_tipo_plan.create_tipo_plan(db, tipo_plan)

@router.put("/{tipo_plan_id}", response_model=TipoPlanResponse)
def update_tipo_plan(tipo_plan_id:int, tipo_plan_update:int, db:Session=Depends(get_db)):
    db_tipo_plan=crud_tipo_plan.update_tipo_plan(db, tipo_plan_id, tipo_plan_update)
    if not db_tipo_plan:
        raise HTTPException(
            status_code=404,
            detail="Tipo de plan no encontrado"
        )
    return db_tipo_plan

@router.delete("/{tipo_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_plan(tipo_plan_id:int, db:Session=Depends(get_db)):
    success=crud_tipo_plan.delete_tipo_plan(db, tipo_plan_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="No se puede eliminar porque tiene contratos asociados o no existe"
        )
    return None

