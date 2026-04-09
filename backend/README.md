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

## 6. Generate a fake 2-hour charging session

This project includes a generator for fake telemetry in the range:

- current: `9-12A`
- voltage: `23-25.5V`
- duration: about `2 hours`

By default it generates a multi-device fleet:

- devices: `esp32s3_01`, `esp32s3_02`, `esp32s3_03`, `esp32s3_04`
- plates: `59A-12345`, `51B-67890`

Write JSONL to a file:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session
```

Generate only one device:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session --single-device --device-code esp32s3_01 --license-plate 59A-12345
```

Publish directly to MQTT:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session --publish --topic ina219/data
```

By default the generator uses a fresh random seed every run.
If you want to reproduce the same fake dataset, pass `--seed` explicitly:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session --seed 20260410
```

The generator injects a few statistical outliers on purpose so you can verify that
`statistical_current_anomaly` alerts are really triggered.

## 7. Load fake payloads directly into the database

If you want the fake data to appear like real historical data in dashboards, history, and alerts,
load it into the database instead of only writing a file or publishing live MQTT:

```powershell
.\.venv\Scripts\python -m backend.scripts.load_fake_payloads_to_db
```

This command will:

- ensure `user1@example.com` / `123456`
- ensure `user2@example.com` / `123456`
- ensure plates `59A-12345` and `51B-67890`
- generate a default 4-device / 2-plate fleet
- preserve generated historical timestamps when inserting into DB
- allow completed charging sessions to appear in user payment history

Use single-device mode when needed:

```powershell
.\.venv\Scripts\python -m backend.scripts.load_fake_payloads_to_db --single-device --device-code esp32s3_01 --license-plate 59A-12345
```

After loading fake data into DB:

- `user1@example.com` can view payment history for `59A-12345`
- `user2@example.com` can view payment history for `51B-67890`
- user dashboard also includes a `Tips / Sponsor` tab that shows the QR image from `interface/assets/image/qr.png`
