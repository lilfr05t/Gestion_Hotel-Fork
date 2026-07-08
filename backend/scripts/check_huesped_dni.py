import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.database import SessionLocal
from app.models import Huesped

if __name__ == '__main__':
    db = SessionLocal()
    try:
        dni = '72084436'
        huesped = db.query(Huesped).filter(Huesped.DNI == dni).first()
        if huesped:
            print('FOUND', huesped.DNI, huesped.nombre, huesped.apellido, huesped.correo, huesped.telefono, huesped.estado)
        else:
            print('NOT FOUND', dni)
    finally:
        db.close()
