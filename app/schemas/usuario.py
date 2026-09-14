from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UsuarioBase(BaseModel):
    username:str
    email: EmailStr
    nombre_completo: str
    telefono:Optional[str]=None
    rol:str #superuser, admin, coordinador, tecnico, almacenista


class UsuarioCreate(UsuarioBase):
    password:str 


class UsuarioUpdate(BaseModel):
    email:Optional[EmailStr]=None
    nombre_completo:Optional[str]=None
    telefono:Optional[str]=None
    rol:Optional[str]=None
    activo:Optional[bool]=None


class UsuarioResponse(UsuarioBase):
    id:int
    activo:bool
    requiere_cambio_password:bool
    ultimo_acceso:Optional[datetime]=None
    creado_por:Optional[int]=None

    class Config:
        from_attribute=True


# ============ AUTENTICACION =====================

class loginRequest(BaseModel):
    username:str 
    password:str 

class TokenResponse(BaseModel):
    access_token:str
    refresh_token:str 
    token_type:str="bearer"
    expires_in:int 

class RefreshTokenRequest(BaseModel):
    refresh_token:str

class CambiarPasswordRequest(BaseModel):
    password_actual:str 
    password_nueva:str 

class ResetPasswordRequest(BaseModel):
    password_nueva:str 

