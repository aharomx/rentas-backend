from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, extract
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


from app.models.mantenimiento import Mantenimiento
from app.models.matenimiento_equipo import MantenimientoEquipo
from app.models.mantenimiento_refaccion import MantenimientoRefaccion
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.equipo import Equipo
from app.models.usuario import Usuario
from app.schemas.mantenimiento import (
    MantenimientoCreate, MantenimientoUpdate,
    AutorizarMantenimientoRequest, IniciarMantenimientoRequest,
    CompletarMantenimientoRequest, CancelarMantenimientoRequest,
    EsperaRefaccionesRequest
)
from app.schemas.mantenimiento_equipo import (
    MantenimientoEquipoCreate, MantenimientoEquipoUpdate
)
from app.schemas.mantenimiento_refaccion import (
    MantenimientoRefaccionCreate, MantenimientoRefaccionUpdate
)


# ==================== GENERACION DE FOLIO =======================
def _generar_folio(db:Session) -> str:
    """ Genera folio único por año: MANT-2026-0001 con manejo de concurrencias"""

    from sqlalchemy import func as sql_func
    from sqlalchemy import text

    anio_actual=datetime.now().year
    prefijo=f"MANT-{anio_actual}-"

    # Usar un lock a nivel de tabla para evitar colisiones
    db.execute(text('LOCK TABLE mantenimientos IN EXCLUSIVE MODE'))

    # Contar cuantos hay en el año actual
    count=db.query(sql_func.count(Mantenimiento.id)).filter(
        Mantenimiento.folio.ilike(f"{prefijo}%")
    ).scalar() or 0

    nuevo_num=count+1
    folio_final=f"{prefijo}{nuevo_num:04d}"

    #print(f"Folio generado: {folio_final} (total previos: {count})")

    return folio_final
    


# ============== LECTURA ========================
def get_mantenimiento(
        db:Session,
        mantenimiento_id:int
) -> Optional[Mantenimiento]:

    return db.query(Mantenimiento).options(
        joinedload(Mantenimiento.equipos)
        .joinedload(MantenimientoEquipo.equipo)
        .joinedload(Equipo.modelo),
        joinedload(Mantenimiento.equipos)
        .joinedload(MantenimientoEquipo.refacciones)
        .joinedload(MantenimientoRefaccion.articulo),
        joinedload(Mantenimiento.contrato),
        joinedload(Mantenimiento.tecnico_asignado_user),
    ).filter(Mantenimiento.id == mantenimiento_id).first()

def get_mantenimientos(
        db:Session,
        skip:int=0,
        limit:int=100,
        estado:Optional[str]=None,
        tipo:Optional[str]=None,
        id_contrato:Optional[int]=None,
        mes:Optional[int]=None,
        anio:Optional[int]=None
) -> List[Mantenimiento]:

    query=db.query(Mantenimiento).options(
        joinedload(Mantenimiento.equipos),
        joinedload(Mantenimiento.contrato),
        joinedload(Mantenimiento.tecnico_asignado_user),
    )

    if estado:
        query=query.filter(Mantenimiento.estado==estado)
    if tipo:
        query=query.filter(Mantenimiento.tipo==tipo)
    if id_contrato:
        query=query.filter(Mantenimiento.id_contrato==id_contrato)
    if mes:
        query=query.filter(extract('month',Mantenimiento.fecha_solicitud==mes))
    if anio:
        query=query.filter(extract('year',Mantenimiento.fecha_solicitud==anio))

    return query.order_by(Mantenimiento.fecha_solicitud.desc()).offset(skip).limit(limit).all()

def get_mantanimientos_pendientes(db:Session) -> List[Mantenimiento]:
    """ Mantenimientos programados o en solicitud, listos para trabajar """

    return db.query(Mantenimiento).options(
        joinedload(Mantenimiento.equipos),
        joinedload(Mantenimiento.contrato),
        joinedload(Mantenimiento.tecnico_asignado_user),
    ).filter(
        Mantenimiento.estado.in_(["en_solicitud","programado","en_proceso","en_espera_refacciones"])
    ).order_by(Mantenimiento.fecha_programada.asc()).all()

