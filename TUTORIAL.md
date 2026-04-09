# TUTORIAL

Huong dan nay giup ban chay du an tu dau den cuoi tren may local, khong can hoi them thong tin trong qua trinh setup.

## 1. Muc tieu

Sau khi lam xong tutorial nay, ban se:

- chay duoc backend Flask
- mo duoc frontend thuong va admin
- ket noi duoc DB
- nhan du lieu MQTT test
- thay du lieu realtime / alert tren giao dien

## 2. Dieu kien can co

Ban can cai san:

- Python 3.11+ hoac moi hon
- Mosquitto broker
- Mot database Postgres cua Supabase
- Trinh duyet web

Neu muon phat MQTT test bang terminal, ban can them 1 trong 2 cach:

- `mosquitto_pub` neu da cai Mosquitto CLI
- hoac dung 1 MQTT client khac ma ban quen tay

## 3. Cau truc can biet

- [backend](F:\Code\IOT_2026\backend): Flask API, JWT, MQTT ingest, Socket.IO
- [interface](F:\Code\IOT_2026\interface): frontend HTML/CSS/JS thuan
- [.env.sample](F:\Code\IOT_2026\.env.sample): file mau de dien broker/server/IP/DB
- [README.md](F:\Code\IOT_2026\README.md): quick start ngan
- [backend/README.md](F:\Code\IOT_2026\backend\README.md): ghi chu rieng cho backend

## 4. Tao file env

Tai root repo, copy file mau:

```powershell
Copy-Item .env.sample .env
```

Mo file [\.env.sample](F:\Code\IOT_2026\.env.sample) de tham chieu, roi sua [\.env](F:\Code\IOT_2026\.env) voi gia tri that.

### 4.1 Cac bien bat buoc can sua

```env
SECRET_KEY=replace-with-a-long-random-app-secret
JWT_SECRET_KEY=replace-with-a-long-random-jwt-secret
DATABASE_URL=postgresql+psycopg://postgres:password@db.supabase.example:5432/postgres

MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_SENSOR_TOPIC=ev/charger/telemetry
```

### 4.2 Cac bien thuong giu mac dinh

```env
FLASK_RUN_HOST=127.0.0.1
FLASK_RUN_PORT=5000
CORS_ALLOWED_ORIGINS=*

DEFAULT_MIN_CURRENT_MA=50
DEFAULT_MAX_CURRENT_MA=500
DEVICE_OFFLINE_SECONDS=60
```

## 5. Tao virtual environment va cai thu vien

Chay tai root repo:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

Neu may ban da co san `venv` khac thi van nen giu `.venv` theo dung huong dan de tranh nham.

## 6. Khoi tao database

Backend se dung schema SQLAlchemy va tao bang bang lenh CLI.

Chay:

```powershell
.\.venv\Scripts\python -m flask --app backend.app init-db
.\.venv\Scripts\python -m flask --app backend.app seed-dev
```

### 6.1 Ket qua mong doi

Ban se thay dai loai:

```text
Database initialized.
Seeded development users and vehicles.
```

### 6.2 Tai khoan seed san

Sau `seed-dev`, he thong co san:

- admin: `admin@example.com` / `Admin@123`
- user 1: `user1@example.com` / `123456`
- user 2: `user2@example.com` / `123456`

Va 2 bien so:

- `59A-12345` gan cho `user1@example.com`
- `51B-67890` gan cho `user2@example.com`

## 7. Chay backend

Chay:

```powershell
.\.venv\Scripts\python -m backend.app
```

Mac dinh backend mo tai:

```text
http://127.0.0.1:5000
```

### 7.1 Health check nhanh

Mo trinh duyet:

```text
http://127.0.0.1:5000/api/health
```

Neu dung, ban se thay:

```json
{"status":"ok"}
```

## 8. Mo frontend

Ban co 2 cach.

### Cach A: Mo truc tiep file HTML

Mo:

- [interface/index.html](F:\Code\IOT_2026\interface\index.html)
- hoac [interface/login.html](F:\Code\IOT_2026\interface\login.html)

### Cach B: Chay static server nho

Neu muon giong thuc te hon:

```powershell
cd interface
python -m http.server 8080
```

Luc do mo:

```text
http://127.0.0.1:8080
```

