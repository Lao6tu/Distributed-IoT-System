#include <Wire.h>
#include <MQTT.h>
#include <WiFi.h>
#include <WiFiManager.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <RTClib.h>
#include <BH1750.h>
#include <Adafruit_INA219.h>
#include <Adafruit_Sensor.h>
#include <LiquidCrystal_I2C.h>

// Function prototypes
void publishData();
void lcdDisplay();
void checkNetwork();

// WiFi
// const char ssid[] = "";
// const char pass[] = "";    
// const int keyIndex = 0;                          
long rssi; // WiFi strength
WiFiClient net;

// MQTT
const char mqttServer[] = "192.168.0.105";
const int mqttServerPort = 1883;           
const char key[] = "";                    
const char secret[] = "";                
const char device[] = "esp32_fyp";        
const String topicRoot = "esp32";          
MQTTClient client;                     

// DHT sensor
#define DHTPIN 4
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);
float temperature;
float humidity;

// LED
const int led2_Pin = 13;
const int led1_Pin = 12;
uint8_t ledState = LOW;

// pb
const int buttonPin = 14;
unsigned long PBcurrentMillis = 0;
unsigned long PBpreviousMillis = 0;
int buttonState = 1;

// non-blocking lcd display
unsigned long PUBcurrentMillis = 0;
unsigned long PUBpreviousMillis = 0;
unsigned long LCDpreviousMillis = 0;
unsigned long LCDcurrentMillis = 0;
unsigned long LCDsecondMillis = 0;
enum lcd_State
{
  WiFi_info,
  case_datetime,
  case_dht11,
  case_voltage_current,
  case_power_light,
  case_battery_indicator
};
lcd_State currentState = WiFi_info;

//non-blocking main loop
unsigned long taskStartTime;
enum loop_State {
    INITIAL,
    DAY_TASK,
    NIGHT_TASK,
    NIGHT_SLEEP,
};
loop_State loopState = INITIAL;

// Current Sensor
Adafruit_INA219 ina219;
float shuntvoltage;
float busvoltage;
float current_mA;
float power_mW;
float loadvoltage;

// Light Sensor
BH1750 lightMeter;
float lux;

// set the LCD address
LiquidCrystal_I2C lcd(0x27, 16, 2);

// DS1307 RTC
RTC_DS1307 rtc;
char daysOfWeek[7][12] = {
  "Sun",
  "Mon",
  "Tue",
  "Wedy",
  "Thu",
  "Fri",
  "Sat"
};

// Battery Level Reader
const float batteryFactor = 1.273;
float batteryVoltage;
int batteryLevel;
long analogValue;
class AnalogAverageReader {
  public:
  AnalogAverageReader(int pin) : _pin(pin), _sum(0), _count(0), _startTime(0) {}
  void startReading(long duration, long interval) {
    _duration = duration;
    _interval = interval;
    _startTime = millis();
    _sum = 0;
    _count = 0;
    _lastReadTime = 0;
    _isReading = true;
  }
  bool update() {
    if (!_isReading) {
      return false;
    }
    if (millis() - _startTime > _duration) {
      _isReading = false;
      return false;
    }
    if (millis() - _lastReadTime >= _interval) {
      _sum += analogRead(_pin);
      _count++;
      _lastReadTime = millis();
    }
    return true;
  }
  int getAverage() {
    if (_count == 0) return 0;
    return _sum / _count;
  }
  bool isReading() {
    return _isReading;
  }
  private:
  int _pin;
  long _sum;
  int _count;
  long _duration;
  long _interval;
  unsigned long _startTime;
  unsigned long _lastReadTime;
  bool _isReading;
};
AnalogAverageReader analogReader(33);



