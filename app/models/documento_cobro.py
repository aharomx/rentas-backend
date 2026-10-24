from sqlalchemy import (
    Column, Integer, String, Text, TIMESTAMP, DECIMAL, ForeignKey
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class DocumentoCobro(Base):
    __tablename__ = "documentos_cobro"

    id = Column(Integer, primary_key=True, index=True)
    folio = Column(String(30), unique=True, nullable=False, index=True)
    tipo = Column(String(20), nullable=False)  # remision | nota_cargo | nota_credito
    id_documento_original = Column(
        Integer, ForeignKey("documentos_cobro.id"), nullable=True
    )

    # Relaciones
    id_contrato = Column(Integer, ForeignKey("contratos.id"), nullable=False)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), nullable=False)

    # Periodo
    mes = Column(Integer, nullable=True)
    anio = Column(Integer, nullable=True)

    # Fechas
    fecha_emision = Column(TIMESTAMP, server_default=func.now())
    estado = Column(String(20), default="borrador")  # borrador | emitido | cancelado

    # Ajuste (solo para notas)
    monto_ajuste = Column(DECIMAL(12, 2), nullable=True)
    motivo_ajuste = Column(Text, nullable=True)
    autorizado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)

    # Cálculos
    subtotal_renta = Column(DECIMAL(12, 2), default=0)
    subtotal_clicks_mono = Column(DECIMAL(12, 2), default=0)
    subtotal_clicks_color = Column(DECIMAL(12, 2), default=0)
    subtotal_excedente_mono = Column(DECIMAL(12, 2), default=0)
    subtotal_excedente_color = Column(DECIMAL(12, 2), default=0)
    descuento = Column(DECIMAL(12, 2), default=0)
    motivo_descuento = Column(Text, nullable=True)
    subtotal = Column(DECIMAL(12, 2), default=0)
    iva = Column(DECIMAL(12, 2), default=0)
    total = Column(DECIMAL(12, 2), default=0)

    # Metadatos
    observaciones = Column(Text, nullable=True)
    generado_por = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    ruta_pdf = Column(String(500), nullable=True)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())

    # Relaciones ORM
    contrato = relationship("Contrato")
    cliente = relationship("Cliente")
    documento_original = relationship(
        "DocumentoCobro", remote_side=[id], foreign_keys=[id_documento_original]
    )
    autorizador = relationship("Usuario", foreign_keys=[autorizado_por])
    generador = relationship("Usuario", foreign_keys=[generado_por])
    detalles_equipos = relationship(
        "DetalleCobroEquipo",
        back_populates="documento",
        cascade="all, delete-orphan",
        order_by="DetalleCobroEquipo.id",
    )
    detalles_bolsas = relationship(
        "DetalleCobroBolsa",
        back_populates="documento",
        cascade="all, delete-orphan",
        order_by="DetalleCobroBolsa.tipo",
    )

    # Propiedades calculadas
    @property
    def cliente_nombre(self) -> str | None:
        return self.cliente.razon_social if self.cliente else None

    @property
    def cliente_rfc(self) -> str | None:
        return self.cliente.rfc if self.cliente else None

    @property
    def contrato_numero(self) -> int | None:
        return self.contrato.id if self.contrato else None

    @property
    def generador_nombre(self) -> str | None:
        return self.generador.nombre_completo if self.generador else None

    @property
    def autorizador_nombre(self) -> str | None:
        return self.autorizador.nombre_completo if self.autorizador else None

    @property
    def periodo(self) -> str:
        if not self.mes or not self.anio:
            return "—"
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                 "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        return f"{meses[self.mes - 1]} {self.anio}"