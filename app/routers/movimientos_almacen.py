from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date 

from app.database import get_db
from app.schemas.movimiento_almacen import (
    MovimientoAlmacenCreate,
    MovimientoAlmacenResponse,
    KardexItem,
    StockBajoItem
)
from app.crud import movimiento_almacen as crud_mov
from app.security import get_current_user, require_roles


router=APIRouter(prefix="/movimientos-almacen",tags=["Movimientos de Almacén"])


@router.get("/",response_model=List[MovimientoAlmacenResponse])
def read_movimientos(
    skip:int=0,
    limit:int=100,
    id_articulo:Optional[int]=None,
    tipo:Optional[str]=None,
    mes:Optional[int]=None,
    anio:Optional[int]=None,
    fecha_inicio:Optional[date]=None,
    fecha_fin: Optional[date] = None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    return crud_mov.get_movimientos(
        db,
        skip=skip,
        limit=limit,
        id_articulo=id_articulo,
        tipo=tipo,
        mes=mes,
        anio=anio,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin 
    )


@router.get("/stock-bajo",response_model=List[StockBajoItem])
def read_stock_bajo(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Articulos con stock por debajo del mínimo """

    return crud_mov.get_articulos_stock_bajo(db)


@router.get("/resumen")
def read_resumen_movimientos(
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Resumen de movimientos por tipo en un periodo """

    return crud_mov.get_resumen_movimientos(
        db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )


@router.get("/kardex/{articulo_id", response_model=List[KardexItem])
def read_kardex(
    articulo_id:int,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    skip:int=0,
    limit:int=500,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Kardex (Historial) de un artículo """

    return crud_mov.get_kardex(
        db,
        articulo_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        skip=skip,
        limit=limit
    )

@router.get("/{movimiento_id}", response_model=(MovimientoAlmacenResponse))
def read_movimiento(
    movimiento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    db_mov=crud_mov.get_movimiento(db,movimiento_id)
    if not db_mov:
        raise HTTPException(
            status_code=404,
            detail="Movimiento no encontrado"
        )

    return db_mov


@router.post("/", response_model=MovimientoAlmacenResponse, status_code=status.HTTP_201_CREATED)
def create_movimiento(
    data:MovimientoAlmacenCreate,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Crea un movimiento de almacén y actualiza el stock """
    try:
        return crud_mov.create_movimiento(
            db,
            data,
            registrado_por_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

