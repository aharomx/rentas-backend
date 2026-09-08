from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# ===================== DIRECCIONES ===================
class DireccionBase(BaseModel):
    tipo_direccion: str
    es_principal: bool = False
    calle: Optional[str] = None
    numero_exterior: Optional[str] = None
    numero_interior: Optional[str] = None
    colonia: Optional[str] = None
    codigo_postal: Optional[str] = None
    ciudad: Optional[str] = None
    estado: Optional[str] = None
    pais:str = "México"
    referencia: Optional[str] = None
    nombre_contacto: Optional[str] = None
    telefono_contacto: Optional[str] =  None
    email_contacto: Optional[EmailStr] = None
    horacion_atencion: Optional[str] = None
    Observaciones: Optional[str] = None

class DireccionCreate(DireccionBase):
    pass


class DirectionUpdate(DireccionBase):
    activo:Optional[bool] = None


class DireccionResponse(DireccionBase):
    id: int
    active:bool
    fecha_alta: datetime

    class config:
        from_attributes = True


# ============= CONTACTOS ===============
class ContactoBase(BaseModel):
    nombre: str 
    puesto: Optional[str] = None
    departamento: Optional[str] = None
    telefono_oficina: Optional[str] = None
    telefono_movil: Optional[str] = None
    email: Optional[EmailStr] = None
    email_alternativo: Optional[EmailStr] = None
    roles:Optional[List[str]]=None
    es_principal:bool=False
    observaciones:Optional[str]=None
    notas_internas: Optional[str] = None

class ContactoCreate(ContactoBase):
    pass

class ContactoUpdate(ContactoBase):
    activo: Optional[bool] = None


class ContactoResponse(ContactoBase):
    id:int
    activo:bool
    fecha_alta: datetime

    class Config:
        from_attributes = True



# =========== CLIENTES =================
class ClienteBase(BaseModel):
    razon_social: str
    nombre_comercial:Optional[str]=None
    rfc:Optional[str]=None
    email_empresa:Optional[EmailStr]=None
    telefono_empresa:Optional[str]=None
    pagina_web:Optional[str]=None
    tipo_persona:str="física"
    observaciones:Optional[str]=None

class ClienteCreate(ClienteBase):
    direcciones:Optional[List[DireccionCreate]]=[]
    contactos:Optional[List[ContactoCreate]]=[]

class ClienteUpdate(ClienteBase):
    activo:Optional[bool]=None

class ClienteResponse(ClienteBase):
    id:int
    activo:bool
    fecha_alta:datetime
    direcciones:List[DireccionResponse]=[]
    contactos:List[ContactoResponse]=[]

    class Config:
        from_attributes:True



