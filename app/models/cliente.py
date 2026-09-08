from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Boolean, ForeignKey, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    razon_social = Column(String(200), nullable=False)
    nombre_comercial = Column(String(200), nullable=True)
    rfc = Column(String(20), unique=True, nullable=True)
    email_empresa = Column(String(100), nullable=True)
    telefono_empresa = Column(String(20), nullable=True)
    pagina_web = Column(String(200), nullable=True)
    tipo_persona = Column(String(20), default="física")
    activo = Column(Boolean, default=True)
    fecha_alta = Column(TIMESTAMP, server_default=func.now())
    observaciones = Column(Text, nullable=True) 


    # Relaciones
    direcciones = relationship("DireccionCliente", back_populates="cliente", cascade="all delete-orphan")
    contactos = relationship("ContactosCliente", back_populates="cliente", cascade="all delete-orphan")
    contratos = relationship("Contrato", back_populates="cliente") 


class DireccionCliente(Base):
    __tablename__ = "direcciones_ciente"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id"), ondelete="CASCADE", nullable=False)
    tipo_dirección = Column(String(30), nullable=False) #fiscal, entrega, facturación, correspondencia
    es_principal = Column(Boolean, default=False)

    calle = Column(String(200), nullable=True)
    numero_exterior = Column(String(20))
    numero_interior = Column(String(20))
    colonia = Column(String(100), nullable=True)
    codigo_postal = Column(String(10), nullable=True)
    ciudad = Column(String(100), nullable=True)
    estado = Column(String(100), nullable=True)
    pais = Column(String(50), default="Mexico")
    referancia = Column(Text, nullable=True)

    nombre_contacto = Column(String(100), nullable=True)
    telefono_contacto = Column(String(20), nullable=True)
    email_contacto = Column(String(100), nullable=True)
    horario_atencion = Column(String(100), nullable=True)

    activo = Column(Boolean, default=True)
    fecha_alta = Column(TIMESTAMP, server_default=func.now())
    observaciones = Column(Text, nullable=True)

    # Relación
    cliente = relationship("Cliente", back_populates="direcciones")


class ContactoCliente(Base):
    __tablename__ = "contactos_cliente"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, ForeignKey("clientes.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String(100), nullable=False)
    puesto = Column(String(100), nullable=True)
    departamento = Column(String(100), nullable=True)
    telefono_oficina = Column(String(20), nullable=True)
    telefono_movil = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    email_aternativo = Column(String(100), nullable=True)

    # Roles como array PostgreSQL
    roles = Column(ARRAY(String), nullable=True) # ['compras', 'entrega', 'it']

    es_principal = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)
    fecha_alta = Column(TIMESTAMP, server_default=func.now())
    observaciones = Column(Text, nullable=True)
    notas_internas = Column(Text, nullable=Text)

    # Relación
    cliente = relationship("Cliente", back_populates="contactos")