import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.core.database import SessionLocal
from app.models import Reserva

if __name__ == '__main__':
    db = SessionLocal()
    try:
        active = db.query(Reserva).filter(Reserva.estado == 'activa').count()
        finalized = db.query(Reserva).filter(Reserva.estado == 'finalizada').count()
        print(f'ACTIVE {active}')
        print(f'FINALIZED {finalized}')
    finally:
        db.close()
