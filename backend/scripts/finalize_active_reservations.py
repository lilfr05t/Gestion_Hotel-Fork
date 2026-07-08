from datetime import datetime
import os
import sys

# Add backend/ (project root) to sys.path so `from app...` imports succeed
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

from app.core.database import SessionLocal
from app.models import Reserva

"""
Script to mark all reservations with estado='activa' as 'finalizada'.
Run with the backend virtualenv (from the `backend` folder):
    .venv\Scripts\python.exe scripts\finalize_active_reservations.py

Or set `PYTHONPATH` to the backend folder before running.
"""

if __name__ == '__main__':
    db = SessionLocal()
    try:
        count_before = db.query(Reserva).filter(Reserva.estado == 'activa').count()
        print(f"Active reservations found: {count_before}")
        if count_before == 0:
            print('No active reservations to update.')
        else:
            # Update in batches to avoid long transactions
            batch_size = 500
            updated = 0
            while True:
                rows = db.query(Reserva).filter(Reserva.estado == 'activa').limit(batch_size).all()
                if not rows:
                    break
                for r in rows:
                    r.estado = 'finalizada'
                    # optionally ensure fecha_salida is not before fecha_entrada; keep existing dates
                    updated += 1
                db.commit()
            print(f'Updated {updated} reservations to finalizada')
    except Exception as e:
        print('Error during update:', e)
        db.rollback()
    finally:
        db.close()
