from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioUpdate,
    UsuarioResponse,
    ResetPasswordRequest
)
from app.crud import usuario as crud_usuario
from app.crud import auditoria as crud_auditoria
from app.security import get_current_user, require_roles

router=APIRouter(prefix="/usuarios", tags=["Usuarios"])

def _get_cliente_info(request:Request):

    ip=request.client.host if request.client else None
    user_agent=request.headers.get("user-agent")
    return ip, user_agent


@router.get("/", response_model=List[UsuarioResponse])
def read_usuarios(
    skip:int=0,
    limit:int=100,
    activo:Optional[bool]=None,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser", "admin"]))
):
    """ Lista de usuarios. Solo Superuser y admin """

    return crud_usuario.get_usuarios(db, skip=skip, limit=limit, activo=activo)

@router.get("/{usuario_id}", response_model=UsuarioResponse)
def read_usuario(
    usuario_id:int,
    db:Session=Depends(get_db),
    current_user = Depends(require_roles(["superuser", "admin"]))
):
    db_usuario=crud_usuario.get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return db_usuario

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def create_usuario(
    request:Request,
    usuario:UsuarioCreate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser"]))  # ⚠️ Solo superuser
):
    """ Crea un usuario nuevo. Solo superuser """
    ip, user_agent = _get_cliente_info(request)

    # Validar que el username no exista
    if crud_usuario.get_usuario_by_username(db, usuario.username):
        raise HTTPException(
            status_code=400,
            detail="El username ya está en uso"
        )

    # Validar que el email no exista
    if crud_usuario.get_usuario_by_email(db, usuario.email):
        raise HTTPException(
            status_code=400,
            detail="El email ya es en uso"
        )

    # Validar rol no permitido
    roles_validos=["superuser","admin","coordinador","tecnico","almacenista"]

    if usuario.rol not in roles_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido, Debe ser uno de: {roles_validos}"
        )

    # Validar longitud de password
    if len(usuario.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 8 caracteres"
        )

    db_usuario = crud_usuario.create_usuario(db, usuario, creado_por_id=current_user.id)

    crud_auditoria.registrar_acceso(
        db,
        accion="crear_usuario",
        id_usuario=current_user.id,
        ip=ip,
        user_agent=user_agent,
        exito=True,
        detalle=f"Creado usuario '{db_usuario.username}' con rol '{db_usuario.rol}' "
    )

    return db_usuario


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def update_usuario(
    request:Request,
    usuario_id:int,
    usuario_update:UsuarioUpdate,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser", "admin"]))
):
    """ Actualiza un usuario, Superuser y admin """

    db_usuario=crud_usuario.get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(
            status_code=400,
            detail="Usuario no encontrado"
        )

    # Validar email duplicado
    if usuario_update.email:
        existing=crud_usuario.get_usuario_by_email(db, usuario_update.email)

        if existing and existing.id != usuario_id:
            raise HTTPException(
                status_code=400,
                detail="El mail ya está en uso"
            )

    # Validar rol
    if usuario_update.rol:
        roles_validos = ["superuser", "admin", "coordinador", "tecnico", "almacenista"]

        if usuario_update.rol not in roles_validos:
            raise HTTPException(
                status_code=400,
                detail= f"Rol invalido. Debe ser un de: {roles_validos}"
            )


    # Un admin no puede modificar a un superuser
    if current_user.rol=="admin" and db_usuario.rol=="superuser":
        raise HTTPException(
            status_code=403,
            detail="Un admin no puede modificar a un superuser"
        )

    db_usuario=crud_usuario.update_usuario(db,usuario_id, usuario_update)

    ip, user_agent = _get_cliente_info

    crud_auditoria.registrar_acceso(
        db,
        accion="actualizar usuario",
        id_usuario=current_user.id,
        ip=ip,
        user_agent=user_agent,
        exito=True,
        detalle=f"Actualizado usuario id={usuario_id}"
    )


    return db_usuario



@router.post("/{usuario_id}/reset-passqword")
def reset_password(
    request:Request,
    usuario_id:int,
    payload:ResetPasswordRequest,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser"])) # ⚠️ Solo superuser
):
    """ Resetea la contraseña de un usuario, Solo superuser """

    db_usuario=crud_usuario.get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if len(payload.password_nueva) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contraseña debe tener al menos 8 caracteres"
        )

    db_usuario=crud_usuario.reset_password(db, db_usuario, payload.password_nueva)

    ip, user_agent=_get_cliente_info(request)

    crud_auditoria.registrar_acceso(
        db,
        accion="reset_password",
        id_usuario=current_user.id,
        ip=ip,
        user_agent=user_agent,
        exito=True,
        detalle=f"Password reseteado para el usaurio id={usuario_id}"
    )

    return db_usuario

@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_usuario(
    request:Request,
    usuario_id:int,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser"]))
):
    """ Desactiva el usuario (no lo elimina físicamente). Solo superuser """

    db_usuario=crud_usuario.get_usuario(db, usuario_id)
    if not db_usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    if db_usuario.id==current_user.id:
        raise HTTPException(
            status_code=404,
            detail="No puedes desactivar tu propio usuario"
        )

    db_usuario.activo=False
    db.commit()

    ip, user_agent=_get_cliente_info
    crud_auditoria.registrar_acceso(
        db,
        accion="desactivar usuario",
        id_usuario=current_user.id,
        ip=ip,
        user_agent=user_agent,
        exito=True,
        detalle=f"Desactivado usuario id={usuario_id}"
    )

    return None

# ======== AUDITORIA ===============

@router.get("/auditoria/accesos")
def read_auditoria(
    skip:int=0,
    limit:int=100,
    id_usuario:Optional[int]=None,
    accion:Optional[str]=None,
    db:Session=Depends(get_db),
    current_user=Depends(require_roles(["superuser","admin"]))
):
    """ Lista los registros de auditoría """

    return crud_auditoria.get_auditoria(
        db, skip=skip, limit=limit, id_usuario=id_usuario, accion=accion
    )

