#include <WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <LiquidCrystal_I2C.h>
#include <ArduinoJson.h>
#include <esp_wifi.h>    
#include <WiFiManager.h> 

const char* mqtt_server = "192.168.0.194"; // <-- PONER LA IP DEL COMANDO 'hostname -I' EN LA RASPBERRY

#define DHTPIN 4       
#define DHTTYPE DHT11
#define PIN_LED 15

const int rowPins[4] = {13, 12, 14, 27}; 
const int colPins[4] = {26, 25, 33, 32}; 
const char keys[4][4] = {
  {'1','2','3','A'},
  {'4','5','6','B'},
  {'7','8','9','C'},
  {'*','0','#','D'}
};

DHT dht(DHTPIN, DHTTYPE);
LiquidCrystal_I2C lcd(0x27, 16, 2); 
WiFiClient espClient;
PubSubClient client(espClient);

unsigned long tiempoAnterior = 0;
const long intervalo = 5000;

float limiteTemp = 28.0; 
String inputTeclado = ""; 
bool modoConfig = false; 

// Variables de control avanzado
bool modoAuto = true;        
bool releActivo = false;     
float tempFiltrada = 0.0;    
bool primeraLectura = true;
bool forzarDibujo = true; 

// Variables globales para la MAC y los tópicos dinámicos
String macLimpia = "";
String topicoTelemetria = "";
String topicoControl = "";
const String TENANT = "ic3_grupo1";

void setup_wifi() {
  // 1. Obtenemos la MAC limpia primero para usarla como nombre único del Access Point
  macLimpia = WiFi.macAddress();
  macLimpia.replace(":", ""); 

  WiFiManager wm;
  
  // 2. Creamos el nombre de la red Wi-Fi temporal que creará la placa (Ej: IC3_Edge_A0B765FEDCBA)
  String nombreAP = "IC3_Edge_" + macLimpia;
  
  Serial.println("Buscando redes Wi-Fi guardadas en memoria...");
  
  // 3. Intenta conectar. Si no hay red guardada o cambió la clave, levanta el portal (clave: admin1234)
  if (!wm.autoConnect(nombreAP.c_str(), "admin1234")) {
    Serial.println("Fallo al conectar y tiempo agotado. Reiniciando placa...");
    delay(3000);
    ESP.restart();
  }
  
  // 4. Activa el ahorro de energía del módem Wi-Fi una vez que ya está conectado a internet
  esp_wifi_set_ps(WIFI_PS_MIN_MODEM); 

  // 5. Estructura exigida por la materia: tenant/MAC/componente/variable
  topicoTelemetria = TENANT + "/" + macLimpia + "/dht11/telemetria";
  topicoControl = TENANT + "/" + macLimpia + "/control/limite";
  
  Serial.println("\n--- ¡Conectado exitosamente al Wi-Fi! ---");
  Serial.print("MAC Identificadora (Edge ID): ");
  Serial.println(macLimpia);
  Serial.print("IP asignada por el router: ");
  Serial.println(WiFi.localIP());
  Serial.print("Tópico de Envío: ");
  Serial.println(topicoTelemetria);
  Serial.print("Tópico de Escucha: ");
  Serial.println(topicoControl);
}

// Escucha los mensajes que llegan desde el Dashboard o Backend
void callback(char* topic, byte* payload, unsigned int length) {
  String mensaje = "";
  for (int i = 0; i < length; i++) {
    mensaje += (char)payload[i];
  }
  
  // Convertimos el mensaje recibido a número y pisamos el límite actual
  limiteTemp = mensaje.toFloat();
  
  // Forzamos a que la pantalla se actualice al instante para mostrar el nuevo límite
  forzarDibujo = true; 
  Serial.println("Nuevo límite recibido por MQTT (" + String(topic) + "): " + String(limiteTemp));
}

void reconnect() {
  while (!client.connected()) {
    // Usamos la MAC limpia como ID de cliente MQTT único para escalar de 1 a N dispositivos
    if (client.connect(macLimpia.c_str())) {
      client.subscribe(topicoControl.c_str()); 
      Serial.println("Conectado a MQTT. Suscrito a: " + topicoControl);
      break;
    }
    delay(5000);
  }
}