def get_mantenimientos_por_equipo(
        db:Session,
        equipo_id:int,
) -> List[MantenimientoEquipo]:
    """ Historial de servicio de un equipo específico (Para reportes)"""

    return db.query(MantenimientoEquipo).options(
        joinedload(MantenimientoEquipo.mantenimiento),
        joinedload(MantenimientoEquipo.equipo),
        joinedload(MantenimientoEquipo.refacciones),
    ).filter(
        MantenimientoEquipo.id_equipo==equipo_id
    ).join(Mantenimiento).order_by(
        Mantenimiento.fecha_solicitud.desc()
    ).all()

def get_servicios_por_periodo(
        db:Session,
        equipo_id:int,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
) -> List[MantenimientoEquipo]:
    """ Servicios realizados a un equipo en un periodo (reporte para análisis)"""

    query=db.query(MantenimientoEquipo).options(
        joinedload(MantenimientoEquipo.mantenimiento),
        joinedload(MantenimientoEquipo.refacciones)
    ).join(Mantenimiento).filter(
        MantenimientoEquipo.id_equipo==equipo_id
    )

    if fecha_inicio:
        query=query.filter(Mantenimiento.fecha_solicitud>=fecha_inicio)
    if fecha_fin:
        query=query.filter(Mantenimiento.fecha_fin<=fecha_fin)

    return query.order_by(Mantenimiento.fecha_solicitud.desc()).all()


# ==================== CREAR =========================
def crear_mantenimiento(
        db:Session,
        data:MantenimientoCreate,
        creado_por_id:int
) -> Mantenimiento:
    """ Crea un mantenimiento (preventivo o correctivo) """

    # verificar contrato
    contrato=db.query(Contrato).filter(Contrato.id==data.id_contrato).first()

    if not contrato:
        raise ValueError("Contrato no encontrado")

    if not contrato.activo:
        raise ValueError("El contrato no está activo")

    # Validar tipo
    if data.tipo not in ["preventivo","correctivo"]:
        raise ValueError("Tipo inválido, Debe ser 'preventivo' o 'correctivo' ")

    # Validar equipos
    if not data.equipos:
        raise ValueError("Debe incluir al menos un equipo")

    for equipo_data in data.equipos:
        # Verificar que el equipo está activo en el contrato
        ce=db.query(ContratoEquipo).filter(
            and_(
                ContratoEquipo.id_contrato==data.id_contrato,
                ContratoEquipo.id_equipo==equipo_data.id_equipo,
                ContratoEquipo.activo==True,
            )
        ).first()

        if not ce:
            raise ValueError(
                f"El equipo {equipo_data.id_equipo} no está activo en este contrato"
            )

        # Estado inicial segun tipo
        if data.tipo=="correctivo":
            estado_inicial="en_solicitud"
        else: #preventivo
            estado_inicial="programado"

        # Generar folio
        folio=_generar_folio(db)

        # Crear mantenimiento
        db_mant=Mantenimiento(
            folio=folio,
            id_contrato=data.id_contrato,
            tipo=data.tipo,
            estado=estado_inicial,
            descripcion_problema=data.descripcion_problema,
            observaciones=data.observaciones,
            fecha_programada=data.fecha_programada,
            tecnico_asignado=data.tecnico_asignado,
        )
        db.add(db_mant)
        db.flush()

        # Crar equipos del mantenimiento
        for equipo_data in data.equipos:
            db_me=MantenimientoEquipo(
                id_mantenimiento=db_mant.id,
                id_equipo=equipo_data.id_equipo,
                contador_mono=equipo_data.contador_mono,
                contador_color=equipo_data.contador_color,
                porcentaje_toner_negro=equipo_data.porcentaje_toner_negro,
                porcentaje_toner_amarillo=equipo_data.porcentaje_toner_amarillo,
                porcentaje_toner_magenta=equipo_data.porcentaje_toner_magenta,
                porcentaje_toner_cyan=equipo_data.porcentaje_toner_cyan,
                porcentaje_unidad_imagen=equipo_data.porcentaje_unidad_imagen,
                trabajos_realizados=equipo_data.trabajos_realizados,
                observaciones=equipo_data.observaciones,
                proximo_mantenimiento_fecha=equipo_data.proximo_mantenimiento_fecha,
                proximo_mantenimiento_contador=equipo_data.proximo_mantenimiento_contador,
            )
            db.add(db_me)
            db.flush()

            # Refacciones
            for ref_data in equipo_data.refacciones or []:
                db_ref=MantenimientoRefaccion(
                    id_mantenimiento_equipo=db_me.id,
                    id_articulo=ref_data.id_articulo,
                    cantidad=ref_data.cantidad,
                    numer_serie_toner=ref_data.numero_serie_toner,
                    observaciones=ref_data.observaciones,
                )
                db.add(db_ref)
    db.commit()
    db.refresh(db_mant)
    return db_mant

