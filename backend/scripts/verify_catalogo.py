import os
import mysql.connector
from app.models_legacy import Amenidad, Servicio
from app.routers.servicios import _servicio_response

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST', '127.0.0.1'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER', 'root'),
    password=os.getenv('DB_PASSWORD', '1234'),
    database=os.getenv('DB_NAME', 'hotel_db'),
)
cur = conn.cursor()

cur.execute('SHOW COLUMNS FROM amenidad')
print('amenidad_columns', [r[0] for r in cur.fetchall()])
cur.execute('SHOW COLUMNS FROM servicio')
print('servicio_columns', [r[0] for r in cur.fetchall()])
cur.execute("SELECT COUNT(*) FROM amenidad WHERE nombre='Escritorio de trabajo'")
print('escritorio_count', cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM amenidad WHERE categoria IS NULL OR TRIM(COALESCE(descripcion,''))=''")
print('amenidades_vacias', cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM servicio WHERE categoria IS NULL OR TRIM(COALESCE(descripcion,''))=''")
print('servicios_vacios', cur.fetchone()[0])
cur.execute("SELECT ID_Amenidad, nombre, categoria, descripcion FROM amenidad ORDER BY ID_Amenidad LIMIT 6")
print('amenidades_sample', cur.fetchall())
cur.execute("SELECT ID_Servicio, nombre, categoria, descripcion FROM servicio ORDER BY ID_Servicio LIMIT 6")
print('servicios_sample', cur.fetchall())
conn.close()

print('model_amenidad_columns', Amenidad.__table__.columns.keys())
print('model_servicio_columns', Servicio.__table__.columns.keys())

class DummyServicio:
    ID_Servicio = 1
    nombre = 'Spa Sunset'
    tipo = 'Bienestar'
    descripcion = 'Spa premium'
    precio_unitario = 120
    estado = 'activo'
    categoria = 'Bienestar'
    costo_proveedor = 55

print('router_servicio_response', _servicio_response(DummyServicio()))