char leerTeclado() {
  for (int r = 0; r < 4; r++) {
    digitalWrite(rowPins[r], HIGH); 
    for (int c = 0; c < 4; c++) {
      if (digitalRead(colPins[c]) == HIGH) { 
        delay(50); 
        while(digitalRead(colPins[c]) == HIGH); 
        digitalWrite(rowPins[r], LOW);
        return keys[r][c];
      }
    }
    digitalWrite(rowPins[r], LOW); 
  }
  return '\0'; 
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  dht.begin();
  
  for (int i = 0; i < 4; i++) {
    pinMode(rowPins[i], OUTPUT);
    digitalWrite(rowPins[i], LOW);
    pinMode(colPins[i], INPUT_PULLDOWN); 
  }

  lcd.init();      
  lcd.backlight(); 
  lcd.print("Iniciando...");
  setup_wifi();
  
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback); 
  
  lcd.clear();
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();

  bool actualizarPantalla = forzarDibujo; 
  forzarDibujo = false; 
  unsigned long tiempoActual = millis();

  // 1. LECTURA Y FILTRO EMA (Cada 5s)
  if (tiempoActual - tiempoAnterior >= intervalo) {
    tiempoAnterior = tiempoActual;
    float t_cruda = dht.readTemperature(); 
    float h = dht.readHumidity();
    
    if (!isnan(t_cruda) && !isnan(h)) {
      if (primeraLectura) {
        tempFiltrada = t_cruda;
        primeraLectura = false;
      } else {
        tempFiltrada = (0.3 * t_cruda) + (0.7 * tempFiltrada); 
      }

      // Lógica de Histéresis
      if (modoAuto) {
        if (tempFiltrada >= limiteTemp) {
          releActivo = true;
        } else if (tempFiltrada <= (limiteTemp - 1.0)) {
          releActivo = false;
        }
      }
      digitalWrite(PIN_LED, releActivo ? HIGH : LOW);
      actualizarPantalla = true; 

      // Armado del JSON
      StaticJsonDocument<200> doc;
      doc["temp"] = tempFiltrada; 
      doc["hum"] = h;
      doc["limite"] = limiteTemp; 
      doc["rele"] = releActivo ? (modoAuto ? "ON (Auto)" : "ON (Man)") : (modoAuto ? "OFF (Auto)" : "OFF (Man)"); 

      char buffer[256];
      serializeJson(doc, buffer);
      
      // Publicamos en el tópico dinámico (ej: ic3_grupo1/A0B765FEDCBA/dht11/telemetria)
      client.publish(topicoTelemetria.c_str(), buffer); 
    }
  }

  // 2. TECLADO Y MENÚ HMI
  char tecla = leerTeclado();
  if (tecla != '\0') {
    actualizarPantalla = true; 
    
    if (!modoConfig) {
      if (tecla == '#') { modoConfig = true; inputTeclado = ""; lcd.clear(); }
      else if (tecla == 'A') { modoAuto = true; } 
      else if (tecla == 'B') { modoAuto = false; } 
      else if (tecla == 'C' && !modoAuto) { 
        releActivo = !releActivo; 
        digitalWrite(PIN_LED, releActivo ? HIGH : LOW);
      }
    } else {
      if (tecla >= '0' && tecla <= '9') { inputTeclado += tecla; } 
      else if (tecla == '#') {
        if (inputTeclado.length() > 0) limiteTemp = inputTeclado.toFloat(); 
        modoConfig = false; inputTeclado = ""; 
        lcd.clear(); lcd.print("Lim. Guardado!"); delay(1000); lcd.clear(); forzarDibujo = true;
      } 
      else if (tecla == '*') {
        modoConfig = false; inputTeclado = ""; 
        lcd.clear(); lcd.print("Cancelado"); delay(1000); lcd.clear(); forzarDibujo = true;
      }
    }
  }

  // 3. ACTUALIZACIÓN LCD
  if (actualizarPantalla) {
    if (!modoConfig) {
      lcd.setCursor(0, 0);
      lcd.print("T:" + String(tempFiltrada, 1) + " L:" + String(limiteTemp, 0) + "  "); 
      lcd.setCursor(0, 1);
      String modoStr = modoAuto ? "AUTO" : "MAN ";
      String estadoStr = releActivo ? "ON " : "OFF";
      lcd.print(modoStr + " -> " + estadoStr + "    "); 
    } else {
      lcd.setCursor(0, 0); lcd.print("Ingrese limite: "); 
      lcd.setCursor(0, 1); lcd.print("> " + inputTeclado + "             "); 
    }
  }
}