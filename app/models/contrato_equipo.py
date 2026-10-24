from sqlalchemy import Column, Integer, ForeignKey, Date, Boolean, TIMESTAMP, Text, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class ContratoEquipo(Base):
    __tablename__ = "contrato_equipos"

    id = Column(Integer, primary_key=True, index=True)
    id_contrato = Column(Integer, ForeignKey("contratos.id", ondelete="CASCADE"), nullable=False)
    id_equipo = Column(Integer, ForeignKey("equipos.id"), nullable=False)

    fecha_ingreso = Column(Date, nullable=False)
    contador_inicial_mono = Column(Integer, nullable=False, default=0)
    contador_inicial_color = Column(Integer, nullable=True, default=0)
    contador_actual_mono = Column(Integer, nullable=True)
    contador_actual_color = Column(Integer, nullable=True)

    ubicacion = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    fecha_baja = Column(Date, nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())

    # Costos por equipo
    costo_renta_equipo=Column(DECIMAL(12,2),nullable=True)
    costo_click_mono_equipo=Column(DECIMAL(10,4), nullable=True)
    costo_click_color_equipo=Column(DECIMAL(10,4), nullable=True)

    # Relaciones
    # ⭐ Contrato apunta a "todos_equipos" (bidireccional)
    contrato = relationship("Contrato", back_populates="todos_equipos")
    equipo = relationship("Equipo")
    lecturas = relationship(
        "LecturaContador",
        back_populates="contrato_equipo",
        cascade="all, delete-orphan"
    )

    # Propiedades calculadas 
    
    @property
    def tiene_costos_diferenciados(self) -> bool:
        """ Indica si este equipo tiene costos propios (Plan costo_diferenciado)."""

        return any([
            self.costo_renta_equipo is not None,
            self.costo_click_mono_equipo is not None,
            self.costo_click_color_equipo is not None,
        ])

    