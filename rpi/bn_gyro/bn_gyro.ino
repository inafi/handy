#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>
#define BNO055_SAMPLERATE_DELAY_MS (100)

//  Connect SCL to analog 5
//  Connect SDA to analog 4
Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x28);
float duration, distance;

void displaySensorDetails(void) {
  sensor_t sensor;
  bno.getSensor(&sensor);
  delay(500);
}

void setup(void) {
  Serial.begin(115200);
  Serial.println("");
  if (!bno.begin()) {
    Serial.print("BNO055 not detected");
    while (1);
  }
  bno.setExtCrystalUse(true);
  displaySensorDetails();
  pinMode(11, OUTPUT);
  pinMode(12, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, INPUT);
  pinMode(9, OUTPUT);
  pinMode(10, INPUT);
  digitalWrite(11, HIGH);
  digitalWrite(12, HIGH);
  delay(1000);
}

void loop(void) {
  sensor(6, 7);
  sensors_event_t event;
  bno.getEvent(&event);
  Serial.print((int)event.orientation.x);
  Serial.print(F(" "));
  Serial.print((int)event.orientation.y);
  Serial.print(F(" "));
  Serial.print((int)event.orientation.z);
  Serial.println(F(""));

  uint8_t sys, gyro, accel, mag = 0;
  bno.getCalibration(&sys, &gyro, &accel, &mag);
  //  Serial.print(F("Calibration: "));
  //  Serial.print(sys, DEC);
  //  Serial.print(F(" "));
  //  Serial.print(gyro, DEC);
  //  Serial.print(F(" "));
  //  Serial.print(accel, DEC);
  //  Serial.print(F(" "));
  //  Serial.println(mag, DEC);

  delay(BNO055_SAMPLERATE_DELAY_MS);
}


void sensor(int trigPin, int echoPin) {
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);

  duration = pulseIn(echoPin, HIGH);
  distance = (duration * .0343) / 2;
  Serial.print(distance / 2.54);
  Serial.print(" ");
}
