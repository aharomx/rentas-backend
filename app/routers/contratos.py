from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date 

from app.database import get_db
from app.schemas.contrato import (
    ContratoCreate,ContratoUpdate,ContratoResponse,
    ContratoEquipoCreate, ContratoEquipoResponse
)
from app.crud import contrato as crud_contrato
from app.crud import cliente as crud_cliente
from app.crud import tipo_plan as crud_tipo_plan
from app.crud import equipo as crud_equipo
from app.security import get_current_user, require_roles


router=APIRouter(prefix="/contratos", tags=["Contratos"])


# ====================== CONTRATOS ==============================

@router.get("/", response_model=List[ContratoResponse])
def read_contratos(
    skip:int=0,
    limit:int=1000,
    activo:Optional[bool]=None,
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """ Obtener lista de contratos con paginación y filtro por estado """
    return crud_contrato.get_contratos(db, skip=skip, limit=limit, activo=activo)


@router.get("/cliente/{cliente_id}", response_model=List[ContratoResponse])
def read_contratod_by_cliente(
    cliente_id:int,
    activo:Optional[bool]=None,
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """ Obtener contratos de un cliente específico """

    # Verificar que el cliente existe
    cliente = crud_cliente.get_cliente(db, cliente_id)
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )
    return crud_contrato.get_contratos_by_cliente(db, cliente_id, activo=activo)


@router.get("/por-vencer", response_model=List[ContratoResponse])
def read_contratos_por_vencer(
    dias:int=30,
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """ Obtener contratos que vencen en los próximos N dias"""
    return crud_contrato.get_contratos_por_vencer(db, dias=dias)


@router.get("/vencidos", response_model=List[ContratoResponse])
def read_contratos_vencidos(
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """ Obtener contratos vencidos que aún están activos """
    return crud_contrato.get_contratos_vencidos(db)

@router.get("/{contrato_id}", response_model=ContratoResponse)
def read_contrato(
    contrato_id:int, 
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    """ Obtener contrato por su id """
    db_contrato = crud_contrato.get_contrato(db, contrato_id)
    if not db_contrato:
        raise HTTPException(
            status_code=404,
            detail="Contrato no encontrado"
        )
    return db_contrato

@router.post("/", response_model=ContratoResponse, status_code=status.HTTP_201_CREATED)
def create_contrato(
    contrato:ContratoCreate, 
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Crear un nuevo contrato con sus equipos asignados """

    # Verificar que el cliente existe
    cliente = crud_cliente.get_cliente(db, contrato.id_cliente)
    if not cliente:
        raise HTTPException(
            status_code=404,
            detail="Cliente no encontrado"
        )

    # Verificar que el tipo de plan exista
    tipo_plan = crud_tipo_plan.get_tipo_plan(db, contrato.id_tipo_plan)
    if not tipo_plan:
        raise HTTPException(
            status_code=404,
            detail="Tipo de plan no encontrado"
        )

    # Verificar que la fecha de inicio sea menor que la fecha de fin
    if contrato.fecha_inicio >= contrato.fecha_fin:
        raise HTTPException(
            status_code=400,
            detail="La fecha de inicio debe ser menos que la fecha de fin"
        )

    try:
        db_contrato = crud_contrato.create_contrato(db, contrato)
        return db_contrato
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.put("/{contrato_id}", response_model=ContratoResponse)
def update_contrato(
    contrato_id:int,
    contrato_update:ContratoUpdate,
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Actualizar un contrato existente """
    db_contrato = crud_contrato.update_contrato(db, contrato_id,contrato_update)
    if not db_contrato:
        raise HTTPException(
            status_code=404,
            detail="Contrato no encontrado"
        )
    return db_contrato

@router.delete("/{contrato_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contrato(
    contrato_id:int, 
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin"]))
):
    """ Eliminar un contrato (Solo si no tiene equipos activos)"""

    db_contrato = crud_contrato.get_contrato(db, contrato_id)
    if not db_contrato:
        raise HTTPException(
            status_code=404,
            detail="Contrato no encontrado"
        )

    # Verificar si tiene equipos activos
    equipos_activos=[ce for ce in db_contrato.equipos_asignados if ce.activo]
    if equipos_activos:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar el contrato porue tiene equipos activos"
        )

    success = crud_contrato.delete_contrato(db, contrato_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Contrato no encontrado"
        )


# ================ NOVIMIENTOS DE EQUIPOS ============================
@router.post("/{contrato_id}/equipos", response_model=ContratoEquipoResponse)
def agregar_equipo_a_contrato(
        contrato_id:int,
        equipo_data:ContratoEquipoCreate,
        db:Session=Depends(get_db),
        current_user = Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Agregar un equipo existente a un contrato """

    # Verificar que el contrato existe
    contrato=crud_contrato.get_contrato(db, contrato_id)
    if not contrato:
        raise HTTPException(
            status_code=404,
            detail="Contrato no encontrado"
        )

    # Verificar que el equipo existe
    equipo = crud_equipo.get_equipo(db, equipo_data.id_equipo)
    if not equipo:
        raise HTTPException(
            status_code=404,
            detail="Equipo no encontrado"
        )

    # Verificar que el equipo está disponible
    if equipo.estado != "disponible":
        raise HTTPException(
            status_code=400,
            detail=f"El equipo {equipo.numero_serie} no está disponible (estado: {equipo.estado})"
        )

    try:
        # Importar aquí para evitar circular imports
        from app.crud import contrato as crud_contrato_full

        # Crear relación contrato-equipo
        nuevo_contrato_equipo = crud_contrato_full.agregar_equipo_a_contrato(db, contrato_id, equipo_data)
        return nuevo_contrato_equipo
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/mover-equipo")
def mover_equipo_entre_contratos(
    equipo_id:int,
    contrato_origen_id:int,
    contrato_destino_id:int,
    nuevo_contador_inicial:int,
    nueva_ubicación:Optional[str]=None,
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin", "coordinador"]))
):
    """ Mover un equipo de un contrato a otro """
    try:
        resultado = crud_contrato.mover_equipo_contrato(
            db,
            equipo_id=equipo_id,
            contrato_origen_id=contrato_origen_id,
            contrato_destino_id=contrato_destino_id,
            nuevo_contador_inicial=nuevo_contador_inicial,
            nueva_ubicacion=nueva_ubicación
        )
        return {
            "mensaje":"Equipo movido exitosamente",
            "contrato_equipo_id": resultado.id,
            "contrato_destino": contrato_destino_id
        }        
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete("/{contrato_id}/equipos/{equipo_id}")
def retirar_equipo_de_contrato(
    contrato_id:int,
    equipo_id:int,
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin"]))
):
    """ Retirar equipo un contrato (dar de baja)"""
    try:
        from app.crud import contrato as crud_contrato_full

        resultado = crud_contrato_full.retirar_equipo_de_contrato(db, contrato_id, equipo_id)
        return {
            "mensaje":"Equipo rtirado del contrato",
            "contrato_equipo_id":resultado.id,
            "equipo_id":equipo_id,
            "fecha_baja":resultado.fecha_baja
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
