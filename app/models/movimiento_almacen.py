from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class MovimientoAlmacen(Base):
    __tablename__="movimientos_almacen"

    id=Column(Integer,primary_key=True,index=True)
    id_articulo=Column(Integer,ForeignKey("articulos.id"),nullable=False,index=True)

    # Tipo de movimiento
    tipo=Column(String(30),nullable=False) #entrada, salida, devoucion, ajuste_positivo,ajuste_negativo,desecho

    # Cantidad
    cantidad=Column(Integer,nullable=False)
    numero_serie_toner=Column(String(50),nullable=True,index=True) # Para tóners

    # Stock
    stock_anterior=Column(Integer,nullable=False)
    stock_nuevo=Column(Integer,nullable=False)

    # Referencias
    motivo=Column(String(200),nullable=True)
    referencia=Column(String(100),nullable=True) # Folio de solicitud de Mantenimiento, etc.
    id_solicitud_almacen=Column(Integer,nullable=True) # FK futura
    id_mantenimiento=Column(Integer,ForeignKey("mantenimientos.id"),nullable=True)

    # Observaciones
    observaciones=Column(Text,nullable=True)

    # Auditoria
    registrado_por=Column(Integer,ForeignKey("usuarios.id"),nullable=True)
    fecha_movimiento=Column(TIMESTAMP,server_default=func.now())

    # Relaciones
    articulo=relationship("Articulo",back_populates="movimientos")
    usuario=relationship("Usuario",foreign_keys=[registrado_por])
    mantinimiento=relationship("Mantenimiento",foreign_keys=[id_mantenimiento])

    # Propiedades calculadas
    @property
    def articulo_nombre(self) -> str | None:
         return self.articulo.codigo if self.articulo else None

    @property
    def articulo_nombre(self) -> str | None:
         return self.articulo.nombre if self.articulo else None

    @property
    def usuario_nombre(self) -> str | None:
         return self.usuario.nombre_completo if self.usuario else None

    