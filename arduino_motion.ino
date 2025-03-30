#include <ICM_20948.h>                      // https://github.com/sparkfun/SparkFun_ICM-20948_ArduinoLibrary
extern "C" {
#include "cnn_model.h"
}

#define SAMPLE_RATE 20

// ICM
ICM_20948_I2C icm;

static long long timer = 0;

char msg[64];
static unsigned int inference_count = 0;

static float accel_buf[MODEL_INPUT_SAMPLES][MODEL_INPUT_CHANNELS];
static size_t sample_i = 0;

void setup() {
  // 10-14-21: Mandatory on new board revision otherwise I2C does not work
  pinMode(SD_ON_OFF, OUTPUT);
  digitalWrite(SD_ON_OFF, HIGH);

  // Initialize pin for blinking LED
  pinMode(PIN_LED, OUTPUT);

  // Initialize serial port
  Serial.begin(115200);

  // Wait for initialization
  while (!Serial && millis() < 5000);

  // Initialize I2C used by IMU
  Wire.begin();

  // Initialize IMU
  icm.begin(Wire, 0);

  // Set sample rate to ~20Hz
  icm.setSampleRate((ICM_20948_Internal_Acc | ICM_20948_Internal_Gyr), {56, 55}); // a = 56 -> 20.09Hz, g = 55 -> 20Hz 

  // Notify readyness
  Serial.println("READY");

  timer = millis();
}

void loop() {
  const char* labels[] = {
    "No particular movement", 
    "Hand shaking", 
    "Sudden movement"
  };


  if (sample_i < MODEL_INPUT_SAMPLES) {
    // Try to respect sampling rate
    if (millis() > timer + (1000 / SAMPLE_RATE)) {
      timer = millis();
      
      if (icm.dataReady()) {
        // Read accelerometer data
        icm.getAGMT(); // The values are only updated when you call 'getAGMT'
      }
      
      // Blink LED for activity indicator
      // digitalWrite(PIN_LED, 1 - digitalRead(PIN_LED)); 
  
      // Read accelerometer data
      accel_buf[sample_i][0] = icm.accX() / 1000.0f;
      accel_buf[sample_i][1] = icm.accY() / 1000.0f;
      accel_buf[sample_i][2] = icm.accZ() / 1000.0f;

      // Format message with accelerometer data
      snprintf(msg, sizeof(msg), "0,%f,%f,%f\r\n", accel_buf[sample_i][0], accel_buf[sample_i][1], accel_buf[sample_i][2]);

      // Send message over serial port
      // Serial.print(msg);

      sample_i++;
    }
  } else { // Buffer is full, perform inference
    static number_t inputs[MODEL_INPUT_CHANNELS][MODEL_INPUT_SAMPLES];
    static number_t outputs[MODEL_OUTPUT_SAMPLES];

    long long t_start = millis();
    int label;

    // Convert inputs from floating-point then to fixed-point
    for (size_t i = 0; i < MODEL_INPUT_SAMPLES; i++) {
      for (size_t j = 0; j < MODEL_INPUT_CHANNELS; j++) {
        inputs[j][i] = clamp_to_number_t((long_number_t)(accel_buf[i][j] * (1<<FIXED_POINT)));
      }
    }

    // digitalWrite(PIN_LED, HIGH);
    // Run inference
    cnn(inputs, outputs);
    // digitalWrite(PIN_LED, LOW); 
    
    // TODO: Get output class

    // Get output class
    label = 0;
    float max_val = outputs[0];
    for (unsigned int i = 1; i < MODEL_OUTPUT_SAMPLES; i++) {
      if (max_val < outputs[i]) {
        max_val = outputs[i];
        label = i;
      }
    }
    
    inference_count++;

    // char msg[64];
    snprintf(msg, sizeof(msg), "%d,%d,%f - %s", inference_count, label, (double)max_val, labels[label]);
    Serial.println(msg);

    if (label == 1 || label == 2) {
      digitalWrite(LS_LED_BLUE, HIGH);
      delay(300); // blink duration
      digitalWrite(LS_LED_BLUE, LOW);
    }

    sample_i = 0;

  }
}
