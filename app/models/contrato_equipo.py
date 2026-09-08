from sqlalchemy import Column, Integer, ForeignKey, Date,Boolean, TIMESTAMP, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class ContratoEquipo(Base):
    __tablename__="Contrato_equipos"

    id= Column(Integer, primary_key=True, index=True)
    id_contrato= Column(Integer, ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False)
    id_equipo= Column(Integer, ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False)

    fecha_ingreso= Column(Date, nullable=False)
    contador_inicial_contrato= Column(Integer, nullable=False) # Contador al ingresar a este contrato
    contador_actual= Column(Integer, nullable=True) # Ultimo contador capturado
    ubicacion= Column(Text, nullable=True) # Ubicación física del equipo

    activo= Column(Boolean, default=True)
    fecha_baja= Column(Date, nullable=True)
    fecha_creacion= Column(TIMESTAMP, server_default=func.now())

    # Relaciones

    contrato= relationship("Contrato", back_populates="equipos_asignados")
    equipo= relationship("Equipo")
    lecturas= relationship("LecturaContador", back_populates="contrato_equipo", cascade="all, delete-orphan")

        