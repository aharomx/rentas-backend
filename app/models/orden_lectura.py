from sqlalchemy import Column, Integer, String, TIMESTAMP, Date, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class OrdenLectura(Base):
    __tablename__="ordenes_lectura"

    id=Column(Integer, primary_key=True, index=True)
    id_contrato=Column(Integer,ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False)
    fecha_generacion=Column(TIMESTAMP, server_default=func.now())
    fecha_limite=Column(Date, nullable=True)
    estado=Column(String(20), default="pendiente") # pendiente, completa, cancelada
    generada_por=Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    completada_en=Column(TIMESTAMP, nullable=True)
    observaciones=Column(Text,nullable=True)

    # Relaciones
    
    contrato=relationship("Contrato")
    generador=relationship("Usuario", foreign_keys=[generada_por])
    lecturas=relationship("LecturaContador", back_populates="orden_lectura")

    