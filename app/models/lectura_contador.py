from sqlalchemy import Column, Integer, Date,DECIMAL, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class LecturaContador(Base):
    __tablename__ = "lecturas_contadores"

    id=Column(Integer, primary_key=True, index=True)
    id_contrato_equipo=Column(Integer, ForeignKey("contrato_equipo.id", ondelete="CASCADE"), nullable=False)
    fecha_lectura=Column(Date, nullable=False)
    contador_mono=Column(Integer, nullable=False)
    contador_color=Column(Integer, nullable=False)
    porcentaje_toner_negro=Column(DECIMAL(5,2), nullable=True)
    porcentaje_toner_amarillo=Column(DECIMAL(5,2), nullable=True)
    porcentaje_toner_magenta=Column(DECIMAL(5,2), nullable=True)
    porcentaje_toner_cyan=Column(DECIMAL(5,2), nullable=True)
    porcentaje_unidad_imagen=Column(DECIMAL(5,2), nullable=True)
    fecha_captura=Column(TIMESTAMP, server_default=func.now())

    # Relación
    contrato_equipo = relationship("ContratoEquipo", back_populates="lecturas")

    
