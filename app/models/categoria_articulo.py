from sqlalchemy import Column, Integer, String, Text, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class CategoriaArticulo(Base):
    __tablename__="categorias_articulo"

    id=Column(Integer,primary_key=True,index=True)
    nombre=Column(String(100),unique=True,nullable=False)
    descripcion=Column(Text,nullable=True)
    activo=Column(Boolean,default=True)
    fecha_alta=Column(TIMESTAMP,server_default=func.now())

    # Relaciones
    articulos=relationship("Articulo",back_populates="categoria")
    