from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from app.database import get_db
from app.security import get_current_user
from app.crud import reportes_kpi as crud_kpi
from app.crud import reportes_facturacion as crud_fact
from app.crud import reportes_consumo as crud_cons
from app.crud import reportes_equipos as crud_eq
from app.crud import reportes_contratos as crud_ct
from app.utils import excel_reporter
from app.utils.pdf_rentabilidad import genera_pdf_rentabilidad


router=APIRouter(prefix="/reportes",tags=["Reportes"])

# ================= DASHBOARD ====================
@router.get("/dashboard")
def get_dashboard(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Dashboard con KPI's principales """

    return crud_kpi.get_dashboard_kpis(db)

# =============== FACTURACIÓN ====================
@router.get("/facturacion/periodo")
def get_facturacion_periodo(
    anio:Optional[int]=None,
    id_cliente:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Facturación agrupada por mes."""
    return crud_fact.get_facturacion_por_periodo(
        db, anio=anio, id_cliente=id_cliente
    )

@router.get("/rentabilidad/contrato/{id_contrato}")
def get_rentabilidad_contrato(
    id_contrato:int,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Rentabilidad de un contrato """
    try:
        return crud_fact.get_rentabilidad_contrato(
            db,
            id_contrato,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )   
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# =============== CONSUMO DE TÓNER ====================

@router.get("/consumo-toner/clientes")
def get_consumo_toner(
    id_cliente:Optional[int]=None,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Consumo de tóner por cliente """

    return crud_cons.get_consumo_toner_por_cliente(
        db,
        id_cliente=id_cliente,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

@router.get("/consumo-toner/real-vs-esperado")
def get_consumo_real_vs_esperado(
    id_cliente:Optional[int]=None,
    id_contrato:Optional[int]=None,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    porcentaje_cobertura:float=5.0,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ 
        Reporte de consumo real vs esperado.
        El porcentaje_cobertura indica el % de cobertura del tóner (defautl 5%).
    """
    from decimal import Decimal

    return crud_cons.get_consumo_real_vs_esperado(
        db,
        id_cliente=id_cliente,
        id_contrato=id_contrato,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        porcentaje_cobertura=Decimal(str(porcentaje_cobertura))
    )

# ================ EQUIPOS =====================

@router.get("/equipos/mas-rentables")
def get_equipos_mas_rentables(
    limite:int=20,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Top equipos más rentables """

    return crud_eq.get_equipos_mas_rentables(
        db,
        limite=limite,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )

@router.get("/equipos/rotacion")
def get_rotacion_equipos(
    limite:int=50,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Rotación de equipos (movimientos entre contratos)"""

    return crud_eq.get_rotacion_equipos(db, limite=limite)


# ================== CONTRATOS ======================

@router.get("/contratos/por-vencer")
def get_contratos_por_vencer(
    dias:int=30,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Contratos próximos a vencer """

    return crud_ct.get_contratos_por_vencer(db, dias=dias)


@router.get("/contratos/mas-rentables")
def get_contratos_mas_rentables(
    limite:int=20,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Top contratos mas rentables """

    return crud_ct.get_contratos_mas_rentables(
        db,
        limite=limite,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )


# =================== EXCEL =========================

@router.get("/dashboard/excel")
def excel_dashboard(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Dashboard KPIs en Excel."""
    try:
        filename = excel_reporter.reporte_dashboard_kpis(db)
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="dashboard_kpis.xlsx",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/facturacion/periodo/excel")
def excel_facturacion(
    anio:Optional[int]=None,
    id_cliente:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Facturación por periodo en Excel """
    try:
        filename=excel_reporter.reporte_facturacion_periodo(
            db,
            anio,
            id_cliente=id_cliente
        )
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="facturacion_periodo.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/consumo-toner/clientes/excel")
def excel_consumo_toner(
    id_cliente:Optional[int]=None,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Consumo de tóner en Excel """
    try:
        filename=excel_reporter.reporte_consumo_toner(
            db,
            id_cliente=id_cliente,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="consumo_toner.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/consumo-toner/real-vs-esperado/excel")
def excel_consumo_real_vs_esperado(
    id_cliente:Optional[int]=None,
    id_contrato:Optional[int]=None,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    porcentaje_cobertura:float=5.0,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Consumo real vs esperado en Excel """
    try:
        filename=excel_reporter.reporte_consumo_real_vs_esperado(
            db,
            id_cliente=id_cliente,
            id_contrato=id_contrato,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            porcentaje_cobertura=porcentaje_cobertura
        )
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="consumo_real_vs_esperado.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/equipos/mas-rentables/excel")
def excel_equipos_mas_rentables(
    limite:int=20,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Equipos más rentables en Excel """
    try:
        filename=excel_reporter.reporte_equipos_mas_rentables(
            db,
            limite=limite,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="equipos_mas_rentables.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/contratos/por-vencer/excel")
def excel_contratos_por_vencer(
    dias:int=30,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Contratos por vencer en excel """
    try:
        filename=excel_reporter.reporte_contratos_por_vencer(
            db,
            dias=dias,
        )
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="contratos_por_vencer.xlsx",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ======================== PDF =================
@router.get("/rentabilidad/contrato/{id_contrato}/pdf")
def pdf_rentabilidad(
    id_contrato:int,
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Rentabilidad de un contrato en PDF """
    try:
        filename=genera_pdf_rentabilidad(
            db,
            id_contrato,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return FileResponse(
            filename,
            media_type="application/pdf",
            filename=f"rentabilidad_contrato_{id_contrato}.pdf",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )
    
