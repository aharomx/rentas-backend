from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db

# Contexto de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema OAuth2 (para swagger)
oauth2_scheme=OAuth2PasswordBearer(tokenUrl="/auth/login")


# ================= HASH de PASSWORDS =======================

def hash_password(password:str) -> str:
    """ Convierte una contraseña en su hash bcrypt """
    return pwd_context.hash(password)

def verify_password(plain_password: str, password_hash:str) -> bool:
    """ Verifica si una contraseña coincide con su hash """
    return pwd_context.verify(plain_password, password_hash)

# ================= JWT ===============================

def create_access_token(data:dict, expires_delta:Optional[timedelta]=None)-> str:
    """ Crea un token de acceso JWT """
    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+(
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp":expire, "type":"access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data:dict) -> str:
    """ Crea un token de refresco JWT """

    to_encode=data.copy()
    expire=datetime.now(timezone.utc)+timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp":expire, "type":"refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    """ Decodifiva un token JWT """
    try:
        payload=jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o exprirado",
            headers={"WWW-Authenticate":"Bearer"},
        )


# =============== DEPENDENCIAS ======================

def get_current_user(
        token: str=Depends(oauth2_scheme),
        db:Session=Depends(get_db)
):
    """ Obtiene el usuario actual a partir del token """
    from app.models.usuario import Usuario

    payload = decode_token(token)

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tipo de token inválido"
        )

    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta el usuario"
        )

    usuario = db.query(Usuario).filter(Usuario.username==username).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario Inactivo"
        )

    return usuario

def require_roles(roles_permitidos: list[str]):
    """ Dependencia que valida que el usuario tienga uno de los roles permiitidos """

    def role_checker(current_user=Depends(get_current_user)):
        if current_user.rol not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tiene permisos. Roles permitidos: {roles_permitidos}"
            )
        return current_user
    return role_checker
