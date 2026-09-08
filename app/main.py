from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import (
    clientes,
    modelos,
    equipos
)

from app.models import (
    Cliente,
    ModeloImpresora,
    Equipo
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


@app.get("/")
def root():
    return {"message":"Sistema de Control de Rentas de Impresoras API,", "Versión":"1.0.0"}

@app.get("/health")
def health_check():
    return {"status":"healthy"}

