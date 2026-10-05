from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Articulo(Base):
    __tablename__="articulos"

    id=Column(Integer,primary_key=True,index=True)
    codigo=Column(String(50),unique=True,nullable=False,index=True)
    nombre=Column(String(200),nullable=True)
    tipo=Column(String(50),nullable=False) # toner, refaccion, kit
    id_categoria=Column(Integer,ForeignKey("categorias_articulo.id"),nullable=True)
    modelo_compatible=Column(Integer,ForeignKey("modelos_impresoras.id"),nullable=True)

    #stock
    stock_minimo=Column(Integer,default=5)
    stock_actual = Column(Integer, default=0)
    
    # Unidad
    unidad_medida=Column(String(20),default="PIEZA")

    # Estado
    activo=Column(Boolean,default=True)
    fecha_alta=Column(TIMESTAMP,server_default=func.now())
    fecha_actualizacion=Column(TIMESTAMP,server_default=func.now(),onupdate=func.now())

    #Relaciones
    categoria = relationship("CategoriaArticulo", back_populates="articulos")
    modelo = relationship("ModeloImpresora")
    movimientos = relationship("MovimientoAlmacen", back_populates="articulo", order_by="MovimientoAlmacen.id.desc()")
    

    