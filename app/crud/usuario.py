from sqlalchemy.orm import Session
from typing import Optional, List
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate
from app.security import hash_password


def get_usuario(db:Session,usuario_id:int) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.id==usuario_id).first()

def get_usuario_by_username(db:Session,username:str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.username==username).first()

def get_usuario_by_email(db:Session, email:str) -> Optional[Usuario]:
    return db.query(Usuario).filter(Usuario.email==email).first()

def get_usuarios(
        db:Session,
        skip:int=0,
        limit:int=100,
        activo:Optional[bool]=None
) -> List[Usuario]:
    query=db.query(Usuario)
    if activo is not None:
        query=query.filter(Usuario.activo==activo)
    return query.offset(skip).limit(limit).all()

def create_usuario(
        db:Session,
        usuario:UsuarioCreate,
        creado_por_id:int
)  -> Usuario:
    db_usuario=Usuario(
        username=usuario.username,
        email=usuario.email,
        password_hash=hash_password(usuario.password),
        nombre_completo=usuario.nombre_completo,
        telefono=usuario.telefono,
        rol=usuario.rol,
        requiere_cambio_password=True,
        creado_por=creado_por_id
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario


def update_usuario(
        db:Session,
        usuario_id:int,
        usuario_update:UsuarioUpdate
) -> Optional[Usuario]:
    db_usuario=get_usuario(db,usuario_id)
    if not db_usuario:
        return None
    for key, value in usuario_update.model_dump(exclude_unset=True).items():
        setattr(db_usuario,key,value)
        db.commit()
        db.refresh(db_usuario)
        return db_usuario



def cambiar_password(db:Session,usuario:Usuario,nueva_password:str)-> Usuario:
    usuario.password_hash = hash_password(nueva_password)
    usuario.requiere_cambio_password = False
    db.commit()
    db.refresh(usuario)
    return usuario


def reset_password(db:Session,usuario:Usuario,nueva_password:str)-> Usuario:
    """ Reset por superuser - el usuario deberá cambiar al siguiente login """
    usuario.password_hash=hash_password(nueva_password)
    usuario.requiere_cambio_password=True
    db.commit()
    db.refresh(usuario)
    return usuario


def actualiazar_ultimo_acceso(db:Session, usuario:Usuario) -> None:
    from sqlalchemy.sql import func
    usuario.ultimo_acceso=func.now()
    db.commit()

