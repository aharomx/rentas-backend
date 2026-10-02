from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.schemas.mantenimiento import (
    MantenimientoCreate, MantenimientoUpdate, MantenimientoResponse,
    MantenimientoResumenResponse,
    AutorizarMantenimientoRequest,IniciarMantenimientoRequest,
    CompletarMantenimientoRequest, CancelarMantenimientoRequest,
    EsperaRefaccionesRequest
)
from app.schemas.mantenimiento_equipo import (
    MantenimientoEquipoCreate, MantenimientoEquipoUpdate,
    MantenimientoEquipoResponse
)
from app.schemas.mantenimiento_refaccion import (
    MantenimientoRefaccionCreate, MantenimientoRefaccionResponse
)
from app.crud import mantenimiento as crud_mant
from app.crud import articulo as crud_articulo
from app.security import get_current_user, require_roles

router = APIRouter(prefix="/mantenimientos", tags=["Mantenimientos"])

# ============= LISTADO Y CONSULTA =================

@router.get("/",response_model=List[MantenimientoResponse])
def read_mantenimientos(
    skip:int=0,
    limit:int=100,
    estado:Optional[str]=None,
    tipo:Optional[str]=None,
    id_contrato:Optional[int]=None,
    mes:Optional[int]=None,
    anio:Optional[int]=None,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Lista mantenimientos con filtros opcionales """

    return crud_mant.get_mantenimientos(
        db,
        skip=skip,
        limit=limit,
        estado=estado,
        tipo=tipo,
        id_contrato=id_contrato,
        mes=mes,
        anio=anio
    )


@router.get("/pendientes",response_model=List[MantenimientoResumenResponse])
def read_mantenmientos_pendientes(
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):

    """ Movimientos Pendientes (en_solicitud, programado, en_proceso, en_espera) """

    return crud_mant.get_mantanimientos_pendientes(db)


@router.get("/{mantenimiento_id}",response_model=MantenimientoResponse)
def read_mantenimiento(
    mantenimiento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Obtiene el mantenimiento completo con equipos y refacciones """

    db_mant=crud_mant.get_mantenimiento(db,mantenimiento_id)
    if not db_mant:
        raise HTTPException(
            status_code=404,
            detail="Mantenimiento no encontrado"
        )
    return db_mant

# =========== CREAR / ACTUALIZAR / ELIMINAR ===================

@router.post("/", response_model=MantenimientoResponse,status_code=status.HTTP_201_CREATED)
def create_mantenimiento(
    data:MantenimientoCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Crea un mantenimiento (preventivo o correctivo)"""
    try:
        return crud_mant.crear_mantenimiento(db,data,creado_por_id=current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.put("/{mantenimiento_id}",response_model=MantenimientoResponse)
def update_mantenimiento(
    mantenimiento_id:int,
    data:MantenimientoUpdate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Actualiza datos generales de un mantenimiento (no permite editar si está completado/cancelado)"""
    try:
        db_mant=crud_mant.update_mantenimiento(db,mantenimiento_id,data)

        if not db_mant:
            raise HTTPException(
                status_code=404,
                detail="Mantenimiento no encontrado"
            )
        return db_mant
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete("/{mantenimiento_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mantenimiento(
    mantenimiento_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):
    """ Elimina un mantenimiento (no permite si está completado)"""

    try:
        success=crud_mant.delete_mantenimiento(db,mantenimiento_id)

        if not success:
            raise HTTPException(
                status_code=404,
                detail="Mantenimiento no encontrado"
            )
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail="Mantenimiento no encontrado"
        )


# =============== ACCIONES DE ESTADO =====================

@router.post("/{mantenimiento_id}/autorizar",response_model=MantenimientoResponse)
def autorizar_mantenimiento(
    mantenimiento_id:int,
    data:AutorizarMantenimientoRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    """ Autoriza un mantenimiento correctivo (en_solicitud a programado) """

    try:
        return crud_mant.autorizar_mantenimiento(
            db,
            mantenimiento_id,
            data,
            usuario_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/{mantenimiento_id}/iniciar",response_model=MantenimientoResponse)
def iniciar_mantenimiento(
    mantenimiento_id:int,
    data:IniciarMantenimientoRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Inicia un mantenimiento (programado a en_proceso)"""
    try:
        return crud_mant.iniciar_mantenimiento(
            db,
            mantenimiento_id,
            data,
            usuario_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/{mantenimiento_id}/completar", response_model=MantenimientoResponse)
def completar_mantenimiento(
    mantenimiento_id:int,
    data:CompletarMantenimientoRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Completa un mantenimiento (en_proceso/en_espera a completado) """
    try:
        return crud_mant.completar_mantenimiento(
            db,
            mantenimiento_id,
            data,
            usuario_id=current_user.id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/{mantenimiento_id}",response_model=MantenimientoResponse)
def cancelar_mantenimiento(
    mantenimiento_id:int,
    data:CancelarMantenimientoRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    """ Cancela un mantenimiento """
    try:
        return crud_mant.cancelar_mantenimiento(
            db,
            mantenimiento_id,
            data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.post("/{mantenimiento_id}/espera-refacciones",response_model=MantenimientoResponse)
def espera_refaccines(
    mantenimiento_id:int,
    data:EsperaRefaccionesRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Pone el mantenimiento en espera de refacciones(en_proceso a en_espera_refacciones) """

    try:
        return crud_mant.poner_en_espera_refacciones(
            db,
            mantenimiento_id,
            data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ================= GESTION DE EQUIPOS DEL MANTENIMIENTO ======================

@router.post(
    "/{mantenimiento_id}/equipos",
    response_model=MantenimientoEquipoResponse,
    status_code=status.HTTP_201_CREATED,
)
def agregar_equipo(
    mantenimiento_id:int,
    data:MantenimientoEquipoCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Agrega un equipo a un mantenimiento existente """

    try:
        return crud_mant.agregar_equipo_a_mantenimiento(
            db,
            mantenimiento_id,
            data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.put(
    "/equipos/{mantenimiento_equipo_id}",
    response_model=MantenimientoEquipoResponse
)
def update_equipo(
    mantenimiento_equipo_id:int,
    data:MantenimientoEquipoUpdate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Actualiza el detalle de un equipo en el mantenimiento (contadores, trabajos, etc)"""

    db_me=crud_mant.update_mantenimiento_equipo(db,mantenimiento_equipo_id,data)
    if not db_me:
        raise HTTPException(
            status_code=404,
            detail="Equipo del mantenimiento no encontrado"
        )
    return db_me

@router.delete(
    "/equipos/{mantenimiento_equipo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_equipo(
    mantenimiento_equipo_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    """ Elimina un equipo del mantenimiento """
    success=crud_mant.delete_mantenimiento_equipo(db,mantenimiento_equipo_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Equipo del mantenimientono encontrado"
        )
    return None


# ================== GESTION DE REFACCIONES ==================

@router.post(
    "/equipos/{mantenimiento_equipo_id}/refacciones",
    response_model=MantenimientoRefaccionResponse,
    status_code=status.HTTP_201_CREATED,
)
def agregar_refaccion(
        mantenimiento_equipo_id:int,
        data:MantenimientoRefaccionCreate,
        db:Session=Depends(get_db),
        current_user=Depends(require_roles(["superuser","admin","coordinador","tecnico"]))
):
    """ Agrega una refacción a un equipo del mantenimiento """

    # Verificar que el artículo existe
    articulo=crud_articulo.get_articulo(db, data.id_articulo)
    if not articulo:
        raise HTTPException(
            status_code=404,
            detail="Articulo no encontrado"
        )

    try:
        return crud_mant.agregar_refaccion(
            db,
            mantenimiento_equipo_id,
            data
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@router.delete(
    "/refacciones/{refaccion_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_refaccion(
    refaccion_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin","coordinador"]))
):
    """ Elimina una refacción del Mantenimiento """

    success=crud_mant.delete_refaccion(db,refaccion_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Refacción no encontrada"
        )
    
    return None


# ================ HISTORIAL Y REPORTES POR EQUIPO ====================

@router.get("/equipo/{equipo_id}/historial", response_model=List[MantenimientoEquipoResponse])
def historial_por_equipo(
    equipo_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Historial de mantenimientos de un equipo específico """

    return crud_mant.get_mantenimientos_por_equipo(db, equipo_id)


@router.get("/equipo/{equipo_id}/servicios", response_model=List[MantenimientoEquipoResponse])
def servicios_por_periodo(
    equipo_id:int,
    fecha_inicio:Optional[date]=Query(None,description="Fecha Inicial (YYYY-MM-DD)"),
    fecha_fin:Optional[date]=Query(None,description="Fecha final (YYYY-MM-DD)"),
    db:Session=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """ Servicios realizados a un equipo en un periodo (reportes para análisis) """

    return crud_mant.get_servicios_por_periodo(
        db,
        equipo_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

