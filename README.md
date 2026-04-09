# IOT 2026 MVP

## Stack

- Frontend: plain HTML/CSS/JavaScript in `interface/`
- Backend: Flask API + Socket.IO in `backend/`
- MQTT broker: Mosquitto
- Database: Supabase Postgres

## Quick Start

1. Copy `.env.sample` to `.env`.
2. Update `DATABASE_URL`, `MQTT_HOST`, `MQTT_PORT`, and the MQTT sensor topic settings.
3. Create a virtual environment:
   - `python -m venv .venv`
   - `.venv\\Scripts\\Activate.ps1`
4. Install backend dependencies:
   - `pip install -r backend/requirements.txt`
5. Initialize and seed the backend:
   - `python -m flask --app backend.app init-db`
   - `python -m flask --app backend.app seed-dev`
6. Start the backend:
   - `python -m backend.app`
7. Open the frontend:
   - serve `interface/` with any static server, or open the HTML files directly for simple API testing.

## MQTT Payload Shape

```json
{
  "device_id": "charger-01",
  "bien_so_xe": "59A-12345",
  "current": 120,
  "voltage": 220,
  "power": 26400
}
```
