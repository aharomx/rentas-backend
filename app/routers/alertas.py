from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.alerta import (
    AlertaResponse, AlertaResumenResponse,
    MarcarLeidaRequest, AtenderAlertaRequest, DescartarAlertaRequest,
    GenerarAlertaResponse, ResumenAlertasDashboard
)
from app.crud import alerta as crud_alerta
from app.services import alerta_service
from app.security import get_current_user, require_roles

router=APIRouter(prefix="/alertas",tags=["Alertas"])


# ================== LISTADO ======================

@router.get("/",response_model=List[AlertaResumenResponse])
def read_alertas(
    skip:int=0,
    limit:int=100,
    estado:Optional[str]=None,
    tipo:Optional[str]=None,
    prioridad:Optional[str]=None,
    referencia_tipo:Optional[str]=None,
    referencia_id:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):

    return crud_alerta.get_alertas(
        db,
        skip=skip,
        limit=limit,
        estado=estado,
        tipo=tipo,
        prioridad=prioridad,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id
    )


@router.get("/nuevas",response_model=List[AlertaResumenResponse])
def read_alertas_nuevas(
    limit:int=50,
    db:Session=Depends(get_db),
):
    """ Alertas nuevas (no leidas) """

    return crud_alerta.get_alertas_nuevas(db, limit=limit)


@router.get("/dashboard", response_model=ResumenAlertasDashboard)
def read_resume_dashboard(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Resumen de alertas para el dashboard """

    return crud_alerta.get_resumen_dashboard(db)


@router.get("/{alerta_id}",response_model=AlertaResponse)
def read_alerta(
    alerta_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ Leer una alerta específica """

    db_alerta=crud_alerta.get_alerta(db, alerta_id)

    if not db_alerta:
        raise HTTPException(
            status_code=404,
            details="Alerta no encontrada"
        )

    return db_alerta

@router.post("/{alerta_id}/marcar-leida", response_model=AlertaResponse)
def marcar_leida(
    alerta_id:int,
    data:MarcarLeidaRequest,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        db_alerta=crud_alerta.marcar_leida(
            db,
            alerta_id,
            data,
            usuario_id=current_user.id,
        )

        if not db_alerta:
            raise HTTPException(
                status_code=404,
                detail="Alerta no encontrada",
            )
        return db_alerta
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/{alerta_id}/atender", response_model=AlertaResponse)
def atender_alerta(
    alerta_id:int,
    data:AtenderAlertaRequest,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        db_alerta=crud_alerta.atender_alerta(
            db,
            alerta_id,
            data,
            usuario_id=current_user.id,
        )

        if not db_alerta:
            raise HTTPException(
                status_code=404,
                detail="Alerta no encontrada"
            )
        return db_alerta
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{alerta_id}/descartar", response_model=AlertaResponse)
def descartar_alerta(
    alerta_id:int,
    data:DescartarAlertaRequest,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        db_alerta=crud_alerta.descartar_alerta(
            db,
            alerta_id,
            data,
            usuario_id=current_user.id
        )

        if not db_alerta:
            raise HTTPException(
                status_code=404,
                detail="Alerta no encontrada"
            )

        return db_alerta
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# =============== GENERACION =================

@router.post("/generar", response_model=GenerarAlertaResponse)
def generar_alertas(
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinadr"]))
):
    """ 
        Genera todas las alertas manualmente.
        TAmbién se puede generar automáticamente por cron
    """
    try:
        resultado=alerta_service.generar_todas_las_alertas(db)

        return GenerarAlertaResponse(
            total_generadas=resultado["total_generadas"],
            total_omitidas_duplicadas=resultado["total_omitidas_duplicadas"],
            alertas_por_tipo=resultado["detalle_por_tipo"],
            mensaje=(
                f"Se generaron {resultado['total_generadas']} alertas nuevas."
                f"{resultado['total_omitidas_duplicadas']} omitidas por duplicado"
            ),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    
