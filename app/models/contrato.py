from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, ForeignKey, Date, DECIMAL, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Contrato(Base):
    __tablename__="contratos"

    id= Column(Integer, primary_key=True, index=True)
    id_cliente= Column(Integer, ForeignKey("clientes.id"), nullable=False)
    id_tipo_plan = Column(Integer, ForeignKey("tipos_plan.id"), nullable=False)

    # Fechas
    fecha_inicio= Column(Date, nullable=False)
    fecha_fin= Column(Date, nullable=False)
    activo= Column(Boolean, default=True)

    # Costos del plan (Negociados por contrato)
    costo_renta_mensual= Column(DECIMAL(12,2), default=0)
    costo_click_mono= Column(DECIMAL(10,4), default=0)
    costo_click_color= Column(DECIMAL(10,4), default=0)
    bolsa_mono= Column(Integer, default=0)
    bolsa_color= Column(Integer, default=0)
    costo_excedente_mono= Column(DECIMAL(10,4), default=0)
    costo_excedente_color= Column(DECIMAL(10,4), default=0)

    # Modo de captura
    modo_captura= Column(String(20), default="contadores") # 'contadores' o 'impresiones_directas'

    # Metadatos de negociación (para histórico)
    condiciones_especiales= Column(Text, nullable=True)
    observaciones = Column(Text, nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_actualizacion= Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    cliente = relationship("Cliente", back_populates="contratos")
    tipo_plan = relationship("TipoPlan")
    equipos_asignados = relationship("ContratoEquipo", back_populates="contrato", cascade="all, delete-orphan")
    movimientos = relationship("MovimientosEquipo", foreign_keys="MovimientoEquipo.id_contrato_origen", back_populates="contrato_origen")


