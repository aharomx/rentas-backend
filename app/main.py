from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import (
    clientes, modelos, equipos,
    tipos_plan, contratos, movimientos
)

from app.models import (
    Cliente, DireccionCliente, ContactoCliente,
    ModeloImpresora, Equipo,
    TipoPlan, Contrato, ContratoEquipo, MovimientoEquipo
)

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

app= FastAPI(
    title="Sistema de Control de Rentas de Impresoras",
    description="API para gestión de contratos, equipos, invetario y facturación",
    version="1.0.0"
)

# Configuración CORS (para conectar con Reflex)
app.middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción especificar origenes
    allow_credentials=True,
    Allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(clientes.router)
app.include_router(modelos.router)
app.include_router(equipos.router)
app.include_router(tipos_plan.router)
app.include_router(contratos.router)
app.include_router(movimientos.router)


@app.get("/")
def root():
    return {
        "message":"Sistema de Control de Rentas de Impresoras API,", 
        "Versión":"1.0.0",
        "endopoints": {
            "clientes":"/clientes",
            "modelos":"/modelos",
            "equipos":"/equipos",
            "tipos_plan":"/tipos_plan",
            "contratos":"/contratos",
            "movimientos":"/movimientos"
        }
        }

@app.get("/health")
def health_check():
    return {"status":"healthy"}

