
#include <Wire.h>
#include <float.h>

#include <Adafruit_AMG88xx.h>
#include <NewPing.h>

#include <SharpIR.h>
#define IRSensor1 A0
SharpIR irSensor1(SharpIR::GP2Y0A41SK0F, IRSensor1);

#ifndef IRAM_ATTR
#define IRAM_ATTR
#endif

// ---- Pin defaults (change to match your wiring) ----
#ifndef AMG88XX_INT_PIN
#define AMG88XX_INT_PIN 2
#endif

#ifndef ULTRASONIC_TRIGGER_PIN
#define ULTRASONIC_TRIGGER_PIN 4
#endif

#ifndef ULTRASONIC_ECHO_PIN
#define ULTRASONIC_ECHO_PIN 3
#endif

#ifndef ULTRASONIC_MAX_DISTANCE_CM
#define ULTRASONIC_MAX_DISTANCE_CM 200
#endif

// ---- Globals ----
static char receivedChar = 0;
static bool ToAccumulate = false;
static String AccString;

static Adafruit_AMG88xx amg;
static bool amgReady = false;
static float pixels[AMG88xx_PIXEL_ARRAY_SIZE];

static volatile bool amgInterruptFired = false;

static void IRAM_ATTR amgIntISR() {
    amgInterruptFired = true;
}

static NewPing sonar(ULTRASONIC_TRIGGER_PIN, ULTRASONIC_ECHO_PIN, ULTRASONIC_MAX_DISTANCE_CM);

static float readMaxPixelTempC() {
    if (!amgReady) {
        return -999.0f;
    }

    amg.readPixels(pixels);

    float maxTemp = -FLT_MAX;
    for (uint8_t i = 0; i < AMG88xx_PIXEL_ARRAY_SIZE; i++) {
        if (pixels[i] > maxTemp) {
            maxTemp = pixels[i];
        }
    }
    return maxTemp;
}

static unsigned int readDistanceCm() {
    // Returns 0 if no echo / out of range.
    return sonar.ping_cm();
}

void setup() {
    delay(300);
    Serial.begin(115200);

    Wire.begin();
    amgReady = amg.begin();

    pinMode(AMG88XX_INT_PIN, INPUT_PULLUP);
    const int irq = digitalPinToInterrupt(AMG88XX_INT_PIN);
#if defined(NOT_AN_INTERRUPT)
    if (irq != NOT_AN_INTERRUPT) {
        attachInterrupt(irq, amgIntISR, FALLING);
    }
#else
    if (irq >= 0) {
        attachInterrupt(irq, amgIntISR, FALLING);
    }
#endif
}

void loop() {
    while (Serial.available()) {
        receivedChar = (char)Serial.read();

        if (receivedChar == '!') {
            ToAccumulate = true;
            AccString = "";
            continue;
        }

        if (receivedChar == '@') {
            ToAccumulate = false;

            if (AccString == "GET_SENSOR_READINGS") {
                float maxTempC = readMaxPixelTempC();
                unsigned int distCm = readDistanceCm();
                if (distCm == 0) {
                    distCm = irSensor1.getDistance();
                }
                Serial.print('!');
                Serial.print(maxTempC, 1);
                Serial.print('_');
                Serial.print(distCm);
                Serial.print('@');
                Serial.println();
            }

            continue;
        }

        if (ToAccumulate) {
            AccString += receivedChar;
        }
    }
}

void sendCommandAck() {
    Serial.println("(");
}
