from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database import get_db
from app.config import settings
from app.schemas.usuario import(
    TokenResponse, 
    RefreshTokenRequest,
    CambiarPasswordRequest
)
from app.crud import usuario as crud_usuario
from app.crud import auditoria as crud_auditoria
from app.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user
)

router=APIRouter(prefix="/auth",tags=["Autenticación"])

def _get_client_info(request:Request):
    """ Extrae IP y User-Agent del Request """

    ip=request.client.host if request.client else None
    user_agent=request.headers.get("user-agent")
    return ip, user_agent


@router.post("/login", response_model=TokenResponse)
def login(
    request:Request,
    form_data:OAuth2PasswordRequestForm=Depends(),
    db:Session=Depends(get_db)
):
    """ Login con username y password, Devuelve accesos y refresh tokens. """

    ip, user_agent=_get_client_info(request)

    usuario=crud_usuario.get_usuario_by_username(db, form_data.username)

    if not usuario or not verify_password(form_data.password, usuario.password_hash):

        # Registrar intento fallido
        crud_auditoria.registrar_acceso(
            db,
            accion="login",
            username_intento=form_data.username,
            ip=ip,
            user_agent=user_agent,
            exito=False,
            detalle="Credenciales incorrectas"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW.Authenticate":"Bearer"}
        )

    if not usuario.activo:
        crud_auditoria.registrar_acceso(
            db,
            accion="login",
            username_intento=form_data.username,
            ip=ip,
            user_agent=user_agent,
            exito=False,
            detalle="Usuario inactivo"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    # Actualizar último acceso
    crud_usuario.actualiazar_ultimo_acceso(db, usuario)


    # Registar el login exitoso
    crud_auditoria.registrar_acceso(
        db,
        accion="login",
        id_usuario=usuario.id,
        ip=ip,
        user_agent=user_agent,
        exito=True
    )

    # Crear tokens
    
    token_data={"sub":usuario.username,"rol":usuario.rol,"id":usuario.id}
    access_token=create_access_token(token_data)
    refresh_token=create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES*60
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request:Request,
    payload:RefreshTokenRequest,
    db:Session=Depends(get_db)
):
    """ Renueva el acess token usando un refresh token válido """

    decoded=decode_token(payload.refresh_token)

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token invalido"
        )

    username=decoded.get("sub")
    usuario=crud_usuario.get_usuario_by_username(db,username)


    if not usuario or not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no valido"
        )

    token_data={"sub":usuario.username,"rol":usuario.rol,"id":usuario.id}
    access_token=create_access_token(token_data)
    new_refresh_token=create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
def logout(
    request:Request,
    current_user=Depends(get_current_user),
    db:Session=Depends(get_db)
):
    """ Cierra la sesión (Registra el evento). El cliente debe eliminar sus tokens """

    ip, user_agent = _get_client_info(request)

    crud_auditoria.registrar_acceso(
        db,
        accion="logout",
        id_usuario=current_user.id,
        ip=ip,
        user_agent=user_agent,
        exito=True
    )

    return {"mensaje":"Sesión cerrada correctamente"}

@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    """Obtiene la información del usuario autenticado """
    return {
        "id":current_user.id,
        "username":current_user.username,
        "email":current_user.email,
        "nomnbre_completo":current_user.nombre_completo,
        "rol":current_user.rol,
        "activo":current_user.activo,
        "require_cambio_password":current_user.requiere_cambio_password,
        "ultimo_acceso":current_user.ultimo_acceso
    }

@router.post("/cambiar-password")
def cambiar_password(
    request:Request,
    payload:CambiarPasswordRequest,
    current_user=Depends(get_current_user),
    db:Session=Depends(get_db)
):
    """ Cambia la contraseña del usuario autenticado """
    ip, user_agent = _get_client_info(request)

    if not verify_password(payload.password_actual, current_user.password_hash):
        crud_auditoria.registrar_acceso(
            db,
            accion="cambio_password",
            id_usuario=current_user.id,
            ip=ip,
            user_agent=user_agent,
            exito=False,
            detalle="Contraseña actual incorrecta"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )

    if len(payload.password_nueva) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La nueva contraseña debe tener al menos 8 caracteres"
        )

    

    crud_usuario.cambiar_password(db, current_user, payload.password_nueva)

  
    

    crud_auditoria.registrar_acceso(
        db,
        accion="cambio_password",
        id_usuario=current_user.id,
        ip=ip,
        user_agent=user_agent,
        exito=True
    )

    return {"mensaje":"Contraseña cambiada corréctamente"}