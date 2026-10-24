from sqlalchemy import (
    Column, Integer, String, Text, DECIMAL, Boolean, ForeignKey
)
from sqlalchemy.orm import relationship
from app.database import Base


class DetalleCobroEquipo(Base):
    __tablename__ = "detalle_cobro_equipos"

    id = Column(Integer, primary_key=True, index=True)
    id_documento = Column(
        Integer, ForeignKey("documentos_cobro.id", ondelete="CASCADE"), nullable=False
    )
    id_contrato_equipo = Column(
        Integer, ForeignKey("contrato_equipos.id"), nullable=True
    )

    # Snapshot del equipo
    numero_serie = Column(String(50), nullable=False)
    modelo = Column(String(200), nullable=True)
    es_color = Column(Boolean, default=False)
    tipo_lectura = Column(String(30), default="contadores")

    # Contadores
    contador_anterior_mono = Column(Integer, nullable=True)
    contador_actual_mono = Column(Integer, nullable=True)
    contador_anterior_color = Column(Integer, nullable=True)
    contador_actual_color = Column(Integer, nullable=True)

    # Impresiones directas
    impresiones_directas_mono = Column(Integer, nullable=True)
    impresiones_directas_color = Column(Integer, nullable=True)

    # Impresiones del mes
    impresiones_mes_mono = Column(Integer, default=0)
    impresiones_mes_color = Column(Integer, default=0)

    # Cargos
    renta_proporcional = Column(DECIMAL(12, 2), default=0)
    cargo_click_mono = Column(DECIMAL(12, 2), default=0)
    cargo_click_color = Column(DECIMAL(12, 2), default=0)
    cargo_excedente_mono = Column(DECIMAL(12, 2), default=0)
    cargo_excedente_color = Column(DECIMAL(12, 2), default=0)
    subtotal_equipo = Column(DECIMAL(12, 2), default=0)

    # Relaciones
    documento = relationship("DocumentoCobro", back_populates="detalles_equipos")
    contrato_equipo = relationship("ContratoEquipo")