# ================= ACTUALIZAR ==========================
def update_mantenimiento(
        db:Session,
        mantenimiento_id:int,
        data:MantenimientoUpdate
) -> Optional[Mantenimiento]:

    db_mant=get_mantenimiento(db,mantenimiento_id)
    if not db_mant:
        return None

    # No permitir edición si ya está completado o cancelado
    if db_mant.estado  in ["completado","cancelado"]:
        raise ValueError(
            f"No se puede editar un mantenimiento en estado '{db_mant.estado}'"
        )

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_mant,key,value)

    db.commit()
    db.refresh(db_mant)
    return db_mant

# ================== ACCIONES DE ESTADO ==================
def autorizar_mantenimiento(
        db:Session,
        mantenimiento_id:int,
        data:AutorizarMantenimientoRequest,
        usuario_id:int
) -> Mantenimiento:
    """ Autoriza un mantenimiento correctivo (pasa de en_solicitud a ptrogramado)"""
    db_mant=get_mantenimiento(db, mantenimiento_id)
    if not db_mant:
        raise ValueError("Mantenimiento no encontrado")

    if db_mant.tipo != "correctivo":
        raise ValueError("Solo los mantenimientos correctivos requieren autorización")

    if db_mant.estado != "en_solicitud":
        raise ValueError(
            f"No se puede autorizar. Estado actual: '{db_mant.estado}'"
        )

    db_mant.estado="programado"
    db_mant.autorizado_por=usuario_id
    db_mant.fecha_autorizacion=func.now()

    if data.observaciones:
        db_mant.observaciones=(
            (db_mant.observaciones or "") + f"\n[Autorización] {data.observaciones}"
        ).strip()

    db.commit()
    db.refresh(db_mant)
    return db_mant

def iniciar_mantenimiento(
        db:Session,
        mantenimiento_id:int,
        data:IniciarMantenimientoRequest,
        usuario_id:int
) -> Mantenimiento:
    """ Iniciar mantenimiento (pasa a en_proceso)"""

    db_mant=get_mantenimiento(db,mantenimiento_id)
    if not db_mant:
        raise ValueError("Mantenimiento no encontrado")

    if db_mant.estado != "programado":
        raise ValueError(
            f"No se puede iniciar. Estado actual: '{db_mant.estado}'"
        )

    db_mant.estado="en_proceso"
    db_mant.fecha_inicio=func.now()
    db_mant.tecnico_inicio=data.tecnico_inicio or usuario_id

    db.commit()
    db.refresh(db_mant)
    return db_mant

