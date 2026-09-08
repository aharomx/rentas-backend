from sqlalchemy.orm import Session
from app.models.cliente import Cliente, DireccionCliente, ContactoCliente
from app.schemas.cliente import (
    ClienteBase, 
    ClienteUpdate, 
    ClienteCreate, 
    DireccionCreate, 
    ContactoCreate
    )
from typing import List, Optional


def get_cliente(db: Session, cliente_id:int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()

def get_cliente_by_rfc(db: Session, rfc=str):
    return db.query(Cliente).filter(Cliente.rfc == rfc).first()

def get_clientes(db:Session, skip:int=0, limit:int=100, activo:Optional[bool]= None):
    query = db.query(Cliente)
    if activo is not None:
        query = query.filter(Cliente.activo == activo)
    return query.offset(skip).limit(limit).all()

def create_cliente(db: Session, cliente: ClienteCreate):
    # Crear cliente
    db_cliente=Cliente(
        razon_social=cliente.razon_social,
        nombre_comercial=cliente.nombre_comercial,
        rfc=cliente.rfc,
        email_empresa=cliente.email_empresa,
        telefono_empresa=cliente.telefono_empresa,
        pagina_web=cliente.pagina_web,
        tipo_persona=cliente.tipo_persona,
        observaciones=cliente.observaciones
    )
    db.add(db_cliente)
    db.flush() # Para obtener el ID sin commit


    # Crear direcciones
    for direccion_data in cliente.direcciones:
        db_direccion = DireccionCliente(
            id_cliente=db_cliente.id,
            **contacto_data.model_dump()
        )
        db.add(db_direccion)

    # Crear contactos
    for contacto_data in cliente.contactos:
        db_contacto = ContactoCliente(
            id_cliente=db_cliente.id,
            **contacto_data.model_dump()
        )
        db.add(db_contacto)

    db.commit()
    db.refresh(db_cliente)
    return db_cliente


def update_cliente(db:Session, cliente_id:int, cliente_update:ClienteUpdate):
    db_cliente = get_cliente(db, cliente_id)
    if not db_cliente:
        return None

    # Actualizar campos del cliente
    for key, value in cliente_update.model_dump(exclude_unset=True).items():
        setattr(db_cliente, key, value)

    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def delete_cliente(db:Session, cliente_id:int):
    db_cliente=get_cliente(db, cliente_id)
    if not db_cliente:
        return False

    db.delete(db_cliente)
    db.commit()
    return True


# ========== CRUD PARA DIRECCIONES ===========
def get_direcciones_by_cliente(db:Session, cliente_id:int):
    return db.query(DireccionCliente).filter(
        DireccionCliente.id_cliente == cliente_id,
        DireccionCliente.activo == True
    ).all

def create_direccion(db:Session, cliente_id:int, direccion:DireccionCreate):
    db_direccion=DireccionCliente(
        id_cliente=cliente_id,
        **direccion.model_dump()
    )
    db.add(db_direccion)
    db.commit()
    db.refresh(db_direccion)
    return db_direccion

def delete_direccion(db:Session, direccion_id:int):
    db_direccion= db.query(DireccionCliente).filter(DireccionCliente.id==direccion_id).first()
    if not db_direccion:
        return False
    db.delete(db_direccion)
    db.commit()
    return True


# =========== CRUD PARA CONTACTOS ===============
def get_contactos_by_cliente(db:Session, cliente_id:int):
    return db.query(ContactoCliente).filter(
        ContactoCliente.id_cliente == cliente_id,
        ContactoCliente.activo==True
    ).all()

def get_contactos_by_role(db:Session, cliente_id:int, rol:str):
    return db.query(ContactoCliente).filter(
        ContactoCliente.id_cliente==cliente_id,
        ContactoCliente.roles.contains([rol]),
        ContactoCliente.activo==True
    ).all()

def create_contacto(db:Session, cliente_id:int, contacto:ContactoCreate):
    db_contacto=ContactoCliente(
        id_cliente=cliente_id,
        **contacto.model_dump()
    )
    db.add(db_contacto)
    db.commit()
    db.refresh(db_contacto)
    return db_contacto

def delete_contacto(db:Session, contacto_id:int):
    db_contacto=db.query(ContactoCliente).filter(ContactoCliente.id==contacto_id).first()
    if not db_contacto:
        return False
    db.delete(db_contacto)
    db.commit()
    return True

