from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, Date, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Mantenimiento(Base):
    __tablename__="mantenimientos"


    id=Column(Integer,primary_key=True,index=True)
    folio=Column(String(30),unique=True,nullable=False,index=True)
    id_contrato=Column(Integer,ForeignKey("contratos.id"),nullable=False)

    # Tipo y estado
    tipo=Column(String(20),nullable=False) # preventivo | correctivo
    estado=Column(String(30),nullable=False,default="programado")
    # en_solicitud | programado | en_proceso | en_espera_refacciones | completado | cancelado

    # Autorización solo en correctivo
    autorizado_por=Column(Integer,ForeignKey("usuarios.id"), nullable=True)
    fecha_autorizacion=Column(TIMESTAMP,nullable=True)

    # Técnicos
    tecnico_asignado=Column(Integer,ForeignKey("usuarios.id"),nullable=True)
    tecnico_inicio=Column(Integer,ForeignKey("usuarios.id"),nullable=True)
    tecnico_fin=Column(Integer,ForeignKey("usuarios.id"),nullable=True)

    # Fechas
    fecha_solicitud=Column(TIMESTAMP,server_default=func.now())
    fecha_programada=Column(TIMESTAMP,nullable=True)
    fecha_inicio=Column(TIMESTAMP,nullable=True)
    fecha_fin=Column(TIMESTAMP,nullable=True)

    # Observaciones
    observaciones = Column(Text, nullable=True)
    motivo_cancelacion = Column(Text, nullable=True)
    motivo_espera = Column(Text, nullable=True)
    descripcion_problema = Column(Text, nullable=True)  # Para correctivos

    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    fecha_actualizacion = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relaciones
    contrato = relationship("Contrato")
    autorizador = relationship("Usuario", foreign_keys=[autorizado_por])
    tecnico_asignado_user = relationship("Usuario", foreign_keys=[tecnico_asignado])
    tecnico_inicio_user = relationship("Usuario", foreign_keys=[tecnico_inicio])
    tecnico_fin_user = relationship("Usuario", foreign_keys=[tecnico_fin])
    
    equipos = relationship(
        "MantenimientoEquipo",
        back_populates="mantenimiento",
        cascade="all, delete-orphan",
        order_by="MantenimientoEquipo.id"
    )