def completar_mantenimiento(
        db:Session,
        mantenimiento_id:int,
        data:CompletarMantenimientoRequest,
        usuario_id:int
) -> Mantenimiento:
    """" Completa el mantenimiento (Pasa a completad y actualiza equipos)"""

    db_mant=get_mantenimiento(db,mantenimiento_id)

    if not db_mant:
        raise ValueError("Mantenimiento no encontrado")

    if db_mant.estado not in ["en_proceso","en_espera_refacciones"]:
        raise ValueError(
            f"No se puede completar. Estado actual: '{db_mant.estado}'"
        )

    db_mant.estado="completado"
    db_mant.fecha_fin=func.now()
    db_mant.tecnico_fin=usuario_id

    if data.observaciones:
        db_mant.observaciones=(
            (db_mant.observaciones or "")+f"\n[Completado] {data.observaciones}"
        ).strip()


    # Actualizar fechas de próximo mantenimiento en equipos
    for me in db_mant.equipos:
        equipo=db.query(Equipo).filter(Equipo.id==me.id_equipo).first()
        if equipo:
            equipo.ultimo_mantenimiento_fecha=date.today()
            if me.proximo_mantenimiento_fecha:
                equipo.proximo_mantenimiento_fecha=me.proximo_mantenimiento_fecha

            if me.proximo_mantenimiento_contador:
                equipo.proximo_mantenimiento_contador=me.proximo_mantenimiento_contador

    db.commit()
    db.refresh(db_mant)
    return db_mant

def cancelar_mantenimiento(
        db:Session,
        mantenimiento_id:int,
        data:CancelarMantenimientoRequest,
) -> Mantenimiento:
    """ Cancela el mantenimiento """

    db_mant=get_mantenimiento(db, mantenimiento_id)
    if not db_mant:
        raise ValueError("Mantenimiento no encontrado")

    if db_mant.estado in ["completado","cancelado"]:
        raise ValueError(
            f"No se puede cancelar. Estado actual: '{db_mant.estado}"
        )

    db_mant.estado="cancelado"
    db_mant.motivo_cancelacion=data.motivo_cancelacion

    db.commit()
    db.refresh(db_mant)
    return db_mant

def poner_en_espera_refacciones(
        db:Session,
        mantenimiento_id:int,
        data:EsperaRefaccionesRequest
) -> Mantenimiento:
    """ Pone el mantenimiento en espera de refacciones """

    db_mant=get_mantenimiento(db,mantenimiento_id)
    if not db_mant:
        raise ValueError("Mantenimiento no encontrado")

    if db_mant.estado != "en_proceso":
        raise ValueError(
            f"Solo se puede poner en espera si está 'en_proceso'. Estado actual: '{db_mant.estado}'"
        )

    db_mant.estado="en_espera_refaccines"
    db_mant.motivo_espera

    db.commit()
    db.refresh(db_mant)
    return db_mant


