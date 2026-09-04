from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    razon_social = Column(String(200), nullable=True)
    rfc = Column(String(20), nullable=True)
    direccion = Column(Text, nullable=True)
    contacto = Column(String(100), nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_alta = Column(TIMESTAMP, server_default=func.now())

    