#include <WiFi.h>
#include <PubSubClient.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ILI9341.h>
#include "qrcode.h"

HardwareSerial NanoSerial(1);

#define RXD1 18
#define TXD1 17

#define TFT_CS   15
#define TFT_DC    2
#define TFT_RST   4

#define BUTTON_PIN 27

// ===== WIFI =====
const char* ssid = "Le Sang";
const char* password = "@1972sang";

// ===== MQTT =====
const char* mqtt_server = "192.168.1.74";
const int   mqtt_port   = 1883;
const char* mqtt_user   = "";
const char* mqtt_pass   = "";
const char* mqtt_topic  = "ina219/data";

WiFiClient espClient;
PubSubClient client(espClient);

// ===== DATA =====
float busV = 0.0;
float current_mA = 0.0;
float power_mW = 0.0;
float loadV = 0.0;

String deviceId = "esp32s3_01";
unsigned long lastPublish = 0;
const unsigned long PUBLISH_INTERVAL_MS = 1000;
bool hasFreshData = false;

// ===== SCREEN =====
// 0 = QR, 1 = STATUS
bool currentScreen = 1;          // default là status
bool lastButtonState = HIGH;
unsigned long lastDebounceTime = 0;
const unsigned long debounceDelay = 80;

Adafruit_ILI9341 tft = Adafruit_ILI9341(TFT_CS, TFT_DC, TFT_RST);

