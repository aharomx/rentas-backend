from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class AuditoriaAcceso(Base):
    __tablename__ = "auditoria_accesos"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    username_intento = Column(String(50), nullable=True)  # Por si el usuario no existe
    accion = Column(String(50), nullable=False)  # login, logout, cambio_password, crear_usuario, etc.
    ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    exito = Column(Boolean, default=True)
    detalle = Column(Text, nullable=True)
    fecha = Column(TIMESTAMP, server_default=func.now())

    # Relación
    usuario = relationship("Usuario")