from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.movimiento_equipo import MovimientoEquipo
from app.models.equipo import Equipo
from app.schemas.contrato import ContratoCreate, ContratoUpdate, ContratoEquipoCreate
from typing import List, Optional
from datetime import date, timedelta


def get_contrato(db:Session, contrato_id:int):
    return db.query(Contrato).filter(Contrato.id==contrato_id).first()

def get_contratos_by_cliente(db:Session, cliente_id:int, activo:Optional[bool]=None):
    query=db.query(Contrato).filter(Contrato.id_cliente==cliente_id)
    if activo is not None:
        query=query.filter(Contrato.activo==activo)

    return query.all()

def get_contratos(db:Session, skip:int=0, limit:int=100, activo:Optional[bool]=None):
    query=db.query(Contrato)
    if activo is not None:
        query=query.filter(Contrato.activo==activo)

    return query.offset(skip).limit(limit).all()

def get_contratos_por_vencer(db:Session, dias:int=30):
    """ Obtener contrato que vencen en los proximos 'dias' dias """
    fecha_limite=date.today()+timedelta(days=dias)
    return db.query(Contrato).filter(
        and_(
            Contrato.activo==True,
            Contrato.fecha_fin<=fecha_limite,
            Contrato.fecha_fin>=date.today()
        )
    ).all()

def get_contratos_vencidos(db:Session):
    """ Obtener contratos vencidos que aún están activos """
    return db.query(Contrato).filter(
        and_(
            Contrato.activo==True,
            Contrato.fecha_fin < date.today()
        )
    ).all()

def create_contrato(db:Session, contrato:ContratoCreate):
    # Crear contrato
    db_contrato=Contrato(
        id_cliente=contrato.id_cliente,
        id_tipo_plan=contrato.id_tipo_plan,
        fecha_inicio=contrato.fecha_inicio,
        fecha_fin=contrato.fecha_fin,
        costo_renta_mensual=contrato.costo_renta_mensual,
        costo_click_mono=contrato.costo_click_mono,
        costo_click_color=contrato.costo_click_color,
        bolsa_mono=contrato.bolsa_mono,
        bolsa_color=contrato.bolsa_color,
        costo_excedente_mono=contrato.costo_excedente_mono,
        costo_excedente_color=contrato.costo_excedente_color,
        modo_captura=contrato.modo_captura,
        condiciones_especiales=contrato.condiciones_especiales,
        observaciones=contrato.observaciones
    )
    db.add(db_contrato)
    db.flush() # Para obtener el id

    # Asignar equipos al contrato
    for equipo_data in contrato.equipos:
        # Verificar que el equipo existe y está disponible
        equipo=db.query(Equipo).filter(Equipo.id==equipo_data.id_equipo).first()

        if not equipo:
            raise ValueError(f"Equipo ID {equipo.numero_serie} no encontrado")

        if equipo.estado != "disponible":
            raise ValueError(f"Equipo {equipo.numero_serie} no está dispobible")

        # Validar si el equipo es monocromático, no traiga contador color
        es_color=equipo.modelo.es_color if equipo.modelo else False

        if not es_color and equipo_data.contador_inicial_color not in (None,0):
            raise ValueError(
                f"El equipo {equipo.numero_serie} es monocromático, "
                f"No debe tenedr contador de color"
            )

        # Crear relación contrato-equipo
        db_contrato_equipo = ContratoEquipo(
            id_contrato=db_contrato.id,
            id_equipo=equipo_data.id_equipo,
            fecha_ingreso=contrato.fecha_inicio,
            contador_inicial_mono=equipo_data.contador_inicial_mono,
            contador_inicial_color=equipo_data.contador_inicial_color or 0,
            contador_actual_mono=equipo_data.contador_actual_mono,
            contador_actual_color=equipo_data.contador_actual_color or 0,
            ubicacion=equipo_data.ubicacion
        )

        db.add(db_contrato_equipo)

        # Actualizar estad del equipo a "rentado"
        equipo.estado="rentado"

        # Registrar movimiento de alta
        movimiento=MovimientoEquipo(
            id_equipo=equipo.id,
            id_contrato_origen=None,
            id_contrato_destino=db_contrato.id,
            tipo_movimiento="alta",
            observaciones=f"Alta en contrato {db_contrato.id}"
        )
        db.add(movimiento)

    db.commit()
    db.refresh(db_contrato)
    return db_contrato 