///////////////////////////////////////////////////////////////////////// Setup
void setup()
{
  Serial.begin(115200);

  // WiFi OTA Manager
  WiFi.mode(WIFI_STA);
  WiFiManager wm; 
  bool wifi_state = wm.autoConnect("IoT_ESP32"); // anonymous ap
  // res = wm.autoConnect(); // auto generated AP name from chipid
  // wm.resetSettings(); // hide this when deploying
  // WiFi.begin(ssid, pass);
  
  // MQTT setup
  client.begin(mqttServer, mqttServerPort, net);
  client.connect(device);

  uint32_t currentFrequency; 
  Wire.begin(); // I2C setup
  ina219.begin(); // INA219 Setup
  lightMeter.begin(); // BH1750 Setup
  dht.begin(); // DHT11 Setup
  lcd.init(); // LCD Setup
  lcd.display(); // LCD display on
  lcd.backlight(); // Turn on LCD backlight
  rtc.begin(); // RTC setup
  rtc.adjust(DateTime(F(__DATE__),F(__TIME__)));

  pinMode(led1_Pin, OUTPUT);
  pinMode(led2_Pin, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(DHTPIN, INPUT);
}
///////////////////////////////////////////////////////////////////////// Setup



///////////////////////////////////////////////////////////////////////// Main Loop
void loop()
{ 
  switch (loopState) {
    case INITIAL:
    checkNetwork();
    loopState = TASK_RUNNING;
    break;

    case DAYTIME_TASK:
    lcdDisplay();
    client.loop(); 
    publishData();
    DateTime now = rtc.now();
    if (now.hour() >= 20 && now.hour() < 6){
      lcd.clear();
      lcd.print("Night Sleep...");
      delay(2000);
      loopState = NIGHT_SLEEP;
    }
    break;

    case NIGHT_SLEEP:
    esp_sleep_enable_timer_wakeup(5 * 60 * 1000000); // 5 min
    esp_light_sleep_start();
    DateTime now = rtc.now();
    lcd.print("Check Time...");
    delay(2000);
    if (now.hour() >= 20 && now.hour() < 6){
      lcd.clear();
      lcd.print("Night Sleep...");
      delay(2000);
      loopState = NIGHT_SLEEP;
    }
    else {
      lcd.clear();
      lcd.print("Wake Up...");
      delay(2000);
      loopState = INITIAL;
    }
    break;
  }
}
///////////////////////////////////////////////////////////////////////// Main Loop



void checkNetwork()
{
  unsigned long netpreviousMillis = 0;
  unsigned long netcurrentMillis = millis();
  // if WiFi is down, try reconnecting
  if ((WiFi.status() != WL_CONNECTED) && (netcurrentMillis - netpreviousMillis >= 10000))
  {
    digitalWrite(led1_Pin, LOW);
    digitalWrite(led2_Pin, HIGH);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("No network !");
    lcd.setCursor(0, 1);
    lcd.print("Reconnecting...");
    WiFi.disconnect();
    WiFi.reconnect();
    netpreviousMillis = netcurrentMillis;
  }
  else
  {
    digitalWrite(led1_Pin, HIGH);
    digitalWrite(led2_Pin, LOW);
  } 
  // if MQTT server is down, try reconnecting
  if((!client.connected()) && (netcurrentMillis - netpreviousMillis >= 10000))
  {
    digitalWrite(led1_Pin, LOW);
    digitalWrite(led2_Pin, HIGH);
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("No MQTT host !");
    lcd.setCursor(0, 1);
    lcd.print("Reconnecting...");
    client.begin(mqttServer, mqttServerPort, net);
    client.connect(device);
  }
  else
  {
    digitalWrite(led1_Pin, HIGH);
    digitalWrite(led2_Pin, LOW);
  }
}




void lcdDisplay()
{
  // LCD backlight and display
  PBcurrentMillis = millis();
  buttonState = digitalRead(buttonPin);
  if (buttonState == LOW)
  {
    PBpreviousMillis = PBcurrentMillis;
    lcd.backlight();
    currentState = case_datetime;
  }
  else if (PBcurrentMillis - PBpreviousMillis >= 30000)
  {
    lcd.noBacklight();
  }

  // LCD display status
  LCDcurrentMillis = millis();
  switch (currentState)
  {
    case case_datetime:
    if (LCDcurrentMillis - LCDpreviousMillis >= 3000)
    {
      DateTime now = rtc.now();
      lcd.clear();
      lcd.setCursor(0, 0);    
      lcd.print(now.year(), DEC);
      lcd.print('/');
      lcd.print(now.month(), DEC);
      lcd.print('/');
      lcd.print(now.day(), DEC);
      lcd.print(",");
      lcd.print(daysOfWeek[now.dayOfTheWeek()]);
      lcd.setCursor(0, 1);
      if (now.hour() < 10)
      lcd.print("0");
      lcd.print(now.hour(), DEC);
      lcd.print(':');
      if (now.minute() < 10)
      lcd.print("0");
      lcd.print(now.minute(), DEC);
      lcd.print(':');
      // Update seconds every second
      if (LCDcurrentMillis - LCDsecondMillis >= 1000) {
        lcd.setCursor(7, 1);
        if (now.second() < 10)
        lcd.print("0");
        lcd.print(now.second(), DEC);
        LCDsecondMillis = LCDcurrentMillis;
      }
      LCDpreviousMillis = LCDcurrentMillis;
      currentState = WiFi_info;
    }
    break;
    case WiFi_info:
    if (LCDcurrentMillis - LCDpreviousMillis >= 3000)
    {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print(WiFi.SSID());
      lcd.setCursor(0, 1);
      lcd.print(WiFi.RSSI());
      lcd.print(" dBm");
      LCDpreviousMillis = LCDcurrentMillis;
      currentState = case_dht11;
    }
    break;
    case case_dht11:
    if (LCDcurrentMillis - LCDpreviousMillis >= 3000)
    {
      // Create a custom Celsius degree symbol
      byte customDegreeChar[8] = {
        B00110,
        B01001,
        B01001,
        B00110,
        B00000,
        B00000,
        B00000,
        B00000
      };
      lcd.clear();
      lcd.createChar(1, customDegreeChar);
      lcd.setCursor(0, 0);
      lcd.print("Temp: ");
      lcd.print(temperature, 1);
      lcd.print(" ");
      lcd.write(byte(1));
      lcd.print("C");
      lcd.setCursor(0, 1);
      lcd.print("Humidity:");
      lcd.print(humidity, 0);
      lcd.print(" %");
      LCDpreviousMillis = LCDcurrentMillis;
      currentState = case_voltage_current;
    }
    break;
    case case_voltage_current:
    if (LCDcurrentMillis - LCDpreviousMillis >= 3000)
    {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Voltage:");
      lcd.print(loadvoltage, 2);
      lcd.print(" V");
      lcd.setCursor(0, 1);
      lcd.print("Current:");
      lcd.print(current_mA, 1);
      lcd.print(" mA");
      LCDpreviousMillis = LCDcurrentMillis;
      currentState = case_power_light;
    }
    break;
    case case_power_light:
    if (LCDcurrentMillis - LCDpreviousMillis >= 3000)
    {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Power:");
      lcd.print(power_mW, 1);
      lcd.print(" mW");
      lcd.setCursor(0, 1);
      lcd.print("Light:");
      lcd.print(lux, 0);
      lcd.print(" lux");
      LCDpreviousMillis = LCDcurrentMillis;
      currentState = case_battery_indicator;
    }
    break;
    case case_battery_indicator:
    if (LCDcurrentMillis - LCDpreviousMillis >= 3000)
    {
      lcd.clear();
      lcd.setCursor(0, 0);
      lcd.print("Battery:");
      lcd.print(batteryLevel, 0);
      lcd.print(" %");
      lcd.setCursor(0, 1);
      lcd.print("Voltage:");
      lcd.print(batteryVoltage, 2);
      lcd.print(" V");
      LCDpreviousMillis = LCDcurrentMillis;
      currentState = case_dht11;
    }
    break;
  }
}


void publishData()
{
  // Publish topic
  PUBcurrentMillis = millis();
  if (PUBcurrentMillis - PUBpreviousMillis >= 5000)
  {
    if (analogReader.isReading())
    analogReader.update();
    if (!analogReader.isReading()) {
      analogValue = analogReader.getAverage();
      batteryVoltage = analogValue * (3.3 / 4095.0) * batteryFactor;
      batteryLevel = map(analogValue, 3120, 4095, 0, 100);
      analogReader.startReading(5000, 500);
    }
    if (batteryLevel < 0)
    batteryLevel = 1;
    temperature = dht.readTemperature();
    humidity = dht.readHumidity();
    shuntvoltage = ina219.getShuntVoltage_mV();
    busvoltage = ina219.getBusVoltage_V();
    current_mA = ina219.getCurrent_mA();
    power_mW = ina219.getPower_mW();
    loadvoltage = busvoltage + (shuntvoltage / 1000);
    lux = lightMeter.readLightLevel();

    // Publish sensor reading
    client.publish(topicRoot + "/Battery/Voltage", String(batteryVoltage, 2) + " V");
    client.publish(topicRoot + "/Battery/Level", String(batteryLevel) + " %");
    client.publish(topicRoot + "/DH11/Temperature", String(temperature, 1) + " °C");
    client.publish(topicRoot + "/DH11/Humidity", String(humidity) + " %");
    client.publish(topicRoot + "/INA219/Bus Voltage", String(busvoltage, 2) + " V");
    client.publish(topicRoot + "/INA219/Shunt Voltage", String(shuntvoltage, 2) + " mV");
    client.publish(topicRoot + "/INA219/Load Voltage", String(loadvoltage, 2) + " V");
    client.publish(topicRoot + "/INA219/Current", String(current_mA, 2) + " mA");
    client.publish(topicRoot + "/INA219/Power", String(power_mW, 2) + " mW");
    client.publish(topicRoot + "/BH1750/Light", String(lux, 1) + " lx");

    PUBpreviousMillis = PUBcurrentMillis;
  }
}
