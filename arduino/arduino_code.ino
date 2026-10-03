#include <SPI.h>
#include "Adafruit_MAX31855.h"
 
#define DO 13
#define CS 12
#define CLK 11
 
unsigned long last_checked_temp = 0;
bool measure = false;

#define LED_CONTROL_PIN 3
bool start_light = true;
bool led_on = true;
bool cmd_sent = false;
unsigned long last_checked_time = 0;

// Change these numbers for different times, system takes milliseconds so 10*1000 is 10 seconds, 30*60*1000 is 30 minutes, etc.
// first_on_interval and first_off_interval are only used once at the start of recording the video
// After that, the lights will continue to turn on and off based on later_on_interval and later_off_interval

// Light on for 30 mins beginning at when video begins recording
unsigned long first_on_interval = 2*60*1000;//10*1000;//

// Light off for 20 mins after light is on for the first time
unsigned long first_off_interval = 1*60*1000;//5*1000;//

// Light on and off every 20 mins
unsigned long later_on_interval = 1*60*1000;//5*1000;//
unsigned long later_off_interval = 1*60*1000;//5*1000;//

Adafruit_MAX31855 thermocouple(CLK, CS, DO);

void setup() {
  Serial.begin(115200);
  pinMode(LED_CONTROL_PIN, OUTPUT);
  digitalWrite(LED_CONTROL_PIN, HIGH);
  start_light = true;
  cmd_sent = false;
  measure = false;
  delay(500);
}

void LED_and_temp(){
    if (Serial.available()){
        char cmd = Serial.read();
        if (cmd == '0'){
            if (not led_on){
                digitalWrite(LED_CONTROL_PIN, HIGH);
                Serial.println("TXT: LED turned on");
            } else {
                Serial.println("TXT: LED already on");
            }
            led_on = true;
            cmd_sent = false;
        } else if (cmd == '1'){
            if (not led_on){
                digitalWrite(LED_CONTROL_PIN, HIGH);
                Serial.println("TXT: LED turned on");
            } else{
                Serial.println("TXT: LED already on");
            }
            start_light = true;
            led_on = true;
            cmd_sent = true;
            last_checked_time = millis();
        } else if (cmd == '2'){
            double temp = thermocouple.readCelsius();
            Serial.print("TEMP:");
            Serial.println(temp);
            last_checked_temp = millis();
            measure = true;
        } else if (cmd == '3'){
            measure = false;
        }
    }
    if (cmd_sent and start_light){
        if (led_on and millis() - last_checked_time == first_on_interval){
            digitalWrite(LED_CONTROL_PIN, LOW);
            Serial.println("TXT: LED turned off");
            led_on = false;
            last_checked_time = millis();
        } else if (not led_on and millis() - last_checked_time == first_off_interval){
            digitalWrite(LED_CONTROL_PIN, HIGH);
            Serial.println("TXT: LED turned on");
            led_on = true;
            start_light = false;
            last_checked_time = millis();
        }
    } else if (cmd_sent){
        if (led_on and millis() - last_checked_time == later_on_interval){
            digitalWrite(LED_CONTROL_PIN, LOW);
            Serial.println("TXT: LED turned off");
            led_on = false;
            last_checked_time = millis();
        } else if (not led_on and millis() - last_checked_time == later_off_interval){
            digitalWrite(LED_CONTROL_PIN, HIGH);
            Serial.println("TXT: LED turned on");
            led_on = true;
            last_checked_time = millis();
        }
    }
    if (measure and millis() - last_checked_temp >= 1000) {
        double temp = thermocouple.readCelsius();
        Serial.print("TEMP:");
        Serial.println(temp);
        last_checked_temp = millis();
    }
}

void LED_on_and_off(){
    // Turn the LED strip off and on every 20 mins
    if (Serial.available()){
        char cmd = Serial.read();
        if (cmd == '0'){
            if (not led_on){
                digitalWrite(LED_CONTROL_PIN, HIGH);
                Serial.println("TXT: LED turned on");
            } else {
                Serial.println("TXT: LED already on");
            }
            led_on = true;
            cmd_sent = false;
        } else if (cmd == '1'){
            if (not led_on){
                digitalWrite(LED_CONTROL_PIN, HIGH);
                Serial.println("TXT: LED turned on");
            } else{
                Serial.println("TXT: LED already on");
            }
            start_light = true;
            led_on = true;
            cmd_sent = true;
            last_checked_time = millis();
        }
    }
    if (cmd_sent and start_light){
        if (led_on and millis() - last_checked_time == first_on_interval){
            digitalWrite(LED_CONTROL_PIN, LOW);
            Serial.println("TXT: LED turned off");
            led_on = false;
            last_checked_time = millis();
        } else if (not led_on and millis() - last_checked_time == first_off_interval){
            digitalWrite(LED_CONTROL_PIN, HIGH);
            Serial.println("TXT: LED turned on");
            led_on = true;
            start_light = false;
            last_checked_time = millis();
        }
    } else if (cmd_sent){
        if (led_on and millis() - last_checked_time == later_on_interval){
            digitalWrite(LED_CONTROL_PIN, LOW);
            Serial.println("TXT: LED turned off");
            led_on = false;
            last_checked_time = millis();
        } else if (not led_on and millis() - last_checked_time == later_off_interval){
            digitalWrite(LED_CONTROL_PIN, HIGH);
            Serial.println("TXT: LED turned on");
            led_on = true;
            last_checked_time = millis();
        }
    }
}

void send_temp(){
  if (Serial.available()){
    char cmd = Serial.read();
    if (cmd == '2'){
      double temp = thermocouple.readCelsius();
      Serial.print("TEMP:");
      Serial.println(temp);
      last_checked_temp = millis();
      measure = true;
    } else if (cmd == '3'){
      measure = false;
    }
  }
  if (measure and millis() - last_checked_temp >= 1000){
    double temp = thermocouple.readCelsius();
    Serial.print("TEMP:");
    Serial.println(temp);
    last_checked_temp = millis();
  }
}

void loop() {
//   LED_on_and_off();
//   send_temp();
  LED_and_temp();
}
