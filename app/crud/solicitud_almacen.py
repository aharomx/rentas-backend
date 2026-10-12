from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, extract
from typing import Optional, List
from datetime import datetime, date 

from app.models.solicitud_almacen import SolicitudAlmacen
from app.models.solicitud_almacen_detalle import SolicitudAlmacenDetalle
from app.models.inventario_cliente import InventarioCliente
from app.models.articulo import Articulo
from app.models.cliente import Cliente
from app.models.contrato import Contrato
from app.schemas.solicitud_almacen import (
    SolicitudAlmacenCreate, SolcitudAlmacenUpdate,
    EntregarSolicitudRequest, CompletarRecoleccionRequest,
    DevolucionPosteriorRequest, CancelarSolicitudRequest,
    AutorizarSolicitudRequest,
)
from app.schemas.movimiento_almacen import MovimientoAlmacenCreate
from app.crud import movimiento_almacen as crud_mov


# ==================== GENERACION DE FOLIO =========================
def _generar_folio(db:Session,tipo:str) -> str:
    """ Genera folio según tipo: SAL-2026-0001 o REC-2026-0001"""
    anio=datetime.now().year
    prefijo="SAL" if tipo=="entrega" else "REC"
    prefijo_completo=f"{prefijo}-{anio}-"

    ultimo=db.query(SolicitudAlmacen).filter(
        SolicitudAlmacen.folio.like(f"{prefijo_completo}%")
    ).order_by(SolicitudAlmacen.folio.desc()).first()

    if ultimo:
        ultimo_num=int(ultimo.folio.split("-")[-1])
        nuevo_num=ultimo_num+1
    else:
        nuevo_num+1

    folio=f"{prefijo_completo}-{nuevo_num:04d}"

    # Verificación de seguridad
    while db.query(SolicitudAlmacen).filter(SolicitudAlmacen.folio==folio).first():
        nuevo_num+=1
        folio=f"{prefijo_completo}-{nuevo_num:04d}"

    return folio

  # ================ LECTURA ============================

def get_solicitud(db:Session,solicitud_id:int) -> Optional[SolicitudAlmacen]:

    return db.query(SolicitudAlmacen).options(
        joinedload(SolicitudAlmacen.detalle).joinedload(SolicitudAlmacenDetalle.articulo),
        joinedload(SolicitudAlmacen.cliente),
        joinedload(SolicitudAlmacen.contrato),
        joinedload(SolicitudAlmacen.autorizador),
        joinedload(SolicitudAlmacen.prcesador),
        joinedload(SolicitudAlmacen.registrador),
    ) .filter(SolicitudAlmacen.id==solicitud_id).first()


def get_solicitudes(
        db:Session,
        skip:int,
        limit:int=100,
        tipo:Optional[str]=None,
        estado:Optional[str]=None,
        id_cliente:Optional[int]=None,
        mes:Optional[int]=None,
        anio:Optional[int]=None,
) -> List[SolicitudAlmacen]:

    query=db.query(SolicitudAlmacen).options(
        joinedload(SolicitudAlmacen.detalle),
        joinedload(SolicitudAlmacen.cliente)
    )

    if tipo:
        query=query.filter(SolicitudAlmacen.tipo==tipo)
    if estado:
        query=query.filter(SolicitudAlmacen.estdo==estado)
    if id_cliente:
        query=query.filter(SolicitudAlmacen.id_cliente==id_cliente)
    if mes:
        query=query.filter(extract('month',SolicitudAlmacen.fecha_solicitud)==mes)
    if anio:
        query=query.filter(extract('year',SolicitudAlmacen.fecha_solicitud)==anio)

    return query.order_by(SolicitudAlmacen.fecha_solicitud.desc().offset(skip).limit(limit)).all()


