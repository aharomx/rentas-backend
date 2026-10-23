from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date 

from app.database import get_db
from app.security import get_current_user, require_roles
from app.utils import excel_reporter
from app.crud import articulo as crud_articulo

router = APIRouter(prefix="/reportes/almacen", tags=["Reportes de Almacén"])


# =========== TÓNERS POR CLIENTE ==================

@router.get("/toners-por-cliente/excel")
def excel_toners_por_cliente(
    id_cliente:Optional[int]=None,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Genera Excel de tóners por cliente """
    try:
        filename=excel_reporter.reporte_toners_por_cliente(
            db,
            id_cliente=id_cliente,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"toners_por-cliente.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============== REFACCIONES EN MANTENIMIENTOS ==============

@router.get("/refacciones-mantenimientos/excel")
def excel_refacciones_mantenimientos(
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    id_equipo:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Genera Excel de refacciones usadas en mantenimientos """

    try:
        filename=excel_reporter.reporte_refacciones_mantenimientos(
            db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_equipo=id_equipo,
        )

        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"refacciones_mantenimientos.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ================== MOVIMIENTOS DE ALMACÉN ===========================

@router.get("/movimientos/excel")
def excel_movimientos(
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    tipo:Optional[str]=None,
    id_articulo:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Genera Excel de movimientos de almacén """

    try:
        filename= excel_reporter.reporte_movimientos_almacén(
            db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
            id_articulo=id_articulo
        )
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="movimientos_almacen.xlsx"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ================== STOCK CRíTICO =========================

@router.get("/stock-critico/excel")
def excel_stock_critico(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Genera Excel de artículos con stock crítico """
    try:
        filename=excel_reporter.reporte_stock_critico(db)
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"stock_critico.xlsx"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ================ HISTORIAL DE REFACCIONES POR EQUIPO =============

@router.get("/historial-refacciones-equipo/{id_equipo}/excel")
def excel_historial_refacciones_equipo(
    id_equipo:int,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Genera Excel del historial de refacciones de un equipo """

    try:
        filename=excel_reporter.reporte_historial_refacciones_equipos(
            db,
            id_equipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=f"historial_refacciones_equipo_{id_equipo}.xlsx",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404, 
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