// ========================= WIFI / MQTT =========================
void connectWiFi() {
  WiFi.begin(ssid, password);
  Serial.print("Dang ket noi WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi OK");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void connectMQTT() {
  while (!client.connected()) {
    Serial.print("Dang ket noi MQTT...");

    bool ok;
    if (strlen(mqtt_user) == 0) {
      ok = client.connect(deviceId.c_str());
    } else {
      ok = client.connect(deviceId.c_str(), mqtt_user, mqtt_pass);
    }

    if (ok) {
      Serial.println(" OK");
    } else {
      Serial.print(" Loi, rc=");
      Serial.print(client.state());
      Serial.println(" thu lai sau 2s");
      delay(2000);
    }
  }
}

// ========================= UART =========================
void readNanoData() {
  if (!NanoSerial.available()) return;

  String data = NanoSerial.readStringUntil('\n');
  data.trim();

  if (data.length() == 0) return;

  Serial.print("[UART] ");
  Serial.println(data);

  int p1 = data.indexOf(',');
  int p2 = data.indexOf(',', p1 + 1);
  int p3 = data.indexOf(',', p2 + 1);

  if (p1 > 0 && p2 > p1 && p3 > p2) {
    busV       = data.substring(0, p1).toFloat();
    current_mA = data.substring(p1 + 1, p2).toFloat();
    power_mW   = data.substring(p2 + 1, p3).toFloat();
    loadV      = data.substring(p3 + 1).toFloat();
    hasFreshData = true;

    Serial.println("[UART] Parse OK");
  } else {
    Serial.println("[UART] Sai dinh dang");
  }
}

// ========================= MQTT PUBLISH =========================
void publishData() {
  String bienSoXe = "59A-12345";

  String payload = "{";
  payload += "\"device_id\":\"" + deviceId + "\",";
  payload += "\"license_plate\":\"" + bienSoXe + "\",";
  payload += "\"current\":" + String(current_mA, 0) + ",";
  payload += "\"voltage\":" + String(loadV, 2) + ",";
  payload += "\"power\":" + String(power_mW, 0);
  payload += "}";

  bool ok = client.publish(mqtt_topic, payload.c_str());

  Serial.print("[MQTT] Publish: ");
  Serial.println(payload);

  if (ok) {
    Serial.println("[MQTT] Thanh cong");
  } else {
    Serial.println("[MQTT] That bai");
  }
}

// ========================= SCREEN =========================
void drawQRScreen() {
  tft.fillScreen(ILI9341_WHITE);

  tft.setTextColor(ILI9341_BLUE);
  tft.setTextSize(2);
  tft.setCursor(50, 20);
  tft.print("XIN MOI CHUYEN TIEN");

  const char* myVietQR = "00020101021138540010A00000072701240006970422011003954637150208QRIBFTTA53037045802VN6304bcb4";

  QRCode qrcode;
  uint8_t qrcodeData[qrcode_getBufferSize(10)];
  qrcode_initText(&qrcode, qrcodeData, 10, 0, myVietQR);

  int scale = 3;
  int x_offset = (tft.width() - (qrcode.size * scale)) / 2;
  int y_offset = 60;

  for (uint8_t y = 0; y < qrcode.size; y++) {
    for (uint8_t x = 0; x < qrcode.size; x++) {
      if (qrcode_getModule(&qrcode, x, y)) {
        tft.fillRect(
          x_offset + x * scale,
          y_offset + y * scale,
          scale,
          scale,
          ILI9341_BLACK
        );
      }
    }
  }
}

void drawStatusFrame() {
  tft.fillScreen(ILI9341_BLACK);

  tft.setTextColor(ILI9341_GREEN);
  tft.setTextSize(3);
  tft.setCursor(20, 15);
  tft.print("TRANG THAI SAC");

  tft.drawLine(10, 50, 310, 50, ILI9341_DARKCYAN);

  tft.setTextSize(2);
  tft.setTextColor(ILI9341_YELLOW);
  tft.setCursor(20, 70);
  tft.print("Voltage:");

  tft.setCursor(20, 120);
  tft.print("Current:");

  tft.setCursor(20, 170);
  tft.print("Power:");
}

void updateStatusValues() {
  if (currentScreen != 1) return;

  // Xóa vùng giá trị cũ
  tft.fillRect(150, 65, 150, 30, ILI9341_BLACK);
  tft.fillRect(150, 115, 150, 30, ILI9341_BLACK);
  tft.fillRect(150, 165, 150, 30, ILI9341_BLACK);

  tft.setTextSize(2);
  tft.setTextColor(ILI9341_WHITE);

  tft.setCursor(150, 70);
  tft.print(loadV, 2);
  tft.print(" V");

  tft.setCursor(150, 120);
  tft.print(current_mA, 0);
  tft.print(" mA");

  tft.setCursor(150, 170);
  tft.print(power_mW, 0);
  tft.print(" mW");
}

void drawStatusScreen() {
  drawStatusFrame();
  updateStatusValues();
}

// ========================= BUTTON =========================
void handleButton() {
  bool reading = digitalRead(BUTTON_PIN);

  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }

  if ((millis() - lastDebounceTime) > debounceDelay) {
    static bool buttonState = HIGH;

    if (reading != buttonState) {
      buttonState = reading;

      // nhấn nút
      if (buttonState == LOW) {
        currentScreen = !currentScreen;

        if (currentScreen == 0) {
          drawQRScreen();
        } else {
          drawStatusScreen();
        }
      }
    }
  }

  lastButtonState = reading;
}

// ========================= SETUP =========================
void setup() {
  Serial.begin(115200);
  NanoSerial.begin(9600, SERIAL_8N1, RXD1, TXD1);

  pinMode(BUTTON_PIN, INPUT_PULLUP);

  connectWiFi();
  client.setServer(mqtt_server, mqtt_port);
  connectMQTT();

  tft.begin();
  tft.setRotation(1);

  // default màn status
  drawStatusScreen();
}

// ========================= LOOP =========================
void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();

  handleButton();
  readNanoData();

  // nếu đang ở màn status thì cập nhật realtime
  static unsigned long lastScreenUpdate = 0;
  if (currentScreen == 1 && millis() - lastScreenUpdate >= 500) {
    updateStatusValues();
    lastScreenUpdate = millis();
  }

  if (hasFreshData && millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
    publishData();
    lastPublish = millis();
    hasFreshData = false;
  }
}