def get_pendientes(db:Session)  -> List[SolicitudAlmacen]:
    """ Solicitudes pendientes de entrega, autorización o recolección """

    return db.query(SolicitudAlmacen).options(
        joinedload(SolicitudAlmacen.detalle),
        joinedload(SolicitudAlmacen.cliente)
    ).filter(
        SolicitudAlmacen.estdo.in_(["solicitud","autorizado"])
    ).order_by(SolicitudAlmacen.fecha_solicitud.asc()).all()


# ================= CREAR ========================
def create_solicitud(
        db:Session,
        data:SolicitudAlmacenCreate,
        registrado_por_id:int
) -> SolicitudAlmacen:

    # Validar cliente
    cliente=db.query(Cliente).filter(Cliente.id==data.id_cliente).first()

    if not cliente:
        raise ValueError("Cliente no encontrado")

    if data.tipo not in["entrega","recoleccion"]:
        raise ValueError("Tipo invalido. Debe ser 'entrega' o 'recoleccion' ")

    # Validar contrato si viene
    if data.id_contrato:
        contrato=db.query(Contrato).filter(Contrato.id==data.id_contrato).first()
        if not contrato:
            raise ValueError("Contrato no encontrado")
        if contrato.id_cliente != data.id_cliente:
            raise ValueError("El contrato no pertenece al cliente")

    # Validar que tenga detalle
    if not data.detalle:
        raise ValueError("La solicitud debe tener al menos un artículo ")

    # Determinar si se requiere autorización
    # Regla: sl la solicitud contiene refacciones/kits o mezcla, requiere autorización
    tipos_articulo=set()
    for item in data.detalle:
        articulo=db.query(Articulo).filter(Articulo.id==item.id_articulo).first()

        if not articulo:
            raise ValueError(f"Articulo ID {item.id_articulo} no encontrado")
        if not articulo.activo:
            raise ValueError(f"El articulo '{articulo.codigo}' no está activo")

        tipos_articulo.add(articulo.tipo)

        # Requere autorización si hay refacciones/kits o si hay mezcla de tipos
        requiere_aut=(
            "refaccion" in tipos_articulo
            or "kit" in tipos_articulo
            or len(tipos_articulo) > 1
        )

        # Validar seriales de tóners (si aplica)
        for item in data.detalle:
            articulo=db.query(Articulo).filter(Articulo.id==item.id_articulo).first()

            # Si es tóner, debe tener Serial
            if articulo.tipo=="toner":
                if not item.numero_serie_toner:
                    raise ValueError(f"El tóner '{articulo.codigo}' requere numero de serie")

                # Verificar que el serial no esté ya reservado en otra solicitud activa

                existente=db.query(SolicitudAlmacenDetalle).join(SolicitudAlmacen).filter(
                    and_(
                        SolicitudAlmacenDetalle.numero_serie_toner==item.numero_serie_toner,
                        SolicitudAlmacen.estdo.in_(["solicitud","autorizado"])
                    )
                ).first()

                if existente:
                    raise ValueError(
                        f"El tóner con serial '{item.numero_serie_toner}' ya está reservado "
                        f"En la solicitud {existente.id_solicitud}"
                    )

        # Generar folio
        folio=_generar_folio(db, data.tipo)

        # Estado Inicial
        estado_inicial="solicitud"

        # Crear la solicitud
        db_sol=SolicitudAlmacen(
            folio=folio,
            tipo=data.tipo,
            estado=estado_inicial,
            id_cliente=data.id_cliente,
            id_contrato=data.id_contrato,
            requiere_autorizacion=requiere_aut,
            chofer=data.chofer,
            observaciones=data.observaciones,
            registrado_por=registrado_por_id,
        )
        db.add(db_sol)
        db.flush()

        # Crear detalle
        for item in data.detalle:
            db_det=SolicitudAlmacenDetalle(
                id_solicitud=db_sol.id,
                id_articulo=item.id_articulo,
                cantidad=item.cantidad,
                numer_serie_toner=item.numero_serie_toner,
                observaciones=item.observaciones,
                estado="reservado"
            )
            db.add(db_det)

        db.commit()
        db.refresh(db_sol)

        return db_sol


