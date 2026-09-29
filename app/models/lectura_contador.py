from sqlalchemy import Column, Integer, String, Date, DECIMAL, ForeignKey, TIMESTAMP, Text, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class LecturaContador(Base):
    __tablename__ = "lecturas_contadores"

    id = Column(Integer, primary_key=True, index=True)
    id_contrato_equipo = Column(Integer, ForeignKey("contrato_equipo.id", ondelete="CASCADE"), nullable=False)
    id_orden_lectura = Column(Integer, ForeignKey("ordenes_lectura.id"), nullable=True)

    fecha_lectura = Column(Date, nullable=False)
    tipo_lectura = Column(String(30), default="contadores")  # contadores, impresiones_directas

    # Para tipo "contadores"
    contador_mono = Column(Integer, nullable=True)
    contador_color = Column(Integer, nullable=True)
    contador_anterior_mono = Column(Integer, nullable=True)
    contador_anterior_color = Column(Integer, nullable=True)
    impresiones_mes_mono = Column(Integer, nullable=True)
    impresiones_mes_color = Column(Integer, nullable=True)

    # Para tipo "impresiones_directas"
    impresiones_directas_mono = Column(Integer, nullable=True)
    impresiones_directas_color = Column(Integer, nullable=True)

    # Porcentajes (opcionales)
    porcentaje_toner_negro = Column(DECIMAL(5, 2), nullable=True)
    porcentaje_toner_amarillo = Column(DECIMAL(5, 2), nullable=True)
    porcentaje_toner_magenta = Column(DECIMAL(5, 2), nullable=True)
    porcentaje_toner_cyan = Column(DECIMAL(5, 2), nullable=True)
    porcentaje_unidad_imagen = Column(DECIMAL(5, 2), nullable=True)

    # Auditoría
    observaciones = Column(Text, nullable=True)
    capturada_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_captura = Column(TIMESTAMP, server_default=func.now())

    # Correcciones
    es_correccion = Column(Boolean, default=False)
    lectura_original_id = Column(Integer, ForeignKey("lecturas_contadores.id"), nullable=True)
    motivo_correccion = Column(Text, nullable=True)

    # Relaciones
    contrato_equipo = relationship("ContratoEquipo", back_populates="lecturas")
    orden_lectura = relationship("OrdenLectura", back_populates="lecturas")
    capturador = relationship("Usuario", foreign_keys=[capturada_por])
    lectura_original = relationship("LecturaContador", remote_side=[id], foreign_keys=[lectura_original_id])

    # Propiedades calculadas
    @property
    def equipo_serie(self)->str | None:
        if self.contrato_equipo and self.contrato_equipo.equipo:
            return self.contrato_equipo.equipo.numero_serie
        return None

    @property
    def equipo_modelo(self)->str | None:
        if self.contrato_equipo and self.contrato_equipo.equipo and self.contrato_equipo.equipo.modelo:
            return self.contrato_equipo.equipo.modelo.nombre_modelo
        return None

    @property
    def ubicacion(self)->str | None:
        if self.contrato_equipo:
            return self.contrato_equipo.ubicacion
        return None