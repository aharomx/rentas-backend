from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.contrato import Contrato
from app.models.contrato_equipo import ContratoEquipo
from app.models.movimiento_equipo import MovimientoEquipo
from app.models.equipo import Equipo
from app.schemas.contrato import ContratoCreate, ContratoUpdate
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
        modo_captur=contrato.modo_captura,
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

        # Crear relación contrato-equipo
        db_contrato_equipo = ContratoEquipo(
            id_contrato=db_contrato.id,
            id_equipo=equipo_data.id_equipo,
            fecha_ingreso=contrato.fecha_inicio,
            contador_inicial_contrato=equipo_data.contador_inicial_contrato,
            contador_actual=equipo_data.contador_inicial_contrato,
            ubicacion=equipo_data.ubicacion
        )

        db.add(db_contrato_equipo)

        # Actualizar estad del equipo a "rentado"
        equipo.estado="rentado"

        # Registrar movimiento de alta
        movimiento=MovimientoEquipo(
            id_equipo=equipo.id,
            id_contrato_origin=None,
            id_contato_destino=db_contrato.id,
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
        setattr(db.contrato, key, value)

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
        nuevo_contador_inicial:int,
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

    # Dar de baja en contrato origen
    contrato_equipo_origen.activo = False
    contrato_equipo_origen.fecha_baja=date.today()

    # Dar de alta en contrato destino
    nuevo_contrato_equipo = ContratoEquipo(
        id_contrato=contrato_destino_id,
        id_equipo=equipo_id,
        fecha_ingreso=date.today(),
        contador_inicial_contrato=nuevo_contador_inicial,
        contador_actual=nuevo_contador_inicial,
        ubicacion=nueva_ubicacion or contrato_equipo_origen.ubicacion
    ) 
    db.add(nuevo_contrato_equipo)

    # Registrar movimiento de transferencia
    movimiento = MovimientoEquipo(
        id_equipo=equipo_id,
        id_contrato_origen=contrato_origen_id,
        id_contrato_destino=contrato_destino_id,
        tipo_movimiento="transferencia",
        observacines=f"Transferencia de contrato {contrato_origen_id} a {contrato_destino_id}"
    )
    db.add(movimiento)

    db.commit()
    return nuevo_contrato_equipo

