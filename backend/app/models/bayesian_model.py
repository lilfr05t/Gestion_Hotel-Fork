import pickle
import random
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict

import pandas as pd
from pgmpy.inference import VariableElimination
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.parameter_estimator import DiscreteMLE
from sqlalchemy import func

from app.core.database import SessionLocal
from app.models_legacy import (
    Amenidad,
    Asignacion_Parking,
    Consumo,
    Habitacion,
    Habitacion_Amenidad,
    Huesped,
    Nota_Servicio,
    Reserva,
    Servicio,
)

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / 'trained_bayesian_model.pkl'


SERVICIOS = ["Alimentacion", "Lavanderia", "Spa", "Ninguno"]
TIPOS_HABITACION = ["Simple", "Doble", "Suite", "Junior"]
PISOS_HABITACION = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]
PROCEDENCIAS_HUESPED = ["Nacional", "Extranjero", "Local"]
ESTADOS_HABITACION = ["disponible", "ocupada", "mantenimiento"]
RANGOS_PRECIO = ["economico", "medio", "alto", "premium"]
AMENIDADES_CATEGORIAS = ["baja", "media", "alta"]
ESTADOS_RESERVA = ["pendiente", "confirmada", "activa", "finalizada", "cancelada"]
SI_NO = ["no", "si"]
RESERVAS_PREVIAS = ["0", "1-2", "3+"]
TIEMPO_CONSUMO = ["0", "1-2", "3+"]
TICKETS_PENDIENTES = ["ninguno", "bajo", "alto"]
RIESGO_NIVELES = ["bajo", "alto"]


def _categoria_dias(dias: int) -> str:
    if dias <= 2:
        return "1-2"
    if dias <= 5:
        return "3-5"
    return "6+"


def _categoria_precio(precio: float) -> str:
    if precio < 120:
        return "economico"
    if precio < 220:
        return "medio"
    if precio < 350:
        return "alto"
    return "premium"


def _categoria_amenidades(cantidad: int) -> str:
    if cantidad <= 1:
        return "baja"
    if cantidad <= 3:
        return "media"
    return "alta"


def _categoria_reservas_previas(cantidad: int) -> str:
    if cantidad == 0:
        return "0"
    if cantidad <= 2:
        return "1-2"
    return "3+"


def _categoria_consumos(cantidad: int) -> str:
    if cantidad == 0:
        return "0"
    if cantidad <= 2:
        return "1-2"
    return "3+"


def _categoria_tickets(cantidad: int) -> str:
    if cantidad == 0:
        return "ninguno"
    if cantidad <= 2:
        return "bajo"
    return "alto"


def _infer_procedencia_desde_email(correo: str | None) -> str:
    if not correo:
        return "Local"
    correo = correo.strip().lower()
    if correo.endswith('.pe'):
        return "Nacional"
    if correo.endswith(tuple([
        '.us', '.uk', '.es', '.cl', '.ar', '.co', '.mx', '.fr', '.it', '.de', '.ca', '.br', '.au', '.jp',
    ])):
        return "Extranjero"
    return "Local"


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


def _calcular_dias_estadia(fecha_entrada, fecha_salida) -> int:
    if fecha_entrada is None or fecha_salida is None:
        return 1
    if isinstance(fecha_entrada, datetime):
        inicio = fecha_entrada.date()
    else:
        inicio = fecha_entrada
    if isinstance(fecha_salida, datetime):
        fin = fecha_salida.date()
    else:
        fin = fecha_salida
    dias = (fin - inicio).days
    return max(1, dias)


