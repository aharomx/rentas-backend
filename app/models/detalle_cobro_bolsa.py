from sqlalchemy import Column, Integer, String, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class DetalleCobroBolsa(Base):
    __tablename__ = "detalle_cobro_bolsas"

    id = Column(Integer, primary_key=True, index=True)
    id_documento = Column(
        Integer, ForeignKey("documentos_cobro.id", ondelete="CASCADE"), nullable=False
    )
    tipo = Column(String(20), nullable=False)  # mono | color
    bolsa_total = Column(Integer, nullable=False)
    impresiones_mes = Column(Integer, nullable=False)
    excedente = Column(Integer, default=0)
    costo_unitario = Column(DECIMAL(10, 4), default=0)
    cargo_excedente = Column(DECIMAL(12, 2), default=0)

    # Relaciones
    documento = relationship("DocumentoCobro", back_populates="detalles_bolsas")