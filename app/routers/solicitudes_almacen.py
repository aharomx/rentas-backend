from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.schemas.solicitud_almacen import (
    SolicitudAlmacenCreate, SolcitudAlmacenUpdate,
    SolicitudAlmacenResponse, SolicitudAlmacenResumenResponse,
    AutorizarSolicitudRequest, EntregarSolicitudRequest,
    CompletarRecoleccionRequest, DevolucionPosteriorRequest,
    CancelarSolicitudRequest,
    ReporteDevolucionesItem
)

from app.schemas.solicitud_almacen_detalle import (
    SolicitudAlmacenDetallResponse,
    SolicitudAlmacenDetalleCreate,
    SolicitudAlmacenDetalleUpdate

)

from app.crud import solicitud_almacen as crud_sol
from app.security import get_current_user, require_roles

router=APIRouter(prefix="/solicitudes-almacen", tags=["Solicitudes de almacén"])


# ============== LISTADO Y CONSULTA ===========================

@router.get("/",response_model=List[SolicitudAlmacenResumenResponse])
def read_solicitudes(
    skip:int=0,
    limit:int=100,
    tipo:Optional[str]=None,
    estado:Optional[str]=None,
    id_cliente:Optional[int]=None,
    mes:Optional[int]=None,
    anio:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    return crud_sol.get_solicitudes(
        db, skip=skip, limit=limit,tipo=tipo,estado=estado,
        id_cliente=id_cliente, mes=mes, anio=anio,
    )

@router.get("/pendientes", response_model=List[ReporteDevolucionesItem])
def read_pendientes(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Solicitudes pendientes de entrega y autorización o recolección """

    return crud_sol.get_pendientes(db)


@router.get("/devoluciones", response_model=List[ReporteDevolucionesItem])
def read_devoluciones(
    fecha_inicio:Optional[date]=None,
    fecha_fin:Optional[date]=None,
    id_cliente:Optional[date]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Reporte de devoluciones parciales y totales """

    return crud_sol.get_devoluciones(
        db,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_cliente=id_cliente
    )


@router.get("/{solicitud_id}", response_model=SolicitudAlmacenResponse)
def read_solicitud(
    solicitud_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_sol=crud_sol.get_solicitud(db, solicitud_id)
    if not db_sol:
        raise HTTPException(
            status_code=404,
            detail="Solicitud no encontrada"
        )

    return db_sol


@router.get("/{solicitud_id}/pdf")
def descargar_pdf_solicitud(
    solicitud_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Descarga el PDF de la solicitud """

    from app.utils.pdf_solicitud import generar_pdf_solicitud
    from fastapi.responses import FileResponse

    db_sol=crud_sol.get_solicitud(db,solicitud_id)
    if not db_sol:
        raise HTTPException(
            status_code=404,
            detail="Solicitud no encontrada"
        )

    try:
        ruta_pdf=generar_pdf_solicitud(db, solicitud_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return FileResponse(
        ruta_pdf,
        media_type="application/pdf",
        filename=f"{db_sol.folio}.pdf"
    )






# =============== CREAR / ACTUALIZAR / ELIMINAR ============
@router.post("/", response_model=SolicitudAlmacenResponse, status_code=status.HTTP_201_CREATED)
def create_solicitud(
    data:SolicitudAlmacenCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","almacenista"])),
):
    """ Crea una solicitud de almacén (entrega o recolección)"""

    try:
        return crud_sol.create_solicitud(db,data,registrado_por_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/{solicitud_id}", response_model=SolicitudAlmacenResponse)
def update_solicitud(
    solicitud_id:int,
    data:SolcitudAlmacenUpdate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinar"]))
):

    try:
        db_sol=crud_sol.update_solicitud(db,solicitud_id, data)
        if not db_sol:
            raise HTTPException(
                status_code=404,
                detail="Solicitud no encontrada"
            )

        return db_sol
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.delete("/{solicitud_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_solicitud(
    solicitud_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):
    try:
        success=crud_sol.delete_solicitud(db,solicitud_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Solicitud no encontrada"
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=400, 
            detail=str(e)
        )

# ================= ACCIONES DE ESTADO ===================

@router.post("/{solicitud_id}/autorizar", response_model=SolicitudAlmacenResponse)
def autorizar_solicitud(
    solicitud_id:int,
    data:AutorizarSolicitudRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):

    try: 
        return crud_sol.autorizar_solicitud(
            db,
            solicitud_id,
            data,
            usuario_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/{solicitud_id}/entregar", response_model=SolicitudAlmacenResponse)
def entregar_solicitud(
    solicitud_id:int,
    data:EntregarSolicitudRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","almacenista"]))
):
    """ Marca como entregada, descuenta de stock y registra devoluciones en el momento """

    try:
        return crud_sol.entregar_solicitud(
            db,
            solicitud_id,
            data,
            usuario_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/{solicitud_id}/completar-recoleccion", response_model=SolicitudAlmacenResponse)
def completar_recoleccion(
    solicitud_id:int,
    data:CompletarRecoleccionRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","almacenista"]))
):
    """ Completa una recolección: los tóners van a desecho """

    try:
        return crud_sol.completar_recoleccion(
            db,
            solicitud_id,
            data,
            usuario_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/{solicitud_id}/devolución-posterior", response_model=SolicitudAlmacenResponse)
def devolucion_posterior(
    solicitud_id:int,
    data:DevolucionPosteriorRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","almacenista"]))
):
    """ Registra una devolución posterior (días después de la entrega) """
    try:
        return crud_sol.registrar_devolucion_posterior(
            db,
            solicitud_id,
            data,
            usuario_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/{solicitud_id}/cancelar", response_model=SolicitudAlmacenResponse)
def cancelar_solicitud(
    solicitud_id:int,
    data:CancelarSolicitudRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):

    try:
        return crud_sol.cancelar_solicitud(
            db,
            solicitud_id,
            data,
            usuario_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ================= DETALLE =======================

@router.post(
    "/{solicitud_id}/detalle",
    response_model=SolicitudAlmacenDetallResponse,
    status_code=status.HTTP_201_CREATED,
)
def agregar_detalle(
    solicitud_id:int,
    data:SolicitudAlmacenDetalleCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","almacenista"]))
):

    try:
        return crud_sol.agregar_detalle(db,solicitud_id,data)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete("/detalle/{detalle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_detalle(
    detalle_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):

    try:
        success=crud_sol.delete_detalle(db,detalle_id)
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Detalle no encontrado"
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


