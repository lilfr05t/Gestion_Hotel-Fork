from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioResponse(BaseModel):
    ID_Usuario: int
    nombre: str
    correo: EmailStr
    rol: str
    activo: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class BoletaResumenResponse(BaseModel):
    ID_Boleta: int
    numero_habitacion: Optional[int]
    monto: Decimal
    fecha: date
    estado: str


class ConfiguracionBase(BaseModel):
    nombre_hotel: str = Field(..., max_length=100)
    hora_checkin: str = Field(..., max_length=5)
    hora_checkout: str = Field(..., max_length=5)


class ConfiguracionResponse(ConfiguracionBase):
    ID_Configuracion: int
    model_config = ConfigDict(from_attributes=True)


class ServicioProbable(BaseModel):
    servicio: str
    probabilidad: float
    porcentaje: int


class ReservaRecomendada(BaseModel):
    ID_Reserva: int
    numero_habitacion: Optional[int] = None
    tipo_habitacion: str
    piso: str
    procedencia: str
    dias_estadia: int
    servicio_recomendado: str
    probabilidades: Dict[str, float]


class AdminAnalyticsResponse(BaseModel):
    total_habitaciones: int
    habitaciones_disponibles: int
    habitaciones_ocupadas: int
    habitaciones_mantenimiento: int
    reservas_activas: int
    reservas_confirmadas: int
    reservas_pendientes: int
    reservas_finalizadas: int
    ocupacion_actual: float
    boletas_generadas: int
    boletas_por_estado: Dict[str, int]
    parking_ocupado: int
    parking_disponible: int
    tickets_pendientes: int
    servicios_probables: List[ServicioProbable]
    reservas_recomendadas: List[ReservaRecomendada]
    recomendaciones: List[str]
    predicciones: Dict[str, float]
    riesgos: Dict[str, float]
    indice_inteligente: int
    explicacion: str

    model_config = ConfigDict(from_attributes=True)
