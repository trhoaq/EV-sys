#include <Wire.h>
#include <Adafruit_INA219.h>
#include <SoftwareSerial.h>

Adafruit_INA219 ina219;

// Chỉ cần TX để gửi đi
SoftwareSerial mySerial(2, 3); // RX, TX
// RX chân 2 không dùng, TX chân 3 dùng để gửi sang ESP32-S3

void setup() {
  Serial.begin(9600);
  mySerial.begin(9600);

  if (!ina219.begin()) {
    Serial.println("Khong tim thay INA219");
    while (1);
  }

  Serial.println("INA219 OK");
}

void loop() {
  float shuntvoltage = ina219.getShuntVoltage_mV();
  float busvoltage   = ina219.getBusVoltage_V();
  float current_mA   = ina219.getCurrent_mA();
  float power_mW     = ina219.getPower_mW();
  float loadvoltage  = busvoltage + (shuntvoltage / 1000.0);

  // Gửi 1 dòng dữ liệu dạng CSV
  mySerial.print(busvoltage, 3);
  mySerial.print(",");
  mySerial.print(current_mA, 3);
  mySerial.print(",");
  mySerial.print(power_mW, 3);
  mySerial.print(",");
  mySerial.println(loadvoltage, 3);

  // In ra Serial Monitor của Nano để kiểm tra
  Serial.print("Bus Voltage: "); Serial.print(busvoltage, 3); Serial.println(" V");
  Serial.print("Current    : "); Serial.print(current_mA, 3); Serial.println(" mA");
  Serial.print("Power      : "); Serial.print(power_mW, 3); Serial.println(" mW");
  Serial.print("Load Volt  : "); Serial.print(loadvoltage, 3); Serial.println(" V");
  Serial.println("----------------------");

  delay(1000);
}