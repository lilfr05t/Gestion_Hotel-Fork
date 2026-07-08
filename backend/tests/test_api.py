import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


def main() -> None:
    payload = {
        "Tipo_Habitacion": "Suite",
        "Piso_Habitacion": "10",
        "Procedencia_Huesped": "Extranjero",
        "Dias_Estadia": 6,
    }

    with TestClient(app) as client:
        response = client.post("/api/predict-upselling", json=payload)

        print("Status code:", response.status_code)
        print("Payload enviado:", json.dumps(payload, indent=2, ensure_ascii=False))

        assert response.status_code == 200, response.text
        data = response.json()
        assert "probabilidades" in data, data

        probabilidades = data["probabilidades"]
        probabilidades_pct = {
            servicio: round(float(valor) * 100, 2)
            for servicio, valor in probabilidades.items()
        }
        ordenadas = dict(
            sorted(probabilidades_pct.items(), key=lambda item: item[1], reverse=True)
        )

        print("Respuesta ordenada por probabilidad:")
        print(json.dumps(ordenadas, indent=2, ensure_ascii=False))

        total = sum(probabilidades.values())
        assert abs(total - 1.0) < 1e-6, f"Probabilidades no normalizadas: {probabilidades}"

        servicio_top = max(probabilidades, key=probabilidades.get)
        print(f"Servicio con mayor probabilidad: {servicio_top}")


if __name__ == "__main__":
    main()
