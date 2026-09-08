from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base

class TipoPlan(Base):
    __tablename__="tipos_plan"

    id=Column(Integer, primary_key=TIMESTAMP, index=True)
    nombre=Column(String(50), unique=True, nullable=False) # solo_renta, renta_click, renta_bolsa, solo_click
    descripcion=Column(Text,nullable=True)
    activo=Column(Boolean, default=True)
    fecha_alta=Column(TIMESTAMP, server_default=func.now())
    