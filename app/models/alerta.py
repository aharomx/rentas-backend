from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Alerta(Base):
    __tablename__="alertas"

    id=Column(Integer,primary_key=True,index=True)

    # Tipo y prioridad
    tipo=Column(String(50),nullable=False,index=True)
    prioridad=Column(String(20),nullable=False,default="media") #alta | media | baja

    # Contenido
    titulo=Column(String(200),nullable=False)
    mensaje=Column(Text,nullable=True)

    #Referencia al objeto que causó la alerta
    referencia_tipo=Column(String(50),nullable=True)
    # contrato | equipo | articulo | documento | contrato_equipo | mantenimiento

    referencia_id=Column(Integer, nullable=True, index=True)

    # Estado
    estado=Column(String(20),nullable=False, default="nueva", index=True)
    # nueva | leida | atendida | descartada

    # Auditoría
    leida_por=Column(Integer, ForeignKey("usuarios.id"),nullable=True)
    fecha_lectura=Column(TIMESTAMP, nullable=True)
    atendida_por=Column(Integer,ForeignKey("usuarios.id"),nullable=True)
    fecha_atencion=Column(TIMESTAMP,server_default=func.now(),index=True)
    observaciones=Column(Text,nullable=True)

    fecha_creacion=Column(TIMESTAMP,server_default=func.now(),index=True)
    fecha_actualizacion=Column(TIMESTAMP,server_default=func.now(),onupdate=func.now())

    # Relaciones
    lector=relationship("Usuario",foreign_keys=[leida_por])
    atendio=relationship("Usuario",foreign_keys=[atendida_por])

    # Propiedades calculadas
    @property
    def leida_por_nombre(self) -> str | None:
        return self.lector.nombre_completo if self.lector else None

    def atendida_por_nombre(self) -> str | None:
        return self.atendio.nombre_completo if self.atendio else None
    