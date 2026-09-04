from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Equipo(Base):
    __tablename__ = "equipos"

    id = Column(Integer, primary_key=True, index=True)
    numero_serie = Column(String(50), unique=True, nullable=False)
    id_modelo = Column(Integer, ForeignKey("modelos_impresoras.id"))
    estado = Column(String(30), default="disponible") # disponible, rentado, reparación
    fecha_alta = Column(TIMESTAMP, server_default=func.now())
    fecha_baja = Column(TIMESTAMP, nullable=True)

    # Relación
    modelo = relationship("ModeloImpresora")