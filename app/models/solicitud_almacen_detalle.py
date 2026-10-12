from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class SolicitudAlmacenDetalle(Base):
    __tablename__="solicitud_almacen_detalle"

    id=Column(Integer,primary_key=True,index=True)
    id_solicitud=Column(
        Integer,
        ForeignKey("solicitudes_almacen.id",ondelete="CASCADE"),
        nullable=False,
    )
    id_articulo=Column(Integer,ForeignKey("articulos.id"),nullable=False)
    cantidad=Column(Integer,ForeignKey("articulos.id"),nullable=False)
    estado=Column(String(20),nullable=False,default="reservado")
    # reservado | entregado | devuelto | desecho
    observaciones=Column(Text,nullable=True)
    fecha_estado=Column(TIMESTAMP,server_default=func.now())

    # Relaciones
    solicitud=relationship("SolicitudAlmacen",back_populates="detalle")
    articulo=relationship("Articulo")

    # Propiedades
    @property
    def articulo_codigo(self) -> str | None:
        return self.articulo.codigo if self.articulo else None

    @property
    def articulo_nombre(self) -> str | None:
        return self.articulo.nombre if self.articulo else None

    @property
    def articulo_tipo(self) -> str | None:
        return self.articulo.tipo if self.articulo else None

    