# ============= ACTUALIZAR ==================
def update_solicitud(
        db:Session,
        solicitud_id:int,
        data:SolcitudAlmacenUpdate
) -> Optional[SolicitudAlmacen]:

    db_sol=get_solicitud(db,solicitud_id)
    if not db_sol:
        return None

    if db_sol.estdo in ["entregado","recolectado","cancelado"]:
        raise ValueError(f"No se puede editar una solicitud en estado '{db_sol.estdo}' ")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(db_sol,key,value)

    db.commit()
    db.refresh(db_sol)
    return db_sol

# ==================== AUTORIZAR ===================
def autorizar_solicitud(
        db:Session,
        solicitud_id:int,
        data:AutorizarSolicitudRequest,
        usuario_id:int
) -> SolicitudAlmacen:

    db_sol=get_solicitud(db,solicitud_id)

    if not db_sol:
        raise ValueError("Solicitud no encontrada")

    if not db_sol.requiere_autorizacion:
        raise ValueError("Esta solicitud no requiere autorización")

    if db_sol.estdo != "solicitud":
        raise ValueError(f"No se puede autorizar. Estado actual: '{db_sol.estdo}")

    db_sol.estado = "autorizado"
    db_sol.autorizado_por=usuario_id
    db_sol.fecha_autorizacion=datetime.now()

    if data.observaciones:
        db_sol.observaciones=(
            (db_sol.observaciones or "") + f"\n[Autorizacion] {data.observaciones}"
        ).strip()

        db.commit()
        db.refresh(db_sol)
        return db_sol


# ================ ENTREGAR (con devoluciones en el momento)===================
def entregar_solicitud(
        db:Session,
        solicitud_id:int,
        data:EntregarSolicitudRequest,
        usuario_id:int
) -> SolicitudAlmacen:
    """ Marca la solicitud como entregada, descuenta stock y registra devoluciones en el momento """

    db_sol=get_solicitud(db,solicitud_id)

    if not db_sol:
        raise ValueError("Solicitud no encontrada")

    if db_sol.tipo != "entrega":
        raise ValueError("Solo las solicitudes tipo 'entrega' se pueden entregar")

    if db_sol.requiere_autorizacion and db_sol.estdo != "autorizado":
        raise ValueError ("La solicitud requiere autorización antes de entregar")

    if db_sol.estdo not in ["solicitud","autorizado"]:
        raise ValueError(f"No se puede entregar. Estado actual: '{db_sol.estdo}")

    # Actualizar chofer si viene
    if data.chofer:
        db_sol.chofer=data.chofer

    # Marcar cada detalle como entregado o devuelto
    ids_vueltas=set(data.ids_detalle_devueltos or [])
    detalle_devueltas=[]

    for det in db_sol.detalle:
        if det.id in ids_vueltas:
            # No se entregó -> marcar como devuelta
            det.estado="devuelto"
            det.fecha_estado=datetime.now()
            detalle_devueltas.append(det)
        else:
            # Se entregó -> movimiento de salida + agregar al ministock del cliente
            try:
                crud_mov.create_movimiento(
                    db,
                    MovimientoAlmacenCreate(
                        id_articulo=det.id_articulo,
                        tipo="salida",
                        cantidad=det.cantidad,
                        numero_serie_toner=det.numero_serie_toner,
                        motivo=f"Entrega a cliente {db_sol.cliente_nombre}",
                        referencia=db_sol.folio,
                        id_solicitud_almacen=db_sol.id,
                    ),
                    registrado_por_id=usuario_id
                )
            except ValueError as e:
                raise ValueError(f"Error en artículo {det.articulo_codigo}: {str(e)}")

            # Agregar al ministock del cliente
            inv_cliente=InventarioCliente(
                id_cliente=db_sol.id_cliente,
                id_articulo=det.id_articulo,
                numero_serie_toner=det.numero_serie_toner,
                id_solicitud=db_sol.id,
                cantidad=det.cantidad,
                estado="en_cliente",
            )
            db.add(inv_cliente)

            det.estado="entregado"
            det.fecha_estado=datetime.now()

        # Determinar estado final
        if detalle_devueltas and len(detalle_devueltas)==len(db_sol.detalle):
            db_sol.estdo="devolucion_total"
        elif detalle_devueltas:
            db_sol.estdo="devolucion_parcial"
        else:
            db_sol.estado="entregado"

        db_sol.fecha_entrega=datetime.now()
        db_sol.procesado_por=usuario_id


        if data.observaciones:
            db_sol.observaciones=(
                (db_sol.observaciones or "") + f"\n[Entrega] {data.observaciones}"
            ).strip()

        if data.motivo_devolucion:
            db_sol.observaciones=(
                (db_sol.observaciones or "") + f"\n[Motivo devolución] {data.motivo_devolucion}"
            ).strip()

        db.commit()
        db.refresh(db_sol)
        return db_sol 

