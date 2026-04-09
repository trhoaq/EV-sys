# Backend Setup

## 1. Environment

Copy the root `.env.sample` to `.env`. The backend reads broker host, port, database URL, secrets,
and thresholds from that root env file.

## 2. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

## 3. Initialize database and seed demo data

```powershell
.\.venv\Scripts\python -m flask --app backend.app init-db
.\.venv\Scripts\python -m flask --app backend.app seed-dev
```

## 4. Run backend

```powershell
.\.venv\Scripts\python -m backend.app
```

## 5. MQTT payload shape

```json
{
  "device_id": "charger-01",
  "bien_so_xe": "59A-12345",
  "current": 120,
  "voltage": 220,
  "power": 26400
}
```
