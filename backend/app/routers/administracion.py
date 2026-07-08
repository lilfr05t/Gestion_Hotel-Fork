from collections import Counter, defaultdict
from datetime import date, datetime
from typing import List
from logging import getLogger

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app import models
from app.models.bayesian_model import predecir_servicio
from app.schemas.administracion import (
    UsuarioResponse,
    BoletaResumenResponse,
    ConfiguracionResponse,
    ConfiguracionBase,
    AdminAnalyticsResponse,
)
from app.crud.facturacion import generar_boleta_final

logger = getLogger(__name__)

router = APIRouter(prefix="", tags=["Administración"])


@router.get("/usuarios", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    usuarios = db.query(models.Usuario).all()
    return usuarios


@router.get("/boletas", response_model=List[BoletaResumenResponse])
def listar_boletas(db: Session = Depends(get_db)):
    try:
        # Usar joinedload para cargar relaciones de manera eficiente (evita N+1 queries)
        boletas = db.query(models.Boleta).options(
            joinedload(models.Boleta.reserva).joinedload(models.Reserva.habitacion)
        ).all()
        resultado = []

        for boleta in boletas:
            numero_habitacion = "N/A"
            
            # Validar que la boleta tiene reserva
            if boleta.reserva:
                try:
                    # Intentar obtener el número de habitación desde la relación cargada
                    if boleta.reserva.habitacion:
                        numero_habitacion = boleta.reserva.habitacion.numero
                    elif boleta.reserva.ID_Habitacion:
                        numero_habitacion = boleta.reserva.ID_Habitacion
                except Exception as e:
                    logger.warning(f"Error accediendo a habitación de boleta {boleta.ID_Boleta}: {str(e)}")
                    numero_habitacion = "N/A"

            resultado.append({
                "ID_Boleta": boleta.ID_Boleta,
                "numero_habitacion": numero_habitacion,
                "monto": float(boleta.total),
                "fecha": boleta.fecha,
                "estado": boleta.estado
            })

        return resultado
    
    except Exception as e:
        logger.error(f"Error en listar_boletas: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al recuperar boletas de la base de datos"
        )


def _infer_procedencia_desde_email(correo: str | None) -> str:
    if not correo:
        return "Local"
    correo = correo.strip().lower()
    if correo.endswith(".pe"):
        return "Nacional"
    if correo.endswith(tuple(
        [
            ".us",
            ".uk",
            ".es",
            ".cl",
            ".ar",
            ".co",
            ".mx",
            ".fr",
            ".it",
            ".de",
            ".ca",
            ".br",
            ".au",
            ".jp",
        ]
    )):
        return "Extranjero"
    return "Local"


def _calcular_dias_estadia(reserva: models.Reserva) -> int:
    if not reserva.fecha_entrada or not reserva.fecha_salida:
        return 1
    inicio = reserva.fecha_entrada
    fin = reserva.fecha_salida
    if isinstance(inicio, datetime):
        inicio = inicio.date()
    if isinstance(fin, datetime):
        fin = fin.date()
    dias = (fin - inicio).days
    return max(1, dias)


def _infer_piso_desde_numero(numero) -> str:
    if numero is None:
        return "1"
    try:
        raw = str(numero).strip()
        if raw.isdigit() and len(raw) >= 2:
            return raw[0]
        if raw.isdigit():
            return raw
        import re
        match = re.search(r"(\d+)", raw)
        if match:
            value = match.group(1)
            return value[0] if len(value) >= 2 else value
    except Exception:
        pass
    return "1"


def _contar_consumos_por_reserva(db: Session, reserva_ids: list[int]) -> dict[int, int]:
    return {
        reserva_id: cantidad
        for reserva_id, cantidad in db.query(models.Consumo.ID_Reserva, func.count(models.Consumo.ID_Consumo))
        .filter(models.Consumo.ID_Reserva.in_(reserva_ids))
        .group_by(models.Consumo.ID_Reserva)
        .all()
    }


def _contar_tickets_pendientes_por_reserva(db: Session, reserva_ids: list[int]) -> dict[int, int]:
    return {
        reserva_id: cantidad
        for reserva_id, cantidad in db.query(models.Nota_Servicio.ID_Reserva, func.count(models.Nota_Servicio.ID_Nota))
        .filter(models.Nota_Servicio.ID_Reserva.in_(reserva_ids), models.Nota_Servicio.estado == "pendiente")
        .group_by(models.Nota_Servicio.ID_Reserva)
        .all()
    }


def _reservas_previas_por_huesped(db: Session, dnis: list[str], actuales_por_dni: dict[str, int]) -> dict[str, int]:
    resultado = {}
    for dni, total in db.query(models.Reserva.DNI, func.count(models.Reserva.ID_Reserva)).filter(models.Reserva.DNI.in_(dnis)).group_by(models.Reserva.DNI).all():
        actuales = actuales_por_dni.get(dni, 0)
        resultado[dni] = max(0, int(total) - int(actuales))
    return resultado


def _contar_amenidades_por_habitacion(db: Session, habitacion_ids: list[int]) -> dict[int, int]:
    return {
        habitacion_id: cantidad
        for habitacion_id, cantidad in db.query(models.Habitacion_Amenidad.ID_Habitacion, func.count(models.Habitacion_Amenidad.ID_Amenidad))
        .filter(models.Habitacion_Amenidad.ID_Habitacion.in_(habitacion_ids))
        .group_by(models.Habitacion_Amenidad.ID_Habitacion)
        .all()
    }


def _generar_recomendaciones(predicciones: dict, riesgos: dict) -> list[str]:
    candidatos = [
        ("Promocionar paquetes de Spa", predicciones.get("spa", 0.0)),
        ("Impulsar room service y alimentación", predicciones.get("alimentacion", 0.0)),
        ("Ofrecer promociones de lavandería", predicciones.get("lavanderia", 0.0)),
        ("Fortalecer atención de limpieza", riesgos.get("sobrecarga_limpieza", 0.0)),
        ("Monitorear disponibilidad de estacionamiento", riesgos.get("baja_ocupacion", 0.0)),
    ]
    return [texto for texto, _ in sorted(candidatos, key=lambda item: item[1], reverse=True)[:3]]


def _explicacion_analitica() -> str:
    return (
        "Las recomendaciones fueron generadas a partir de la inferencia de la red bayesiana "
        "utilizando la información de habitación, reserva y huésped disponible actualmente."
    )


@router.get("/analitica", response_model=AdminAnalyticsResponse)
def obtener_panel_analitica(db: Session = Depends(get_db)):
    # Build active reservations as union of:
    #  - reservas whose estado == 'activa'
    #  - reservas whose linked habitacion.estado == 'ocupada'
    # Use two queries and merge to avoid subtle join/filter issues.
    reservas_by_state = (
        db.query(models.Reserva)
        .options(joinedload(models.Reserva.habitacion), joinedload(models.Reserva.huesped))
        .filter(models.Reserva.estado == 'activa')
        .all()
    )

    reservas_by_room_subquery = (
        db.query(
            models.Reserva.ID_Habitacion.label('ID_Habitacion'),
            func.max(models.Reserva.ID_Reserva).label('ultima_reserva')
        )
        .group_by(models.Reserva.ID_Habitacion)
        .subquery()
    )

    reservas_by_room = (
        db.query(models.Reserva)
        .join(models.Habitacion, models.Reserva.ID_Habitacion == models.Habitacion.ID_Habitacion)
        .join(
            reservas_by_room_subquery,
            (models.Reserva.ID_Habitacion == reservas_by_room_subquery.c.ID_Habitacion)
            & (models.Reserva.ID_Reserva == reservas_by_room_subquery.c.ultima_reserva)
        )
        .options(joinedload(models.Reserva.habitacion), joinedload(models.Reserva.huesped))
        .filter(models.Habitacion.estado == 'ocupada')
        .all()
    )

    # Merge preserving order and uniqueness by ID_Reserva
    seen = set()
    reservas_activas = []
    for r in reservas_by_state + reservas_by_room:
        if r.ID_Reserva not in seen:
            reservas_activas.append(r)
            seen.add(r.ID_Reserva)

    reservas_confirmadas_count = db.query(models.Reserva).filter(models.Reserva.estado == 'confirmada').count()
    reservas_pendientes_count = db.query(models.Reserva).filter(models.Reserva.estado == 'pendiente').count()

    total_habitaciones = db.query(models.Habitacion).count()
    habitaciones_disponibles = db.query(models.Habitacion).filter(models.Habitacion.estado == "disponible").count()
    habitaciones_ocupadas = db.query(models.Habitacion).filter(models.Habitacion.estado == "ocupada").count()
    habitaciones_mantenimiento = db.query(models.Habitacion).filter(models.Habitacion.estado == "mantenimiento").count()

    boletas_por_estado = {
        estado: cantidad
        for estado, cantidad in db.query(models.Boleta.estado, func.count(models.Boleta.ID_Boleta)).group_by(models.Boleta.estado).all()
    }
    boletas_generadas = sum(boletas_por_estado.values())

    parking_ocupado = db.query(models.Parking).filter(models.Parking.estado == "ocupado").count()
    parking_disponible = db.query(models.Parking).filter(models.Parking.estado == "disponible").count()
    tickets_pendientes = db.query(models.Nota_Servicio).filter(models.Nota_Servicio.estado == "pendiente").count()

    reserva_ids = [reserva.ID_Reserva for reserva in reservas_activas]
    dnis_activos = [reserva.DNI for reserva in reservas_activas]
    actuales_por_dni = Counter(dnis_activos)

    consumos_por_reserva = _contar_consumos_por_reserva(db, reserva_ids)
    tickets_por_reserva = _contar_tickets_pendientes_por_reserva(db, reserva_ids)
    reservas_previas = _reservas_previas_por_huesped(db, dnis_activos, actuales_por_dni)
    amenidades_por_habitacion = _contar_amenidades_por_habitacion(db, [reserva.ID_Habitacion for reserva in reservas_activas if reserva.ID_Habitacion])
    parking_ids = {
        reserva_id
        for reserva_id, in db.query(models.Asignacion_Parking.ID_Reserva).filter(models.Asignacion_Parking.ID_Reserva.in_(reserva_ids)).all()
    }

    servicios_agrupados = defaultdict(float)
    riesgos_agrupados = defaultdict(float)
    suma_indice = 0.0
    cantidad_evaluaciones = 0
    reservas_recomendadas = []

    for reserva in reservas_activas:
        habitacion = reserva.habitacion
        huesped = reserva.huesped
        if not habitacion:
            continue

        evidencia = {
            "Tipo_Habitacion": str(habitacion.tipo).title() if habitacion.tipo else "Simple",
            "Piso_Habitacion": _infer_piso_desde_numero(habitacion.numero),
            "Procedencia_Huesped": _infer_procedencia_desde_email(huesped.correo if huesped else None),
            "Dias_Estadia": _calcular_dias_estadia(reserva),
            "Estado_Habitacion": habitacion.estado,
            "Precio_Rango": float(habitacion.precio_noche or 0.0),
            "Amenidades_Habitacion": amenidades_por_habitacion.get(habitacion.ID_Habitacion, 0),
            "Estado_Reserva": reserva.estado,
            "Tiene_Parking": "si" if reserva.ID_Reserva in parking_ids else "no",
            "Reservas_Previas": reservas_previas.get(reserva.DNI, 0),
            "Consumos_Count": consumos_por_reserva.get(reserva.ID_Reserva, 0),
            "Tickets_Pendientes": tickets_por_reserva.get(reserva.ID_Reserva, 0),
        }

        resultado_bayes = predecir_servicio(evidencia)
        probabilidades = resultado_bayes.get("probabilidades", {})
        predicciones = resultado_bayes.get("predicciones", {})
        riesgos = resultado_bayes.get("riesgos", {})
        indice_inteligente = resultado_bayes.get("indice_inteligente", 0)

        if not predicciones:
            continue

        cantidad_evaluaciones += 1
        suma_indice += indice_inteligente
        for servicio, valor in predicciones.items():
            servicios_agrupados[servicio] += float(valor)
        for nombre, valor in riesgos.items():
            riesgos_agrupados[nombre] += float(valor)

        reservas_recomendadas.append({
            "ID_Reserva": reserva.ID_Reserva,
            "numero_habitacion": habitacion.numero,
            "tipo_habitacion": evidencia["Tipo_Habitacion"],
            "piso": evidencia["Piso_Habitacion"],
            "procedencia": evidencia["Procedencia_Huesped"],
            "dias_estadia": evidencia["Dias_Estadia"],
            "servicio_recomendado": max(predicciones, key=predicciones.get),
            "probabilidades": probabilidades,
            "predicciones": predicciones,
            "riesgos": riesgos,
            "indice_inteligente": indice_inteligente,
        })

    if cantidad_evaluaciones > 0:
        predicciones_agrupadas = {
            servicio: round(valor / cantidad_evaluaciones, 4)
            for servicio, valor in servicios_agrupados.items()
        }
        riesgos_agrupados = {
            nombre: round(valor / cantidad_evaluaciones, 4)
            for nombre, valor in riesgos_agrupados.items()
        }
        indice_inteligente = round(suma_indice / cantidad_evaluaciones)
    else:
        predicciones_agrupadas = {"spa": 0.0, "alimentacion": 0.0, "lavanderia": 0.0, "ninguno": 0.0}
        riesgos_agrupados = {"baja_ocupacion": 0.0, "sobrecarga_limpieza": 0.0}
        indice_inteligente = 0

    recomendaciones = _generar_recomendaciones(predicciones_agrupadas, riesgos_agrupados)
    explicacion = _explicacion_analitica()
    reservas_recomendadas = sorted(
        reservas_recomendadas,
        key=lambda item: max(item["probabilidades"].values()) if item["probabilidades"] else 0,
        reverse=True,
    )[:5]

    reservas_finalizadas_count = db.query(models.Reserva).filter(models.Reserva.estado == "finalizada").count()

    return AdminAnalyticsResponse(
        total_habitaciones=total_habitaciones,
        habitaciones_disponibles=habitaciones_disponibles,
        habitaciones_ocupadas=habitaciones_ocupadas,
        habitaciones_mantenimiento=habitaciones_mantenimiento,
        reservas_activas=len(reservas_activas),
        reservas_confirmadas=reservas_confirmadas_count,
        reservas_pendientes=reservas_pendientes_count,
        reservas_finalizadas=reservas_finalizadas_count,
        ocupacion_actual=round((habitaciones_ocupadas / total_habitaciones) * 100, 1) if total_habitaciones else 0.0,
        boletas_generadas=boletas_generadas,
        boletas_por_estado=boletas_por_estado,
        parking_ocupado=parking_ocupado,
        parking_disponible=parking_disponible,
        tickets_pendientes=tickets_pendientes,
        servicios_probables=[
            {
                "servicio": servicio,
                "probabilidad": round(valor, 4),
                "porcentaje": int(round(valor * 100)),
            }
            for servicio, valor in sorted(predicciones_agrupadas.items(), key=lambda item: item[1], reverse=True)
        ],
        reservas_recomendadas=reservas_recomendadas,
        recomendaciones=recomendaciones,
        predicciones=predicciones_agrupadas,
        riesgos=riesgos_agrupados,
        indice_inteligente=indice_inteligente,
        explicacion=explicacion,
    )


@router.get("/configuracion", response_model=ConfiguracionResponse)
def obtener_configuracion(db: Session = Depends(get_db)):
    configuracion = db.query(models.Configuracion).order_by(models.Configuracion.ID_Configuracion).first()
    if not configuracion:
        configuracion = models.Configuracion(
            nombre_hotel="Hotel PMS",
            hora_checkin="15:00",
            hora_checkout="12:00"
        )
        db.add(configuracion)
        db.commit()
        db.refresh(configuracion)
    return configuracion


@router.put("/configuracion", response_model=ConfiguracionResponse)
def actualizar_configuracion(
    payload: ConfiguracionBase,
    db: Session = Depends(get_db)
):
    configuracion = db.query(models.Configuracion).order_by(models.Configuracion.ID_Configuracion).first()

    if not configuracion:
        configuracion = models.Configuracion(
            nombre_hotel=payload.nombre_hotel,
            hora_checkin=payload.hora_checkin,
            hora_checkout=payload.hora_checkout,
        )
        db.add(configuracion)
    else:
        configuracion.nombre_hotel = payload.nombre_hotel
        configuracion.hora_checkin = payload.hora_checkin
        configuracion.hora_checkout = payload.hora_checkout

    db.commit()
    db.refresh(configuracion)
    return configuracion