# ============== COMPLETAR RECOLECCION ======================

def completar_recoleccion(
        db:Session,
        solicitud_id:int,
        data:CompletarRecoleccionRequest,
        usuario_id:int
) -> SolicitudAlmacen:
    """ COmpleta una recolección: mueve los tóners recogidos a desecho y los resta del ministock"""

    db_sol=get_solicitud(db,solicitud_id)

    if not db_sol:
        raise ValueError("Solicitud no encontrada")

    if db_sol.tipo != "recoleccion":
        raise ValueError("Solo las solicitudes tipo 'recoleccion' se pueden completar")

    if db_sol.estdo != "solicitud":
        raise ValueError(f"No se puede completar. Estado actual: '{db_sol.estdo}'")


    # ID's de los detalles que efectivamente se recogieron
    ids_recogidaos = set(data.ids_detalle_recogidos or [])

    for det in db_sol.detalle:
        if det.id not in ids_recogidaos:
            # No se recogió -> se queda con el cliente
            continue

        # Verificar que el tóner está en el ministock del cliente
        inv_cliente=db.query(InventarioCliente).filter(
            and_(
                InventarioCliente.id_cliente==db_sol.id_cliente,
                InventarioCliente.numero_serie_toner==det.numero_serie_toner,
                InventarioCliente.estado=="en_cliente"
            )
        ).first()

        if not inv_cliente:
            raise ValueError(
                f"El tóner con serial '{det.numero_serie_toner}' no está en el ministock del cliente"
            )

        # Marcar como desecho en el ministock
        inv_cliente.estado="desecho"
        inv_cliente.fecha_devolucion=datetime.now()

        # Los tóners vacíos no se integran al stock del almacén (se van a desecho)
        # Pero registramos el movimiento para auditoría
        # Nota: com ono regresa al stock, No llamamos a create_movimiento

        det.estado="desecho"
        det.fecha_estado=datetime.now()

    db_sol.estdo="recolectado"
    db_sol.fecha_recoleccion=datetime.now()
    db_sol.procesado_por=usuario_id

    if data.observaciones:
        db_sol.observaciones=(
            (db_sol.observaciones or "") + f"\n[Recolección] {data.observaciones}"
        ).strip()

    db.commit()
    db.refresh(db_sol)
    
    return db_sol


# =============== DEVOLUCION POSTERIOR =========================

