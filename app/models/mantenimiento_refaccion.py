from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class MantenimientoRefaccion(Base):
    __tablename__="mantenimiento_refacciones"

    id=Column(Integer, primary_key=True, index=True)
    id_mantenimiento_equipo=Column(
        Integer,
        ForeignKey("mantenimiento_equipo.id",ondelete="CASCADE"),
        nullable=False
    )
    id_articulo=Column(Integer,ForeignKey("articulos.id"),nullable=False)
    cantidad=Column(Integer,nullable=False,default=1)
    numero_serie_toner=Column(String(50),nullable=True)
    observaciones=Column(Text,nullable=True)

    # Relaciones
    mantenimiento_equipo=relationship("MantenimientoEquipo",back_populates="refacciones")
    articulo=relationship("Articulo")

    