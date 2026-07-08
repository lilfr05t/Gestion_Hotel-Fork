import argparse
import json
import pickle
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
from pgmpy.inference import VariableElimination

from app.models.bayesian_model import (
    DEFAULT_MODEL_PATH,
    build_training_dataframe_from_db,
    train_model_from_dataframe,
    save_trained_model,
    _generar_datos_sinteticos,
    _crear_red_bayesiana,
)


def _inferencia_evidencia(model, evidencia):
    inferencia = VariableElimination(model)
    resultado = inferencia.query(variables=['Tipo_Servicio'], evidence=evidencia)
    estados = list(model.states['Tipo_Servicio'])
    return {estado: float(resultado.values[idx]) for idx, estado in enumerate(estados)}


def _promedio_confianza(model, df, sample_size=200):
    muestra = df.sample(min(sample_size, len(df)), random_state=42)
    scores = []
    for _, row in muestra.iterrows():
        evidencia = {
            'Tipo_Habitacion': row['Tipo_Habitacion'],
            'Piso_Habitacion': row['Piso_Habitacion'],
            'Procedencia_Huesped': row['Procedencia_Huesped'],
            'Dias_Estadia': row['Dias_Estadia'],
            'Estado_Habitacion': row['Estado_Habitacion'],
            'Precio_Rango': row['Precio_Rango'],
            'Amenidades_Habitacion': row['Amenidades_Habitacion'],
            'Estado_Reserva': row['Estado_Reserva'],
            'Tiene_Parking': row['Tiene_Parking'],
            'Reservas_Previas': row['Reservas_Previas'],
            'Consumos_Count': row['Consumos_Count'],
            'Tickets_Pendientes': row['Tickets_Pendientes'],
        }
        probabilidades = _inferencia_evidencia(model, evidencia)
        scores.append(max(probabilidades.values()))
    return float(pd.Series(scores).mean()) if scores else 0.0


def _format_distribution(series):
    counts = series.value_counts(normalize=True).round(4)
    return {str(k): float(v) for k, v in counts.items()}


def _build_report(baseline_stats, new_stats, comparison_stats, report_path: Path):
    lines = []
    lines.append('MODELO BAYESIANO - ENTRENAMIENTO')
    lines.append('===================================')
    lines.append('')
    lines.append('Datos usados para entrenamiento:')
    lines.append(f"- Registros de entrenamiento: {new_stats['records']}")
    lines.append('')
    lines.append('Distribuciones principales del nuevo dataset:')
    for nombre, dist in new_stats['distributions'].items():
        lines.append(f"- {nombre}: {dist}")
    lines.append('')
    lines.append('Validación del modelo entrenado:')
    lines.append(f"- Confianza promedio del modelo nuevo: {new_stats['confidence_mean']:.4f}")
    lines.append(f"- Número de variables de evidencia: {len(new_stats['variables'])}")
    lines.append('')
    lines.append('Comparación con modelo de referencia (muestra sintética):')
    lines.append(f"- Registros sintéticos de referencia: {baseline_stats['records']}")
    lines.append(f"- Confianza promedio referencia: {baseline_stats['confidence_mean']:.4f}")
    lines.append(f"- Diferencia de confianza: {new_stats['confidence_mean'] - baseline_stats['confidence_mean']:.4f}")
    lines.append('')
    lines.append('Estructura final del modelo entrenado:')
    lines.extend([f"- {edge[0]} -> {edge[1]}" for edge in new_stats['structure']])
    lines.append('')
    if comparison_stats:
        lines.append('Resumen de comparación de probabilidades:')
        lines.append(json.dumps(comparison_stats, indent=2))
        lines.append('')
    report_text = '\n'.join(lines)
    report_path.write_text(report_text, encoding='utf-8')
    return report_text


def main():
    parser = argparse.ArgumentParser(description='Entrena y serializa la red bayesiana desde la base de datos.')
    parser.add_argument('--model-path', default=None, help='Ruta donde se guardará el modelo entrenado.')
    parser.add_argument('--report-path', default='train_bayesian_model_report.txt', help='Ruta del informe de entrenamiento.')
    parser.add_argument('--compare', action='store_true', help='Entrena y compara con el modelo sintético de referencia.')
    args = parser.parse_args()

    model_path = Path(args.model_path) if args.model_path else None
    report_path = Path(args.report_path)

    print('Construyendo DataFrame de entrenamiento desde la base de datos...')
    df = build_training_dataframe_from_db()
    print(f'- Registros generados: {len(df)}')

    print('Entrenando modelo bayesiano con datos reales...')
    model = train_model_from_dataframe(df)
    save_trained_model(model, model_path)
    print(f'Modelo guardado en: {Path(args.model_path or DEFAULT_MODEL_PATH).resolve()}')

    new_stats = {
        'records': len(df),
        'distributions': {
            'Tipo_Habitacion': _format_distribution(df['Tipo_Habitacion']),
            'Procedencia_Huesped': _format_distribution(df['Procedencia_Huesped']),
            'Dias_Estadia': _format_distribution(df['Dias_Estadia']),
            'Estado_Reserva': _format_distribution(df['Estado_Reserva']),
            'Tiene_Parking': _format_distribution(df['Tiene_Parking']),
        },
        'confidence_mean': _promedio_confianza(model, df),
        'variables': [
            'Tipo_Habitacion',
            'Piso_Habitacion',
            'Procedencia_Huesped',
            'Dias_Estadia',
            'Estado_Habitacion',
            'Precio_Rango',
            'Amenidades_Habitacion',
            'Estado_Reserva',
            'Tiene_Parking',
            'Reservas_Previas',
            'Consumos_Count',
            'Tickets_Pendientes',
        ],
        'structure': model.edges(),
    }

    baseline_stats = None
    comparison_stats = None
    if args.compare:
        print('Entrenando modelo de referencia sintético...')
        base_df = _generar_datos_sinteticos(5000)
        baseline_model = train_model_from_dataframe(base_df)
        baseline_stats = {
            'records': len(base_df),
            'confidence_mean': _promedio_confianza(baseline_model, base_df),
        }
        comparison_stats = {
            'topological_difference': len(set(model.edges()) ^ set(baseline_model.edges())),
        }
    else:
        baseline_stats = {'records': 0, 'confidence_mean': 0.0}

    summary = _build_report(baseline_stats, new_stats, comparison_stats, report_path)
    print(summary)
    print(f'Informe guardado en: {report_path.resolve()}')


if __name__ == '__main__':
    main()
