from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date 

from app.database import get_db
from app.schemas.orden_lectura import (
    OrdenLecturaCreate,
    OrdenLecturaUpdate,
    OrdenLecturaResponse
)
from app.crud import orden_lectura as crud_orden
from app.crud import contrato as crud_contrato
from app.security import get_current_user, require_roles
from app.models.contrato_equipo import ContratoEquipo


router = APIRouter(prefix="/ordenes-lectura", tags=["Órdenes de lectura"])


@router.get("/", response_model=List[OrdenLecturaResponse])
def read_ordenes(
    skip:int=0,
    limit:int=100,
    estado:Optional[str]=None,
    id_contrato:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Lista todas las órdenes de lectura """

    return crud_orden.get_ordenes(
        db,
        skip=skip,
        limit=limit,
        estado=estado, 
        id_contrato=id_contrato
    )


@router.get("/{orden_id}", response_model=OrdenLecturaResponse)
def read_orden(
    orden_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    db_orden=crud_orden.get_orden(db, orden_id)
    if not db_orden:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )

    return db_orden


@router.post("/", response_model=OrdenLecturaResponse, status_code=status.HTTP_201_CREATED)
def create_orden(
    orden:OrdenLecturaCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Genera una nueva orden de lectura para un contrato """

    contrato=crud_contrato.get_contrato(db, orden.id_contrato)
    if not contrato:
        raise HTTPException(
            status_code=404,
            detail="Contrato no encontrado"
        )

    if not contrato.activo:
        raise HTTPException(
            status_code=400,
            detail="El contrato no está activo"
        )

    # Verificar que tenga equipos activos
    equipos = db.query(ContratoEquipo).filter(
        ContratoEquipo.id_contrato==orden.id_contrato,
        ContratoEquipo.activo==True
    ).count()

    if equipos==0:
        raise HTTPException(
            status_code=400,
            detail="El contrato no tiene equipos activos para lectura"
        )

    return crud_orden.create_orden(db, orden, generada_por_id=current_user.id)


@router.put("/{orden_id}", response_model=OrdenLecturaResponse)
def update_orden(
    orden_id:int,
    orden_update:OrdenLecturaUpdate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinado"]))
):
    db_orden=crud_orden.update_orden(db, orden_id, orden_update)
    if not db_orden:
        raise HTTPException(
            status_code=404, 
            detail="Orden no encontrada"
        )

    return db_orden


@router.delete("/{orden_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_orden(
    orden_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser", "admin", "coordinador"]))
):

    success=crud_orden.delete_orden(db, orden_id)
    if not success:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    return None

@router.get("/{orden_id}/pdf")
def descargar_pdf_orden(
    orden_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Descarga el PDF de la cédula de lectura ordenada por ubicación """

    from app.utils.pdf_orden_lectura import generar_cedula_lectura
    from fastapi.responses import FileResponse

    db_orden=crud_orden.get_orden(db, orden_id)
    if not db_orden:
        raise HTTPException(
            status_code=404,
            detail="Orden no encontrada"
        )

    ruta_pdf=generar_cedula_lectura(db, orden_id)

    return FileResponse(
        ruta_pdf,
        media_type="application/pdf",
        filename=f"cedula_lectura_{orden_id}.pdf"
    )

