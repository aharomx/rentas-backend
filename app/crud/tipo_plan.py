from sqlalchemy.orm import Session
from app.models.tipo_plan import TipoPlan
from app.schemas.tipo_plan import TipoPlanCreate, TipoPlanUpdate
from typing import List, Optional

def get_tipo_plan(db:Session, tipo_plan_id:int):
    return db.query(TipoPlan).filter(TipoPlan.id==tipo_plan_id).first()

def get_tipo_plan_by_name(db:Session, nombre:str):
    return db.query(TipoPlan).filter(TipoPlan.nombre==nombre).first()

def get_tipos_plan(db:Session, skip:int=0, limit:int=100, activo:Optional[bool]=None):
    query=db.query(TipoPlan)
    if activo is not None:
        query=query.filter(TipoPlan.activo==activo)

    return query.offset(skip).limit(limit).all()

def create_tipo_plan(db:Session, tipo_plan:TipoPlanCreate):
    db_tipo_plan=TipoPlan(**tipo_plan.model_dump())
    db.add(db_tipo_plan)
    db.commit()
    db.refresh(db_tipo_plan)
    return db_tipo_plan

def update_tipo_plan(db:Session, tipo_plan_id:int, tipo_plan_update:TipoPlanUpdate):
    db_tipo_plan=get_tipo_plan(db, tipo_plan_id)
    if not db_tipo_plan:
        return None

    for key, value in tipo_plan_update.model_dump(exclude_unset=True).items():
        setattr(db_tipo_plan, key, value)

    db.commit()
    db.refresh(db_tipo_plan)
    return db_tipo_plan

def delete_tipo_plan(db:Session, tipo_plan_id:int):
    db_tipo_plan=get_tipo_plan(db, tipo_plan_id)
    if not db_tipo_plan:
        return False
    # Verificar si ha contratos usando este plan
    if db_tipo_plan.contratos:
        return False # No se puede eliminar si tiene contratos asociados
    db.delete(db_tipo_plan)
    db.commit()
    return True