def registrar_devolucion_posterior(
        db:Session,
        solicitud_id:int,
        data:DevolucionPosteriorRequest,
        usuario_id:int
) -> SolicitudAlmacen:
    """ Registra una devolución posterior (días después de la entrega)"""

    db_sol=get_solicitud(db,solicitud_id)

    if not db_sol:
        raise ValueError("Solicitud no encontrada")

    if db_sol.tipo != "entrega":
        raise ValueError(" Solo aplica a solicitudes de entrega ")

    if db_sol.estdo not in ["entregado", "devolucion_parcial"]:
        raise ValueError(
            f"No se puede devolver. El estado actual: '{db_sol.estdo}'."
            f"Solo se devuelven entregas ya realizadas"
        )

    ids_devueltas=set(data.ids_detalle_devueltos)
    detalle_devueltos=[]

    for det in db_sol.detalle:
        if det.id not in ids_devueltas:
            continue

        if det.estado!="entregado":
            continue # Solo los que están entregados

        # Buscar en el ministock del cliente
        inv_cliente=db.query(InventarioCliente).filter(
            and_(
                InventarioCliente.id_cliente==db_sol.id_cliente,
                InventarioCliente.id_solicitud_entrega==db_sol.id,
                InventarioCliente.id_articulo==det.id_articulo,
                InventarioCliente.estado=="en_cliente"
            )
        ).first()

        if not inv_cliente:
            raise ValueError(
                f"No se encontró el artículo '{det.articulo_codigo}' en el ministock del cliente"
            )

        # Marcar como devuelto en el ministock
        inv_cliente.estado="devuelto"
        inv_cliente.fecha_devolucion=datetime.now()

        # Registrar movimiento de entrada(regresa al stock)

        try:
            crud_mov.create_movimiento(
                db,
                MovimientoAlmacenCreate(
                    id_articulo=det.id_articulo,
                    tipo="devolucion",
                    cantidad=det.cantidad,
                    numero_serie_toner=det.numero_serie_toner,
                    motivo=f"Devolución de cliente: {data.motivo_devolucion}",
                    referencia=db_sol.folio,
                    id_solicitud_almacen=db_sol.id,
                ),
                registrado_por_id=usuario_id,
            )
        except ValueError as e:
            raise ValueError(f"Error al registrar devolución: {str(e)}")


        det.estado="devuelto"
        det.fecha_estado=datetime.now()
        detalle_devueltos.append(det)

    if not detalle_devueltos:
        raise ValueError("No se especificaron artículos válidos para devolver")

    # Actualizar estado de la devolución
    # Verificar si todos los artículos entregados ya fueron devueltos
    
    total_entregados=len([d for d in db_sol.detalle if d.estado in ["entregado","devuleto"]])
    total_devueltos=len([d for d in db_sol if d.estado == "devuelto"])

    if total_devueltos >= total_entregados:
        db_sol.estdo="devolucion_total"
    else:
        db_sol.estdo="devolucion_parcial"

    db_sol.procesado_por=usuario_id

    if data.observaciones:
        db_sol.observaciones=(
            (db_sol.observaciones or "") + f"\n[Devolución Posterior] {data.observaciones}"
        ).strip()

    db.commit()
    db.refresh(db_sol)
    return db_sol


# ==================== CANCELAR ================

def cancelar_solicitud(
        db:Session,
        solicitud_id:int,
        data:CancelarSolicitudRequest,
        usuario_id:int,
) -> SolicitudAlmacen:

    db_sol=get_solicitud(db,solicitud_id)
    if not db_sol:
        raise ValueError("Solicitud no encontrada")

    if db_sol.estdo in ["entregado","recolectado","devolucion_total","cancelado"]:
        raise ValueError(
            f"No se puede cancelar. Estado actual: '{db_sol.estado}'."
            f"Si ya se entregó, se debe hacer una devolución"
        )

    # Liberar los seriales reservados
    for det in db_sol.detalle:
        if det.estado=="reservado":
            det.estado="devuelto" # Se libera la reserva
            det.fecha_estado=datetime.now()

    db_sol.estado="cancelado"
    db_sol.motivo_cancelacion=data.motivo_cancelacion
    db_sol.procesado_por=usuario_id

    db.commit()
    db.refresh(db_sol)
    return db_sol


# =========== ELIMINAR ==================

