from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, Date, DECIMAL, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class MantenimientoEquipo(Base):
    __tablename__ = "mantenimiento_equipo"

    id=Column(Integer,primary_key=True,index=True)
    id_mantenimiento=Column(Integer,ForeignKey("mantenimientos.id", ondelete="CASCADE"),nullable=False)
    id_equipo=Column(Integer,ForeignKey("equipos.id"), nullable=False)

    # Contadores (INFORMATIVOS - no afecta facturación)
    contador_mono=Column(Integer,nullable=True)
    contador_color=Column(Integer,nullable=True)

    # Porcentajes
    porcentaje_toner_negro=Column(DECIMAL(5,2),nullable=True)
    porcentaje_toner_amarillo=Column(DECIMAL(5,2),nullable=True)
    porcentaje_toner_magenta=Column(DECIMAL(5,2),nullable=True)
    porcentaje_toner_cyan=Column(DECIMAL(5,2),nullable=True)
    porcentaje_unidad_imagen=Column(DECIMAL(5,2),nullable=True)

    # Trabajos
    trabajos_realizados=Column(Text,nullable=True)
    observaciones=Column(Text,nullable=True)

    # Próximo mantenimiento
    proximo_mantenimiento_fecha=Column(Date,nullable=True)
    proximo_mantenimiento_contador=Column(Integer,nullable=True)

    fecha_registro=Column(TIMESTAMP,server_default=func.now())

    # Relaciones
    mantenimiento=relationship("Mantenimiento",back_populates="equipos")
    equipo=relationship("Equipo")
    refacciones=relationship(
        "MantenimientoRefaccion",
        back_populates="mantenimiento_equipo",
        cascade="all, delete-orphan"
    )

    # Propiedades calculadas
    @property
    def equipo_serie(self) -> str | None:
        return self.equipo.numero_serie if self.equipo else None

    @property
    def equipo_modelo(self) -> str | None:
        if self.equipo and self.equipo.modelo:
            return self.equipo.modelo.nombre_modelo
        return None

    