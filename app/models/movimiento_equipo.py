from sqlalchemy import Column, Integer, ForeignKey, String, TIMESTAMP, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class MovimientoEquipo(Base):
    __tablename__ = "movimientos_equipos"

    id= Column(Integer, primary_key=True, index=True)
    id_equipo= Column(Integer, ForeignKey("equipos.id"), nullable=True)
    id_contrato_origen= Column(Integer, ForeignKey("contratos.id"), nullable=True)
    id_contrato_destino= Column(Integer, ForeignKey("contratos.id"), nullable=True)

    tipo_movimiento= Column(String(30), nullable=False) # 'alta', 'cambio_ubicacion', 'baja', 'transferencia'
    fecha_movimiento= Column(TIMESTAMP, server_default=func.now())
    observaciones= Column(Text, nullable=True)

    # Relaciones
    equipo= relationship("Equipo")
    contrato_origen= relationship("Contrato", foreign_keys=[id_contrato_origen])
    contrato_destino= relationship("Contrato", foreign_keys=[id_contrato_destino])