def update_contrato(db:Session, contrato_id:int, contrato_update:ContratoUpdate):
    db_contrato=get_contrato(db, contrato_id)
    if not db_contrato:
        return None

    for key, value in contrato_update.model_dump(exclude_unset=True).items():
        setattr(db_contrato, key, value)

    db.commit()
    db.refresh(db_contrato)
    return db_contrato

def delete_contrato(db:Session, contrato_id:int):
    db_contrato=get_contrato(db, contrato_id)
    if not db_contrato:
        return False

    db.delete(db_contrato)
    db.commit()
    return True

def mover_equipo_contrato(
        db:Session,
        equipo_id:int,
        contrato_origen_id:int,
        contrato_destino_id:int,
        nuevo_contador_inicial_mono:int,
        nuevo_contador_inicial_color:Optional[int]=0,
        nueva_ubicacion:Optional[str]=None
):
    """ Mover un equipo de un contrato a otro """

    # Verificar que el equipo existe
    equipo=db.query(Equipo).filter(Equipo.id==equipo_id).first()
    if not equipo:
        raise ValueError("Equipo no encontrado")

    # Verificar que está en el contrato origen
    contrato_equipo_origen=db.query(ContratoEquipo).filter(
        and_(
            ContratoEquipo.id_contrato==contrato_origen_id,
            ContratoEquipo.id_equipo==equipo_id,
            ContratoEquipo.activo==True
        )
    ).first()

    if not contrato_equipo_origen:
        raise ValueError("El equipo no está activo en el contrato origen")

    # Verificar que el contrato destino existe
    contrato_destino = get_contrato(db,contrato_destino_id)
    if not contrato_destino:
        raise ValueError("Contrato destino no encontrado")


    if not contrato_destino.activo:
        raise ValueError("El contrato destino no está activo")

    # Verificar que no esté ya en el destino
    ya_en_destino=db.query(ContratoEquipo).filter(
        and_(
            ContratoEquipo.id_contrato==contrato_destino_id,
            ContratoEquipo.id_equipo==equipo_id,
            ContratoEquipo.activo==False
        )
    ).first()


    if ya_en_destino:
        raise ValueError(
            " El equipo ya está activado en el contrato destino"
        )


    # Dar de baja en contrato origen
    contrato_equipo_origen.activo = False
    contrato_equipo_origen.fecha_baja=date.today()

    # Validar monocromático
    es_color=equipo.modelo.es_color if equipo.modelo else False
    if not es_color:
        nuevo_contador_inicial_color=0

    # Dar de alta en contrato destino
    nuevo_contrato_equipo = ContratoEquipo(
        id_contrato=contrato_destino_id,
        id_equipo=equipo_id,
        fecha_ingreso=date.today(),
        contador_inicial_mono=nuevo_contador_inicial_mono,
        contador_inicial_color=nuevo_contador_inicial_color or 0,
        contador_actual_mono=nuevo_contador_inicial_mono,
        contador_actual_color=nuevo_contador_inicial_color or 0,
        ubicacion=nueva_ubicacion or contrato_equipo_origen.ubicacion
    ) 
    db.add(nuevo_contrato_equipo)

    # El equipo sigue rentado (ahora en el nuevo contrato)
    equipo.estado="rentado"

    # Registrar movimiento de transferencia
    movimiento = MovimientoEquipo(
        id_equipo=equipo_id,
        id_contrato_origen=contrato_origen_id,
        id_contrato_destino=contrato_destino_id,
        tipo_movimiento="transferencia",
        observaciones=f"Transferencia de contrato {contrato_origen_id} a {contrato_destino_id}"
    )
    db.add(movimiento)

    db.commit()
    db.refresh(nuevo_contrato_equipo)
    return nuevo_contrato_equipo

# =================== FUNCIONES ADICIONALES PARA CONTRATO-EQUIPO ==========================

