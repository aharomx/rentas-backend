from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.movimiento_equipo import (
    MovimientoEquipoCreate,
    MovimientoEquipoResponse
)
from app.models.movimiento_equipo import MovimientoEquipo

router = APIRouter(prefix="/movimientos", tags=["Movimientos de Equipos"])

@router.get("/", response_model=List[MovimientoEquipoResponse])
def read_movimientos(
    skip:int=0,
    limit:int=100,
    equipo_id:Optional[int]=None,
    db:Session=Depends(get_db)
):
    """ Onbtener historial de movimientos de equipos """
    query = db.query(MovimientoEquipo)
    if equipo_id:
        query = query.filter(MovimientoEquipo.id_equipo==equipo_id)
    return query.order_by(MovimientoEquipo.fecha_movimiento.desc()).offset(skip).limit(limit).all

@router.get("/contrato/{contrato_id}", response_model=List[MovimientoEquipoResponse])
def read_movimientos_by_contrato(
    contrato_id:int,
    skip:int=0,
    limit:int=0,
    db:Session=Depends(get_db)
):
    """ Obtener historial de movimientos de un contrato específico """
    return db.query(MovimientoEquipo.filter(
        (MovimientoEquipo.id_contrato_origen == contrato_id)  |
        (MovimientoEquipo.id_contrato_destino == contrato_id)
    )).order_by(MovimientoEquipo.fecha_movimiento.desc()).offset(skip).limit(limit).all()