def _tipo_servicio_desde_consumos(consumos: list[Consumo]) -> str:
    totales = Counter()
    for consumo in consumos:
        servicio = consumo.servicio
        if servicio is None:
            continue
        nombre = (servicio.nombre or '').lower()
        tipo = (servicio.tipo or '').lower()
        monto = float(consumo.precio_unitario or 0.0) * (int(consumo.cantidad or 1))
        if 'spa' in nombre or tipo == 'bienestar':
            totales['Spa'] += monto
        elif 'lavander' in nombre or tipo == 'limpieza':
            totales['Lavanderia'] += monto
        elif tipo == 'alimentación' or 'desayuno' in nombre or 'almuerzo' in nombre or 'cena' in nombre or 'minibar' in nombre or 'room' in nombre or 'servicio' in nombre:
            totales['Alimentacion'] += monto
        elif tipo == 'transporte' or tipo == 'recepción':
            totales['Ninguno'] += monto
        else:
            totales['Ninguno'] += monto
    if not totales:
        return 'Ninguno'
    return totales.most_common(1)[0][0]


def build_training_dataframe_from_db() -> pd.DataFrame:
    with SessionLocal() as db:
        reservas = db.query(Reserva).all()

        amenidades = {
            row[0]: int(row[1])
            for row in db.query(Habitacion_Amenidad.ID_Habitacion, func.count(Habitacion_Amenidad.ID_Amenidad))
            .group_by(Habitacion_Amenidad.ID_Habitacion)
            .all()
        }

        asignaciones = {row[0] for row in db.query(Asignacion_Parking.ID_Reserva).all()}
        consumos_por_reserva = {
            row[0]: int(row[1])
            for row in db.query(Consumo.ID_Reserva, func.count(Consumo.ID_Consumo))
            .group_by(Consumo.ID_Reserva)
            .all()
        }
        tickets_por_reserva = {
            row[0]: int(row[1])
            for row in db.query(Nota_Servicio.ID_Reserva, func.count(Nota_Servicio.ID_Nota))
            .filter(Nota_Servicio.estado == 'pendiente')
            .group_by(Nota_Servicio.ID_Reserva)
            .all()
        }

        reservas_por_huesped = {}
        for reserva in sorted(reservas, key=lambda r: (r.DNI or '', r.fecha_entrada or datetime.min)):
            reservas_por_huesped.setdefault(reserva.DNI, []).append(reserva)

        filas = []
        for dni, lista in reservas_por_huesped.items():
            for idx, reserva in enumerate(lista):
                habitacion = reserva.habitacion
                huesped = reserva.huesped
                if habitacion is None or huesped is None:
                    continue

                dias = _calcular_dias_estadia(reserva.fecha_entrada, reserva.fecha_salida)
                consumos = db.query(Consumo).filter(Consumo.ID_Reserva == reserva.ID_Reserva).all()
                tipo_servicio = _tipo_servicio_desde_consumos(consumos)
                consumos_count = consumos_por_reserva.get(reserva.ID_Reserva, 0)
                tickets = tickets_por_reserva.get(reserva.ID_Reserva, 0)
                reserva_previas = idx

                filas.append({
                    'Tipo_Habitacion': str(habitacion.tipo).title() if habitacion.tipo else 'Simple',
                    'Piso_Habitacion': _infer_piso_desde_numero(habitacion.numero),
                    'Procedencia_Huesped': _infer_procedencia_desde_email(huesped.correo),
                    'Dias_Estadia': _categoria_dias(dias),
                    'Estado_Habitacion': habitacion.estado,
                    'Precio_Rango': _categoria_precio(float(habitacion.precio_noche or 0.0)),
                    'Amenidades_Habitacion': _categoria_amenidades(amenidades.get(habitacion.ID_Habitacion, 0)),
                    'Estado_Reserva': reserva.estado,
                    'Tiene_Parking': 'si' if reserva.ID_Reserva in asignaciones else 'no',
                    'Reservas_Previas': _categoria_reservas_previas(reserva_previas),
                    'Consumos_Count': _categoria_consumos(consumos_count),
                    'Tickets_Pendientes': _categoria_tickets(tickets),
                    'Tipo_Servicio': tipo_servicio,
                    'Baja_Ocupacion': 'alto' if reserva.estado == 'pendiente' and tipo_servicio == 'Ninguno' else 'bajo',
                    'Sobrecarga_Limpieza': 'alto' if consumos_count >= 3 or tickets >= 2 else 'bajo',
                })

        return pd.DataFrame(filas)


