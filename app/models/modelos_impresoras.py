from sqlalchemy import Column, Integer, String, TIMESTAMP, Boolean
from sqlalchemy.sql import func
from app.database import Base


class ModeloImpresora(Base):
    __tablename__ = "modelos_impresoras"

    id = Column(Integer,primary_key=True, index=True)
    nombre_modelo = Column(String(100), unique=True, nullable=False)
    es_color = Column(Boolean, default=False)
    velocidad_ppm = Column(Integer, nullable=True)
    rendimiento_toner_negro = Column(Integer, nullable=True)
    rendimiento_toner_color =Column(Integer, nullable=True)
    fecha_alta = Column(TIMESTAMP, server_default=func.now())


