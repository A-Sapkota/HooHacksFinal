#include <MPU6050.h>
#include <Wire.h>

MPU6050 mpu;

float prevX = 0;
float prevY = 0;
float prevZ = 0;

// Thresholds for movement detection
const float TREMOR_THRESHOLD = 0.7;
const float JERK_THRESHOLD = 2.0;

void setup() {
  Serial.begin(9600);

  while (!mpu.begin(MPU6050_SCALE_2000DPS, MPU6050_RANGE_2G)) {
    Serial.println("Could not find a valid MPU6050 sensor, check wiring!");
    delay(500);
  }

  mpu.calibrateGyro();

  mpu.setThreshold(3);

  Serial.println("MPU6050 initialized successfully!");
}

void loop() {
  Vector normAccel = mpu.readNormalizeAccel();

  float deltaX = abs(normAccel.XAxis - prevX);
  float deltaY = abs(normAccel.YAxis - prevY);
  float deltaZ = abs(normAccel.ZAxis - prevZ);

  prevX = normAccel.XAxis;
  prevY = normAccel.YAxis;
  prevZ = normAccel.ZAxis;

  if (deltaX > TREMOR_THRESHOLD || deltaY > TREMOR_THRESHOLD || deltaZ > TREMOR_THRESHOLD) {
    Serial.println("hand shaking");
  }

  else if (deltaX > JERK_THRESHOLD || deltaY > JERK_THRESHOLD || deltaZ > JERK_THRESHOLD) {
    Serial.println("sudden movement");
  }

  else {
    Serial.println("no significant movement");
  }

  delay(100);
}