def save_trained_model(model: DiscreteBayesianNetwork, path: str | Path | None = None) -> Path:
    path_obj = Path(path or DEFAULT_MODEL_PATH)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    with path_obj.open('wb') as f:
        pickle.dump(model, f)
    return path_obj


def load_trained_model(path: str | Path | None = None) -> DiscreteBayesianNetwork:
    path_obj = Path(path or DEFAULT_MODEL_PATH)
    if not path_obj.exists():
        raise FileNotFoundError(f'El modelo bayesiano serializado no existe en {path_obj}')
    with path_obj.open('rb') as f:
        return pickle.load(f)


def check_cpds_normalized(model: DiscreteBayesianNetwork) -> bool:
    from numpy import allclose

    for cpd in model.get_cpds():
        values = cpd.values
        totals = values.sum(axis=0)
        if not allclose(totals, 1.0, atol=1e-6):
            return False
    return True


def train_model_from_dataframe(df: pd.DataFrame) -> DiscreteBayesianNetwork:
    modelo = DiscreteBayesianNetwork(
        [
            ('Tipo_Habitacion', 'Tipo_Servicio'),
            ('Piso_Habitacion', 'Tipo_Servicio'),
            ('Procedencia_Huesped', 'Tipo_Servicio'),
            ('Dias_Estadia', 'Tipo_Servicio'),
            ('Estado_Habitacion', 'Tipo_Servicio'),
            ('Precio_Rango', 'Tipo_Servicio'),
            ('Amenidades_Habitacion', 'Tipo_Servicio'),
            ('Estado_Reserva', 'Tipo_Servicio'),
            ('Tiene_Parking', 'Tipo_Servicio'),
            ('Reservas_Previas', 'Tipo_Servicio'),
            ('Consumos_Count', 'Tipo_Servicio'),
            ('Tickets_Pendientes', 'Tipo_Servicio'),
            ('Tipo_Servicio', 'Baja_Ocupacion'),
            ('Estado_Reserva', 'Baja_Ocupacion'),
            ('Tipo_Servicio', 'Sobrecarga_Limpieza'),
            ('Tickets_Pendientes', 'Sobrecarga_Limpieza'),
        ]
    )
    modelo.fit(df, estimator=DiscreteMLE())
    return modelo


