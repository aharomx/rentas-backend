from sqlalchemy.orm import Session
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteBase, ClienteUpdate, ClienteCreate
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
    db_cliente = Cliente(**cliente.model_dump())
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente



def update_cliente(db: Session, cliente_id: int, cliente_update:ClienteUpdate):
    db_cliente = get_cliente(db, cliente_id)

    if not db_cliente:
        return None

    for key, value in cliente_update.model_dump(exclude_unset=True).items:
        setattr(db_cliente, key, value)

    db.commit()
    db.refresh(db_cliente)
    return db_cliente

def delete_cliente(db: Session, cliente_id: int):
    db_cliente = get_cliente(db, cliente_id)

    if not db_cliente:
        return False

    db.delete(db_cliente)
    db.commit()
    return True
