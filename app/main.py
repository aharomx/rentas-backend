from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

# ⭐ IMPORTAR TODOS LOS MODELOS
from app.models import (
    Cliente, DireccionCliente, ContactoCliente,
    ModeloImpresora, Equipo,
    TipoPlan, Contrato, ContratoEquipo, MovimientoEquipo
)

# ⭐ CREAR TABLAS SI NO EXISTEN
Base.metadata.create_all(bind=engine)

# ⭐ IMPORTAR ROUTERS
from app.routers import (
    clientes, modelos, equipos, 
    tipos_plan, contratos, movimientos
)

app = FastAPI(
    title="Sistema de Control de Rentas de Impresoras",
    description="API para gestión de contratos, equipos, inventario y facturación",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
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
        "message": "Sistema de Control de Rentas de Impresoras API",
        "version": "1.0.0",
        "endpoints": {
            "clientes": "/clientes",
            "modelos": "/modelos",
            "equipos": "/equipos",
            "tipos_plan": "/tipos-plan",
            "contratos": "/contratos",
            "movimientos": "/movimientos"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}