def _generar_datos_sinteticos(numero_filas: int = 5000) -> pd.DataFrame:
    registros = []
    for _ in range(numero_filas):
        tipo_habitacion = random.choice(TIPOS_HABITACION)
        piso_habitacion = random.choice(PISOS_HABITACION)
        procedencia_huesped = random.choice(PROCEDENCIAS_HUESPED)
        dias_estadia = random.randint(1, 10)
        estado_habitacion = random.choices(ESTADOS_HABITACION, weights=[0.55, 0.35, 0.1])[0]
        precio_rango = random.choices(RANGOS_PRECIO, weights=[0.25, 0.4, 0.25, 0.1])[0]
        amenidades_habitacion = random.choices(AMENIDADES_CATEGORIAS, weights=[0.4, 0.4, 0.2])[0]
        estado_reserva = random.choices(["pendiente", "confirmada", "activa"], weights=[0.2, 0.5, 0.3])[0]
        tiene_parking = random.choice(SI_NO)
        reservas_previas = random.choice(RESERVAS_PREVIAS)
        consumos_count = random.choice(TIEMPO_CONSUMO)
        tickets_pendientes = random.choice(TICKETS_PENDIENTES)

        dias_categoria = _categoria_dias(dias_estadia)
        tipo_servicio = random.choice(SERVICIOS)

        if tipo_habitacion == "Suite" or precio_rango in ["alto", "premium"]:
            tipo_servicio = random.choices(["Spa", "Alimentacion", "Lavanderia", "Ninguno"], weights=[0.35, 0.3, 0.2, 0.15])[0]
        elif procedencia_huesped == "Extranjero" and dias_estadia >= 3:
            tipo_servicio = random.choices(["Alimentacion", "Spa", "Lavanderia", "Ninguno"], weights=[0.4, 0.25, 0.2, 0.15])[0]
        elif estado_habitacion == "mantenimiento":
            tipo_servicio = random.choices(["Lavanderia", "Ninguno", "Alimentacion", "Spa"], weights=[0.4, 0.3, 0.2, 0.1])[0]
        elif tipo_habitacion == "Junior" and dias_estadia <= 2:
            tipo_servicio = random.choices(["Ninguno", "Alimentacion", "Lavanderia", "Spa"], weights=[0.5, 0.2, 0.2, 0.1])[0]
        elif consumos_count == "3+" or tickets_pendientes == "alto":
            tipo_servicio = random.choices(["Lavanderia", "Spa", "Alimentacion", "Ninguno"], weights=[0.35, 0.35, 0.2, 0.1])[0]

        baja_ocupacion = "alto" if estado_reserva == "pendiente" and tipo_servicio == "Ninguno" else "bajo"
        sobrecarga_limpieza = "alto" if consumos_count == "3+" or tickets_pendientes == "alto" else "bajo"

        registros.append(
            {
                "Tipo_Habitacion": tipo_habitacion,
                "Piso_Habitacion": piso_habitacion,
                "Procedencia_Huesped": procedencia_huesped,
                "Dias_Estadia": dias_categoria,
                "Estado_Habitacion": estado_habitacion,
                "Precio_Rango": precio_rango,
                "Amenidades_Habitacion": amenidades_habitacion,
                "Estado_Reserva": estado_reserva,
                "Tiene_Parking": tiene_parking,
                "Reservas_Previas": reservas_previas,
                "Consumos_Count": consumos_count,
                "Tickets_Pendientes": tickets_pendientes,
                "Tipo_Servicio": tipo_servicio,
                "Baja_Ocupacion": baja_ocupacion,
                "Sobrecarga_Limpieza": sobrecarga_limpieza,
            }
        )

    return pd.DataFrame(registros)


def _crear_red_bayesiana() -> DiscreteBayesianNetwork:
    modelo = DiscreteBayesianNetwork(
        [
            ("Tipo_Habitacion", "Tipo_Servicio"),
            ("Piso_Habitacion", "Tipo_Servicio"),
            ("Procedencia_Huesped", "Tipo_Servicio"),
            ("Dias_Estadia", "Tipo_Servicio"),
            ("Estado_Habitacion", "Tipo_Servicio"),
            ("Precio_Rango", "Tipo_Servicio"),
            ("Amenidades_Habitacion", "Tipo_Servicio"),
            ("Estado_Reserva", "Tipo_Servicio"),
            ("Tiene_Parking", "Tipo_Servicio"),
            ("Reservas_Previas", "Tipo_Servicio"),
            ("Consumos_Count", "Tipo_Servicio"),
            ("Tickets_Pendientes", "Tipo_Servicio"),
            ("Tipo_Servicio", "Baja_Ocupacion"),
            ("Estado_Reserva", "Baja_Ocupacion"),
            ("Tipo_Servicio", "Sobrecarga_Limpieza"),
            ("Tickets_Pendientes", "Sobrecarga_Limpieza"),
        ]
    )
    datos = _generar_datos_sinteticos(5000)
    modelo.fit(datos, estimator=DiscreteMLE())
    return modelo


_MODELO = None


def _obtener_modelo() -> DiscreteBayesianNetwork:
    global _MODELO
    if _MODELO is None:
        _MODELO = load_trained_model()
    return _MODELO


def _procesar_valor(clave: str, valor) -> str:
    if clave == "Dias_Estadia":
        try:
            dias = int(valor)
        except (TypeError, ValueError):
            dias = 1
        return _categoria_dias(dias)
    if clave == "Precio_Rango":
        try:
            valor = float(valor)
        except (TypeError, ValueError):
            valor = 0.0
        return _categoria_precio(valor)
    if clave == "Amenidades_Habitacion":
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            valor = 0
        return _categoria_amenidades(valor)
    if clave == "Reservas_Previas":
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            valor = 0
        return _categoria_reservas_previas(valor)
    if clave == "Consumos_Count":
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            valor = 0
        return _categoria_consumos(valor)
    if clave == "Tickets_Pendientes":
        try:
            valor = int(valor)
        except (TypeError, ValueError):
            valor = 0
        return _categoria_tickets(valor)
    return str(valor)


