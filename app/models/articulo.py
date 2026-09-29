from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Articulo(Base):
    __tablename__="articulos"

    id=Column(Integer,primary_key=True,index=True)
    codigo=Column(String(50),unique=True)
    nombre=Column(String(200),nullable=True)
    tipo=Column(String(50)) # toner, refaccion, kit
    modelo_compatible=Column(Integer,ForeignKey("modelos_impresoras.id"),nullable=True)
    stock_minimo=Column(Integer,default=3)
    unidad_medida=Column(String(20),default="PIEZA")

    