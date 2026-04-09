#include <WiFi.h>
#include <PubSubClient.h>

HardwareSerial NanoSerial(1);

#define RXD1 18
#define TXD1 17

// ===== WIFI =====
const char* ssid = "ten wifi";
const char* password = "password";

// ===== MQTT =====
const char* mqtt_server = "ipv4";
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
const unsigned long PUBLISH_INTERVAL_MS = 10000;
bool hasFreshData = false;

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

void setup() {
  Serial.begin(115200);
  NanoSerial.begin(9600, SERIAL_8N1, RXD1, TXD1);

  connectWiFi();
  client.setServer(mqtt_server, mqtt_port);
  connectMQTT();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    connectWiFi();
  }

  if (!client.connected()) {
    connectMQTT();
  }

  client.loop();
  readNanoData();

  if (hasFreshData && millis() - lastPublish >= PUBLISH_INTERVAL_MS) {
    publishData();
    lastPublish = millis();
    hasFreshData = false;
  }
}