# =============== GESTION DE EQUIPOS ======================
def agregar_equipo_a_mantenimiento(
        db:Session,
        mantenimiento_id:int,
        data:MantenimientoEquipoCreate
) -> MantenimientoEquipo:
    """ Agrega un equipo a un mantenimiento existente """

    db_mant=get_mantenimiento(db,mantenimiento_id)
    if not db_mant:
        raise ValueError("Mantenimiento no encontrado")

    if db_mant.estado in ["completado", "cancelado"]:
        raise ValueError(
            f"No se puede modificar un mantenimiento en estado '{db_mant.estado}'"
        )

    # Verificar que el equipo está activo en el contrato
    ce=db.query(ContratoEquipo).filter(
        and_(
            ContratoEquipo.id_contrato==db_mant.id_contrato,
            ContratoEquipo.id_equipo==data.id_equipo,
            ContratoEquipo.activo==True,
        )
    ).first()

    if not ce:
        raise ValueError(
            f"El equipo {data.id_equipo} no está activo en el contrato {db_mant.id_contrato}"
        )

    # Verificar que no esté ya en el mantenimiento
    existente=db.query(MantenimientoEquipo).filter(
        and_(
            MantenimientoEquipo.id_mantenimiento==mantenimiento_id,
            MantenimientoEquipo.id_equipo==data.id_equipo
        )
    ).first()

    if existente:
        raise ValueError(
            f"El equipo {data.id_equipo} ya está en este mantenimiento"
        )

    db_me=MantenimientoEquipo(
        id_mantenimiento=mantenimiento_id,
        id_equipo=data.id_equipo,
        contador_mono=data.contador_mono,
        contador_color=data.contador_color,
        porcentaje_toner_negro=data.porcentaje_toner_negro,
        porcentaje_toner_amarillo=data.porcentaje_toner_amarillo,
        porcentaje_toner_magenta=data.porcentaje_toner_magenta,
        porcentaje_toner_cyan=data.porcentaje_toner_cyan,
        porcentaje_unidad_imagen=data.porcentaje_unidad_imagen,
        trabajos_realizados=data.trabajos_realizados,
        observaciones=data.observaciones,
        proximo_mantenimiento_fecha=data.proximo_mantenimiento_fecha,
        proximo_mantenimiento_contador=data.proximo_mantenimiento_contador,
    )

    db.add(db_me)
    db.commit()
    db.refresh(db_me)
    return db_me

def update_mantenimiento_equipo(
        db:Session,
        mantenimiento_equipo_id:int,
        data:MantenimientoEquipoUpdate
) -> Optional[MantenimientoEquipo]:
    """ Actualiza un equipo del mantenimiento """

    db_me=db.query(MantenimientoEquipo).filter(
        MantenimientoEquipo.id==mantenimiento_equipo_id
    ).first()

    if not db_me:
        return None

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_me,key,value)

    db.commit()
    db.refresh(db_me)
    return db_me

def delete_mantenimiento_equipo(
        db:Session,
        mantenimiento_equipo_id:int,
) -> bool:
    """ Elimina un equipo del mantenimiento """

    db_me=db.query(MantenimientoEquipo).filter(
        MantenimientoEquipo.id==mantenimiento_equipo_id
    ).first()

    if not db_me:
        return False

    db.delete(db_me)
    db.commit()
    return True

# ========== GESTION DE REFACCIONES =============
def agregar_refaccion(
        db:Session,
        mantenimiento_equipo_id:int,
        data:MantenimientoRefaccionCreate
) -> MantenimientoRefaccion:
    """ Agrega una refacción a un equipo del mantenimiento """
    db_me=db.query(MantenimientoEquipo).filter(
        MantenimientoEquipo.id==mantenimiento_equipo_id
    ).first()

    if not db_me:
        raise ValueError("Equipo del mantenimiento no encontrado")

    db_ref=MantenimientoRefaccion(
        id_mantenimiento_equipo=mantenimiento_equipo_id,
        id_articulo=data.id_articulo,
        cantidad=data.cantidad,
        numero_serie_toner=data.numero_serie_toner,
        observaciones=data.observaciones,
    )

    db.add(db_ref)
    db.commit()
    db.refresh(db_ref)
    return db_ref

def delete_refaccion(
        db:Session,
        refaccion_id:int
) -> bool:
    """ Elimina una refacción del mantenimiento """

    db_ref=db.query(MantenimientoRefaccion).filter(
        MantenimientoRefaccion.id==refaccion_id
    ).first()

    if not db_ref:
        return False

    db.delete(db_ref)
    db.commit()
    return True

# ============= ELIMINAR ===================
def delete_mantenimiento(
        db:Session,
        mantenimiento_id:int
) -> bool:
    db_mant=get_mantenimiento(db,mantenimiento_id)

    if not db_mant:
        return False

    if db_mant.estado=="completado":
        raise ValueError("No se puede elimiar un mantenimiento completado")

    db.delete(db_mant)
    db.commit()
    return True

 