## 9. Dang nhap va kiem tra giao dien

### 9.1 Dang nhap admin

Vao trang login, nhap:

- Email: `admin@example.com`
- Password: `Admin@123`

Frontend se tu dung backend mac dinh `http://127.0.0.1:5000`, hoac dung gia tri da duoc doi truoc do trong `localStorage` neu co.

Ban se duoc dua toi dashboard admin.

Tai day ban co the:

- xem danh sach device
- xem alert log
- doi threshold global
- gan bien so cho user

### 9.2 Dang nhap user

Dang xuat admin, roi dang nhap:

- Email: `user1@example.com`
- Password: `123456`

Ban se duoc dua toi dashboard user.

Tai day ban co the:

- xem du lieu cua bien so duoc gan
- xem history
- xem alert
- xem `Payment History`
- xem tab `Tips / Sponsor` voi anh QR

## 10. Gui MQTT test

Backend chi co du lieu realtime khi broker nhan message dung format.

### 10.1 Payload mau hop le

```json
{
  "device_id": "charger-01",
  "bien_so_xe": "59A-12345",
  "current": 120,
  "voltage": 220,
  "power": 26400
}
```

### 10.2 Publish bang `mosquitto_pub`

Thay topic neu ban doi trong `.env`.

```powershell
mosquitto_pub -h 127.0.0.1 -p 1883 -t ev/charger/telemetry -m "{\"device_id\":\"charger-01\",\"bien_so_xe\":\"59A-12345\",\"current\":120,\"voltage\":220,\"power\":26400}"
```

Neu broker co username/password:

```powershell
mosquitto_pub -h 127.0.0.1 -p 1883 -u "<username>" -P "<password>" -t ev/charger/telemetry -m "{\"device_id\":\"charger-01\",\"bien_so_xe\":\"59A-12345\",\"current\":120,\"voltage\":220,\"power\":26400}"
```

### 10.3 Kiem tra ket qua mong doi

#### Tren dashboard user

- user `user1@example.com` thay du lieu cho bien so `59A-12345`
- current / power / history duoc cap nhat

#### Tren dashboard admin

- thay `charger-01`
- thay trang thai device
- thay bien so dang lien ket

## 11. Test alert

### 11.1 Alert current thap

```powershell
mosquitto_pub -h 127.0.0.1 -p 1883 -t ev/charger/telemetry -m "{\"device_id\":\"charger-01\",\"bien_so_xe\":\"59A-12345\",\"current\":20,\"voltage\":220,\"power\":4400}"
```

Ket qua mong doi:

- khong tao alert
- device o trang thai `not_charging`
- user dashboard khong co alert moi tu mau nay
- admin dashboard khong co alert log moi tu mau nay

### 11.2 Alert current cao

```powershell
mosquitto_pub -h 127.0.0.1 -p 1883 -t ev/charger/telemetry -m "{\"device_id\":\"charger-01\",\"bien_so_xe\":\"59A-12345\",\"current\":650,\"voltage\":220,\"power\":143000}"
```

Ket qua mong doi:

- sinh alert `high_current`
- admin va user thay canh bao moi

## 12. Test doi threshold global

### Cach nhanh tren giao dien admin

1. Dang nhap admin
2. Sua:
   - `Minimum current`
   - `Maximum current`
3. Bam `Save settings`
4. Publish lai MQTT payload moi

Neu threshold da doi dung, rule alert moi se ap dung cho message den sau do.

## 13. Test assign bien so cho user

Tren admin dashboard:

1. Chon user
2. Dien bien so
3. Neu can, dien `device_code`
4. Bam `Assign vehicle`

Sau do:

- user duoc gan bien so moi
- payload MQTT co `bien_so_xe` trung bien so do se map du lieu vao user

## 14. Chay test tu dong

Khi muon check nhanh backend:

```powershell
.\.venv\Scripts\python -m pytest backend\tests -q
```

Kiem tra compile Python:

```powershell
.\.venv\Scripts\python -m compileall backend interface
```

Kiem tra syntax JS:

```powershell
node --check interface\assets\js\api.js
node --check interface\assets\js\auth.js
node --check interface\assets\js\socket.js
node --check interface\assets\js\user-dashboard.js
node --check interface\assets\js\admin-dashboard.js
```

