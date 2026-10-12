from sqlalchemy import (
    Column, Integer, String, Text, Date, TIMESTAMP, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class InventarioCliente(Base):
    __tablename__="inventario_cliente"

    id=Column(Integer,primary_key=True,index=True)
    id_cliente=Column(Integer,ForeignKey("clientes.id"),nullable=False,index=True)
    id_articulo=Column(Integer,ForeignKey("articulos.id"),nullable=False,index=True)
    numero_serie_toner=Column(String(50),nullable=True,index=True)
    id_solicitud_entrega=Column(Integer,ForeignKey("solicitudes_almacen.id"),nullable=True)
    cantidad=Column(Integer,nullable=False,default=1) # Para artículos sin serial
    fecha_entrega=Column(TIMESTAMP,server_default=func.now())
    estado=Column(String(20),nullable=False,default="en_cliente")
    # en_cliente | devuelto | desecho
    fecha_devolucion=Column(TIMESTAMP,nullable=True)
    observaciones=Column(Text,nullable=True)

    # Relaciones
    cliente=relationship("Cliente")
    articulo=relationship("Articulo")
    solicitud_entrega=relationship("SolicitudAlmacen")

    # Propiedades calculadas
    @property
    def cliente_nombre(self) -> str | None:
        return self.cliente.razon_social if self.cliente else None

    @property
    def articulo_codigo(self) -> str | None:
        return self.articulo.codigo if self.articulo else None

    @property
    def articulo_nombre(self) -> str | None:
        return self.articulo.nombre if self.articulo else None

    @property
    def articulo_tipo(self) -> str | None:
        return self.articulo.tipo if self.articulo else None

    