def delete_solicitud(
        db:Session,
        solicitud_id:int
) -> bool:

    db_sol=get_solicitud(db,solicitud_id)

    if not db_sol:
        return False

    if db_sol.estado in ["entregado","recolectado"]:
        raise ValueError("No se puede eliminar una solicitud ya procesada")

    db.delete(db_sol)
    db.commit()
    return True


# ============ DETALLE ========================

def agregar_detalle(
        db:Session,
        solicitud_id:int,
        item_data
) -> SolicitudAlmacenDetalle:
    """ Agrega un artículo a una solicitud existente """

    from app.schemas.solicitud_almacen_detalle import SolicitudAlmacenDetalleCreate

    db_sol=get_solicitud(db,solicitud_id)
    if not db_sol:
        raise ValueError("Solicitud no encontrada")

    if db_sol.estado not in ["solicitud","autorizado"]:
        raise ValueError(f"No se puede modificar una solicitud en estado '{db_sol.estdo}' ")

    articulo=db.query(Articulo).filter(Articulo.id==item_data.id_articulo).first()
    if not articulo:
        raise ValueError("Artículo no encontrado")

    # Validar serial de tóner
    if articulo.tipo == "toner":
        if not item_data.numero_serie_toner:
            raise ValueError(f"El tóner '{articulo.codigo}' requiere número de serie")

        existente=db.query(SolicitudAlmacenDetalle).join(SolicitudAlmacen).filter(
            and_(
                SolicitudAlmacenDetalle.numero_serie_toner==item_data.numero_serie_toner,
                SolicitudAlmacen.estado.in_(["solicitud","autorizado"]),
            )
        ).first()

        if existente:
            raise ValueError(f"El tóner ya está reservado en otra solicitud")

        db_det=SolicitudAlmacenDetalle(
            id_solicitud=solicitud_id,
            id_articulo=item_data.id_articulo,
            cantidad=item_data.cantidad,
            numero_serie_toner=item_data.numero_serie_toner,
            observaciones=item_data.observaciones,
            estado="reservado",
        )
        db.add(db_det)

        # Recalcular si requiere autorización
        tipos=set(d.articulo.tipo for d in db_sol.detalle)
        tipos.add(articulo.tipo)
        db_sol.requiere_autorizacion=(
            "refaccion" in tipos or "kit" in tipos or len(tipos) > 1
        )

        db.commit()
        db.refresh(db_det)
        return db_det

def delete_detalle(
        db:Session,
        detalle_id:int
) -> bool:

    db_det=db.query(SolicitudAlmacenDetalle).filter(
        SolicitudAlmacenDetalle.id==detalle_id
    ).first()

    if not db_det:
        raise ValueError("Solo se pueden eliminar artículos en estado 'reservado' ")

    db.delete(db_det)
    db.commit()
    return True


# ================ REPORTES ==================
def get_devoluciones(
        db:Session,
        fecha_inicio:Optional[date]=None,
        fecha_fin:Optional[date]=None,
        id_cliente:Optional[int]=None,
) -> List[SolicitudAlmacen]:
    """ Solicitudes con devoluciones parciales o totales"""

    query=db.query(SolicitudAlmacen).option(
        joinedload(SolicitudAlmacen.detalle),
        joinedload(SolicitudAlmacen.cliente),
    ).filter(
        SolicitudAlmacen.estdo.in_(
            ["devolucion_parcial","devolucion_total"]
        )
    )

    if fecha_inicio:
        query=query.filter(SolicitudAlmacen.fecha_solicitud >= fecha_inicio)

    if fecha_fin:
        query=query.filter(SolicitudAlmacen.fecha_solicitud <= fecha_fin )

    if id_cliente:
        query=query.filter(SolicitudAlmacen.id_cliente==id_cliente)

    return query.order_by(SolicitudAlmacen.fecha_solicitud.desc()).all()


    
        




    
    

