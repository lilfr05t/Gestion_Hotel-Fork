import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.database import SessionLocal
from app.models import Habitacion

"""
Script to release rooms currently marked as 'ocupada'.
Run from backend folder with the backend virtual environment.
"""

if __name__ == '__main__':
    db = SessionLocal()
    try:
        ocupadas = db.query(Habitacion).filter(Habitacion.estado == 'ocupada').all()
        count = len(ocupadas)
        print(f'Reservas activas actuales: {db.query(Habitacion).filter(Habitacion.estado == "ocupada").count()} habitaciones ocupadas')
        if count == 0:
            print('No hay habitaciones ocupadas para liberar.')
        else:
            for habitacion in ocupadas:
                habitacion.estado = 'disponible'
            db.commit()
            print(f'Liberadas {count} habitaciones ocupadas.')
    except Exception as e:
        print('Error al liberar habitaciones:', e)
        db.rollback()
    finally:
        db.close()
