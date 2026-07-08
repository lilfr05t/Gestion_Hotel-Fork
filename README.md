# Sistema de Gestión Hotelera (PMS)

Este repositorio contiene un backend en FastAPI y un frontend en Vue 3 + Vite.

## Requisitos

- Windows 10/11
- Python 3.14
- Node.js 25.x (o compatible)
- npm
- MySQL o MariaDB con la base de datos configurada
- Virtualenv (opcional, se usa `.venv` en el root)

## Backend

### 1. Instalar dependencias

Desde la raíz del proyecto:

```powershell
cd C:\Users\Moroni\Downloads\Gestion_Hotel-Bayes_version\Gestion_Hotel-Bayes_version
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

### 2. Configurar variables de entorno

El backend usa `backend/.env` con los datos de conexión a la base de datos.

Ejemplo de valores esperados:

```text
DATABASE_USER=root
DATABASE_PASSWORD=1234
DATABASE_HOST=127.0.0.1
DATABASE_PORT=3306
DATABASE_NAME=hotel_db
DATABASE_URL="mysql+pymysql://root:1234@localhost:3306/hotel_db"
```

Asegúrate de que la base de datos `hotel_db` exista y que el usuario tenga permisos.

### 3. Ejecutar backend

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

Esto levantará el backend en:

- http://127.0.0.1:8001
- http://localhost:8001

## Frontend

### 1. Instalar dependencias

```powershell
cd frontend
npm install
```

### 2. Ejecutar frontend

```powershell
npm run dev
```

El frontend se sirve en:

- http://127.0.0.1:5173
- http://localhost:5173

## Rutas importantes

- Backend API base: `http://127.0.0.1:8001/api/v1`
- Analítica predictiva: `http://127.0.0.1:8001/api/v1/analitica`
- Verificación básica: `http://127.0.0.1:8001/`
- Frontend app: `http://127.0.0.1:5173`

## Notas

- Si el puerto `5173` ya está en uso, Vite propondrá otro puerto.
- Si el backend necesita conectarse a MySQL, verifica que el servicio de base de datos esté activo.
- El frontend ya usa `vite.config.js` para servir en `127.0.0.1:5173`.
