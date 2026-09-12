from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre_completo = Column(String(200), nullable=False)
    telefono = Column(String(20), nullable=True)
    rol = Column(String(30), nullable=False)  # superuser, admin, coordinador, tecnico, almacenista
    activo = Column(Boolean, default=True)
    requiere_cambio_password = Column(Boolean, default=True)
    ultimo_acceso = Column(TIMESTAMP, nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_actualizacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    creado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Relaciones
    creador = relationship("Usuario", remote_side=[id], foreign_keys=[creado_por])