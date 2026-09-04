from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.modelo_impresora import ModeloImpresoraResponse


class EquipoBase(BaseModel):
    numero_serie: str
    id_modelo: int
    estado: str = "disponible"

class EquipoCreate(EquipoBase):
    pass


class EquipoUpdate(BaseModel):
    estado: Optional[str] = None
    fecha_baja: Optional[datetime] = None


class EquipoResponse(EquipoBase):
    id: int
    fecha_alta: Optional[datetime]
    modelo: Optional[ModeloImpresoraResponse] = None

    class Config:
        from_attributes = True
        