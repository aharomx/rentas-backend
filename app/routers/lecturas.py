from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.lectura_contador import (
    LecturaContadorCreate,
    LecturaContadorResponse,
    CorreccionLecturaRequest
)
from app.crud import lectura_contador as crud_lecturas
from app.crud import contrato_equipo as crud_ce
from app.security import get_current_user, require_roles


router = APIRouter(prefix="/lecturas", tags=["Lecturas de Contadores"])


@router.get("/", response_model=List[LecturaContadorResponse])
def read_lecturas(
    skip:int=0,
    limit:int=100,
    id_contrato_equipo:Optional[int]=None,
    mes:Optional[int]=None,
    anio:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    return crud_lecturas.get_lecturas(
        db,
        skip=skip,
        limit=limit,
        id_contrato_equipo=id_contrato_equipo,
        mes=mes,
        anio=anio
    )


@router.post("/", response_model=LecturaContadorResponse, status_code=status.HTTP_201_CREATED)
def create_lectura(
    lectura: LecturaContadorCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser", "admin", "coordinador", "tecnico"]))
):
    try:
        db_lectura=crud_lecturas.create_lectura(
            db,
            lectura,
            capturada_por_id=current_user.id
        )
        return db_lectura
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/{lectura_id}/corregir", response_model=LecturaContadorResponse)
def corregir_lectura(
    lectura_id:int,
    correccion: CorreccionLecturaRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Corrige una lectura creando una nueva con auditoría """

    try:
        db_lectura=crud_lecturas.corregir_lectura(
            db,
            lectura_id, 
            correccion,
            capturada_por_id=current_user.id
        )
        return db_lectura
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.get("/equipo/{contrato_equipo_id}", response_model=List[LecturaContadorResponse])
def read_lecturas_by_equipo(
    contrato_equipo_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Historial de lecturas de un equipo en un contrato """

    return crud_lecturas.get_lecturas(
        db,
        id_contrato_equipo=contrato_equipo_id
    )

@router.get("/contrato/{contrato_id}", response_model=List[LecturaContadorResponse])
def read_lecturas_by_contratos(
    contrato_id:int,
    mes:Optional[int]=None,
    anio:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    return crud_lecturas.get_lecturas_by_contratos(
        db,
        contrato_id,
        mes=mes,
        anio=anio
    )


@router.get("/faltantes/periodo")
def read_equipos_sin_lectura(
    mes:int,
    anio:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Equipos activos sin lectura en el mes/año especificado """

    equipos=crud_lecturas.get_equipos_sin_lectura(
        db,
        mes=mes,
        anio=anio
    )

    return [
        {
            "id_contrato_equipo":ce.id,
            "id_contrato":ce.id_contrato,
            "id_equipo":ce.id_equipo,
            "numero_serie":ce.equipo.numero_serie if ce.equipo else None,
            "ubicacion":ce.ubicacion,
            "contador_actual":ce.contador_actual
        }
        for ce in equipos
    ]



