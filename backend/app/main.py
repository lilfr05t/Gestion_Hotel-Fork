import os
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.database import Base, engine
from app.models.bayesian_model import predecir_servicio
from app.routers import (
    administracion,
    autenticacion,
    codigos_acceso,
    facturacion,
    habitaciones,
    historial,
    huespedes,
    notas_servicio,
    parking,
    reservas,
    servicios,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión Hotelera (PMS)",
    description="API para el control de usuarios, habitaciones, reservas y facturación.",
    version="1.0.0",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "https://gestion-hotel-168m.onrender.com,https://gestion-hotel-backend-ilge.onrender.com,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

# Ensure local dev origins are present to avoid accidental CORS blocking during development
_dev_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
for _o in _dev_origins:
    if _o not in allowed_origins:
        allowed_origins.append(_o)

print("CORS allowed_origins:", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(autenticacion.router, prefix="/api/v1")
app.include_router(habitaciones.router, prefix="/api/v1")
app.include_router(huespedes.router, prefix="/api/v1")
app.include_router(reservas.router, prefix="/api/v1")
app.include_router(servicios.router, prefix="/api/v1")
app.include_router(facturacion.router, prefix="/api/v1")
app.include_router(administracion.router, prefix="/api/v1")
app.include_router(parking.router, prefix="/api/v1")
app.include_router(notas_servicio.router, prefix="/api/v1")
app.include_router(historial.router, prefix="/api/v1")
app.include_router(codigos_acceso.router, prefix="/api/v1")


class PredictUpsellingRequest(BaseModel):
    Tipo_Habitacion: str
    Piso_Habitacion: str
    Procedencia_Huesped: str
    Dias_Estadia: int


@app.get("/", tags=["General"])
def read_root():
    return {"mensaje": "API del Sistema Hotelero en línea y conectada a MySQL"}


@app.post("/api/predict-upselling", tags=["Machine Learning"])
def predict_upselling(payload: PredictUpsellingRequest) -> dict:
    evidencia = {
        "Tipo_Habitacion": payload.Tipo_Habitacion,
        "Piso_Habitacion": payload.Piso_Habitacion,
        "Procedencia_Huesped": payload.Procedencia_Huesped,
        "Dias_Estadia": payload.Dias_Estadia,
    }
    return predecir_servicio(evidencia)