def _query_variable(inferencia: VariableElimination, modelo: DiscreteBayesianNetwork, variable: str, evidence: dict) -> Dict[str, float]:
    try:
        resultado = inferencia.query(variables=[variable], evidence=evidence)
    except KeyError:
        valid_evidence = {
            clave: valor
            for clave, valor in evidence.items()
            if clave in modelo.states and valor in modelo.states[clave]
        }
        resultado = inferencia.query(variables=[variable], evidence=valid_evidence)

    states = list(modelo.states[variable])
    values = resultado.values
    return {state: float(values[idx]) for idx, state in enumerate(states)}


SERVICE_RECOMENDATIONS = {
    "Alimentacion": "Promocionar paquetes de alimentación y room service.",
    "Lavanderia": "Ofrecer promociones de lavandería para estadías largas.",
    "Spa": "Promocionar experiencias de Spa para clientes con mayor potencial.",
    "Ninguno": "Monitorear la demanda antes de lanzar ofertas adicionales.",
}
RISK_RECOMMENDATIONS = {
    "baja_ocupacion": "Preparar promociones comerciales para evitar baja ocupación.",
    "sobrecarga_limpieza": "Refuerzo operativo en limpieza por alta demanda esperada.",
}


def _generar_recomendaciones_bayes(predicciones: dict, riesgos: dict) -> list[str]:
    recomendaciones = []
    recomendaciones.extend(
        SERVICE_RECOMENDATIONS.get(servicio.title(), "")
        for servicio, _ in sorted(predicciones.items(), key=lambda item: item[1], reverse=True)[:2]
    )
    recomendaciones.extend(
        RISK_RECOMMENDATIONS.get(riesgo, "")
        for riesgo, _ in sorted(riesgos.items(), key=lambda item: item[1], reverse=True)[:1]
    )
    return [texto for texto in recomendaciones if texto]


def predecir_servicio(evidencia: dict) -> dict:
    modelo = _obtener_modelo()
    evidencia_procesada = {
        clave: _procesar_valor(clave, valor)
        for clave, valor in evidencia.items()
        if valor is not None
    }

    inferencia = VariableElimination(modelo)
    probabilidades = _query_variable(inferencia, modelo, "Tipo_Servicio", evidencia_procesada)
    riesgos_baja = _query_variable(inferencia, modelo, "Baja_Ocupacion", evidencia_procesada)
    riesgos_limpieza = _query_variable(inferencia, modelo, "Sobrecarga_Limpieza", evidencia_procesada)

    predicciones = {servicio.lower(): prob for servicio, prob in probabilidades.items()}
    riesgos = {
        "baja_ocupacion": riesgos_baja.get("alto", riesgos_baja.get("bajo", 0.0)),
        "sobrecarga_limpieza": riesgos_limpieza.get("alto", riesgos_limpieza.get("bajo", 0.0)),
    }
    indice_inteligente = min(
        100,
        max(
            0,
            round(
                (
                    predicciones.get("alimentacion", 0.0) * 0.35
                    + predicciones.get("spa", 0.0) * 0.35
                    + (1.0 - riesgos["baja_ocupacion"]) * 0.15
                    + (1.0 - riesgos["sobrecarga_limpieza"]) * 0.15
                )
                * 100
            )
        ),
    )
    recomendaciones = _generar_recomendaciones_bayes(predicciones, riesgos)
    explicacion = (
        "Las recomendaciones fueron generadas a partir de la inferencia de la red bayesiana "
        "utilizando la información de habitación, reserva y huésped disponible actualmente."
    )

    return {
        "probabilidades": probabilidades,
        "predicciones": predicciones,
        "riesgos": riesgos,
        "indice_inteligente": indice_inteligente,
        "recomendaciones": recomendaciones,
        "explicacion": explicacion,
    }
