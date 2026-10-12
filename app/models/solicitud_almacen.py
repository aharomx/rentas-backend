from sqlalchemy import (
    Column, Integer, String, Text, Boolean, TIMESTAMP, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base



class SolicitudAlmacen(Base):
    __tablename__="solicitudes_almacen"

    id=Column(Integer,primary_key=True,index=True)
    folio=Column(String(30),unique=True,nullable=False,index=True)
    tipo=Column(String(20),nullable=False) # entrega | recoleccion
    estdo=Column(String(30),nullable=False, default="solicitud")
    # solicitud | autorizado | entregado | devolucion_parcial | 
    # devolucion_total | recolectado | cancelado

    # Relaciones
    id_cliente=Column(Integer,ForeignKey("clientes.id"),nullable=False)
    id_contrato=Column(Integer,ForeignKey("contratos.id"),nullable=True)

    # Autorización
    requiere_autorizacion=Column(Boolean,default=False)
    autorizado_por=Column(Integer,ForeignKey("usuarios.id"),nullable=True)
    fecha_autorizacion=Column(TIMESTAMP, nullable=True)

    # Fechas
    fecha_solicitud=Column(TIMESTAMP,server_default=func.now())
    fecha_entrega=Column(TIMESTAMP,nullable=True)
    fecha_recoleccion=Column(TIMESTAMP,nullable=True)

    # Chofer
    chofer=Column(String(200), nullable=True)

    # Observaciones y motivos
    observaciones=Column(Text,nullable=True)
    motivo_cancelacion=Column(Text,nullable=True)

    # Auditoria
    procesado_por=Column(Integer,ForeignKey("usuarios.id"),nullable=True)
    registrado_por=Column(Integer,ForeignKey("usuarios.id"),nullable=True)
    fecha_creacion=Column(TIMESTAMP,server_default=func.now())

    # Relaciones ORM
    cliente=relationship("Cliente")
    contrato=relationship("Contrato")
    autorizador=relationship("Usuario", foreign_keys=[autorizado_por])
    procesador=relationship("Usuario", foreign_keys=[procesado_por])
    registrador=relationship("Usuario",foreign_keys=[registrado_por])
    detalle=relationship(
        "SolicitudAlmacenDetalle",
        back_populates="solicitud",
        cascade="all, delete-orphan",
        order_by="SolicitudAlmacenDetalle.id"
    )

    # Propiedades calculadas
    @property
    def cliente_nombre(self) -> str | None:
        return self.cliente.razon_social if self.cliente else None

    @property
    def contrato_numero(self) -> int | None:
        return self.contrato.id if self.contrato else None

    @property
    def autorizador_nombre(self) -> str | None:
        return self.autorizador.nombre_completo if self.autorizador else None

    @property
    def procesador_nombre(self) -> str | None:
        return self.procesador.nombre_completo if self.procesador else None

    @property
    def total_articulos(self) -> str | None:
        return len(self.detalle) if self.detalle else 0

    
