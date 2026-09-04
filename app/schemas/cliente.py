from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class ClienteBase(BaseModel):
    razon_social: Optional[str] = None
    rfc: Optional[str] = None
    direccion: Optional[str] = None
    contacto: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[EmailStr] = None

class ClienteCreate(ClienteBase):
    pass

class ClienteUpdate(ClienteBase):
    activo: Optional[bool] = None


class ClienteResponse(ClienteBase):
    id: int
    activo: bool
    fecha_alta: datetime

    class Config:
        from_attributes = True


        