def agregar_equipo_a_contrato(db: Session, contrato_id: int, equipo_data: ContratoEquipoCreate):
    """Agregar un equipo a un contrato existente con validaciones reforzadas."""
    from sqlalchemy import and_
    
    contrato = get_contrato(db, contrato_id)
    if not contrato:
        raise ValueError("Contrato no encontrado")
    
    if not contrato.activo:
        raise ValueError("El contrato no está activo")
    
    # Verificar que el equipo existe
    equipo = db.query(Equipo).filter(Equipo.id == equipo_data.id_equipo).first()
    if not equipo:
        raise ValueError("Equipo no encontrado")
    
    # ⭐ VALIDACIÓN CRÍTICA: verificar que no esté activo en NINGÚN contrato
    existe_en_contrato = db.query(ContratoEquipo).filter(
        and_(
            ContratoEquipo.id_equipo == equipo_data.id_equipo,
            ContratoEquipo.activo == True
        )
    ).first()
    
    if existe_en_contrato:
        raise ValueError(
            f"El equipo {equipo.numero_serie} ya está asignado activamente al contrato "
            f"{existe_en_contrato.id_contrato}. Debe retirarlo primero."
        )
    
    # ⭐ Verificar el estado del equipo
    if equipo.estado != "disponible":
        raise ValueError(
            f"El equipo {equipo.numero_serie} no está disponible "
            f"(estado actual: {equipo.estado})"
        )
    
    # Validar monocromático vs color
    es_color = equipo.modelo.es_color if equipo.modelo else False
    if not es_color and equipo_data.contador_inicial_color not in (None, 0):
        raise ValueError(f"El equipo {equipo.numero_serie} es monocromático, no acepta contador color")
    
    # Crear la relación
    db_contrato_equipo = ContratoEquipo(
        id_contrato=contrato_id,
        id_equipo=equipo_data.id_equipo,
        fecha_ingreso=date.today(),
        contador_inicial_mono=equipo_data.contador_inicial_mono,
        contador_inicial_color=equipo_data.contador_inicial_color or 0,
        contador_actual_mono=equipo_data.contador_inicial_mono,
        contador_actual_color=equipo_data.contador_inicial_color or 0,
        ubicacion=equipo_data.ubicacion,
        activo=True
    )
    db.add(db_contrato_equipo)
    
    # Actualizar estado del equipo
    equipo.estado = "rentado"
    
    # Registrar movimiento
    movimiento = MovimientoEquipo(
        id_equipo=equipo.id,
        id_contrato_origen=None,
        id_contrato_destino=contrato_id,
        tipo_movimiento="alta",
        observaciones=f"Alta en contrato {contrato_id}"
    )
    db.add(movimiento)
    
    db.commit()
    db.refresh(db_contrato_equipo)
    return db_contrato_equipo


def retirar_equipo_de_contrato(db:Session, contrato_id:int, equipo_id:int):
    """ 
        Retirar un equipo de un contrato 
        Actualiza correctamente el estado del equipo basándose en si sigue en otro contrato
    """

    from sqlalchemy import and_



    # Buscar la relación activa
    contrato_equipo = db.query(ContratoEquipo).filter(
        and_(
            ContratoEquipo.id_contrato==contrato_id,
            ContratoEquipo.id_equipo==equipo_id,
            ContratoEquipo.activo== True
        )
    ).first()
 
    if not contrato_equipo:
        raise ValueError("El equipo no está activo en este contrato")

    # Dar de baja
    contrato_equipo.activo = False
    contrato_equipo.fecha_baja = date.today()

    # Verificar si el equipo sigue en otro contrato activo
    otro_contrato_activo=db.query(ContratoEquipo).filter(
        and_(
            ContratoEquipo.id_equipo==equipo_id,
            ContratoEquipo.activo==True,
            ContratoEquipo.id != contrato_equipo.id # Excluir el que acabamos de dar de baja
        )
    ).first()



    # Actualizar estado del equipo
    equipo=db.query(Equipo).filter(Equipo.id==equipo_id).first()
    if equipo:
        if otro_contrato_activo:
            equipo.estado = "rentado"
        else:
            equipo.estado="disponible"

    # Registrar Movimiento
    movimiento=MovimientoEquipo(
        id_equipo=equipo_id,
        id_contrato_origen=contrato_id,
        id_contrato_destino=None,
        tipo_movimiento="baja",
        observaciones=f"Baja del contrato {contrato_id}"
    )
    db.add(movimiento)

    db.commit()
    db.refresh(contrato_equipo)
    return contrato_equipo
    