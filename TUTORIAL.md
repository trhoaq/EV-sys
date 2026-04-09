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
- user 1: `user1@example.com` / `Password1`
- user 2: `user2@example.com` / `Password1`

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
- Password: `Password1`

Ban se duoc dua toi dashboard user.

Tai day ban co the:

- xem du lieu cua bien so duoc gan
- xem history
- xem alert

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

- sinh alert `low_current`
- user dashboard thay alert moi
- admin dashboard thay alert log moi

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