## 14.1 Tao du lieu gia 2 gio de test detector

Generator co san trong repo se tao 1 phien sac gia:

- `9-12A`
- `23-25.5V`
- keo dai khoang `120 phut`
- chen san mot vai diem outlier de test anomaly detection

Ghi ra file:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session
```

Mac dinh lenh nay sinh bo du lieu cho nhieu thiet bi va 2 bien so:

- devices: `esp32s3_01`, `esp32s3_02`, `esp32s3_03`, `esp32s3_04`
- plates: `59A-12345`, `51B-67890`

Publish truc tiep len broker:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session --publish --topic ina219/data
```

Mac dinh moi lan generate se dung seed random khac nhau.
Neu muon lap lai dung cung bo data:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session --seed 20260410
```

Neu muon generate 1 thiet bi duy nhat:

```powershell
.\.venv\Scripts\python -m backend.scripts.generate_fake_charging_session --single-device --device-code esp32s3_01 --license-plate 59A-12345
```

Neu ban muon detector thong ke co dat ngưong phu hop voi don vi `A`, hay dat settings admin xap xi:

- `Minimum current = 8.0`
- `Charging detection current = 8.5`
- `Maximum current = 18.0`

## 14.2 Nap fake payload truc tiep vao database

Neu ban muon fake payload duoc xem nhu data that trong dashboard, history, graph, va alert,
hay nap thang vao database:

```powershell
.\.venv\Scripts\python -m backend.scripts.load_fake_payloads_to_db
```

Lenh nay se:

- dam bao `user1@example.com` / `123456`
- dam bao `user2@example.com` / `123456`
- dam bao 2 bien so:
  - `59A-12345`
  - `51B-67890`
- tao du lieu cho 4 thiet bi
- chen lich su 2 gio vao database voi timestamp lich su da generate

Sau do:

1. Dang nhap `user1@example.com` / `123456`
2. Xem dashboard, history graph, payment history, alert nhu data that
3. Dang nhap `user2@example.com` / `123456`
4. Xem du lieu va payment history cho bien so cua user 2
5. Dang nhap admin va vao `Stations`, `Graphs`, `Alerts`

Neu muon nap 1 thiet bi duy nhat:

```powershell
.\.venv\Scripts\python -m backend.scripts.load_fake_payloads_to_db --single-device --device-code esp32s3_01 --license-plate 59A-12345
```

## 15. Checklist demo end-to-end

Lam theo thu tu nay:

1. Dien `.env`
2. Chay Mosquitto
3. Chay `init-db`
4. Chay `seed-dev`
5. Chay backend Flask
6. Mo frontend
7. Dang nhap admin
8. Dang nhap user
9. Publish MQTT hop le
10. Publish MQTT tao alert thap
11. Publish MQTT tao alert cao
12. Sua threshold global
13. Kiem tra realtime + history + alert

Neu 13 buoc nay deu thong, MVP cua ban da chay duoc tu dau den cuoi.

## 16. Loi thuong gap

### 16.1 Login duoc nhung khong co du lieu

Kiem tra:

- MQTT co dang publish dung topic khong
- `bien_so_xe` trong payload co trung bien so da gan cho user khong
- backend co dang chay khong

### 16.2 Khong thay realtime

Kiem tra:

- backend da chay tren dung host/port trong login page chua
- browser co block Socket.IO CDN khong
- console browser co loi JS khong

### 16.3 Khong ket noi duoc DB

Kiem tra:

- `DATABASE_URL` co dung thong tin Supabase khong
- Supabase co cho phep IP hien tai ket noi khong
- password DB co dung khong

### 16.4 Publish MQTT nhung khong co gi xay ra

Kiem tra:

- `MQTT_ENABLED=true`
- `MQTT_HOST`, `MQTT_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`
- `MQTT_SENSOR_TOPIC` co trung topic khi publish khong

## 17. Lenh tam dung backend

Neu dang chay backend trong terminal, bam:

```text
Ctrl + C
```

## 18. Ghi chu cuoi

Ban co the bat dau bang local demo truoc:

- Mosquitto local
- Supabase Postgres that
- frontend mo bang file hoac `http.server`

Sau khi local on dinh, moi dua tiep sang VPS, reverse proxy, HTTPS, va hardening bao mat.
