#include "I2Cdev.h"
#include "Wire.h"
#include <avr/pgmspace.h>
#include <ArduinoJson.h>
#include <SD.h>
#include <SPI.h>
#include <Arduino.h>
#include "wiring_private.h"
#include <Arduino_LSM9DS1.h> // Incluye la biblioteca para la IMU de 9 ejes
#include <TensorFlowLite.h>
#include <tensorflow/lite/micro/all_ops_resolver.h>
#include <tensorflow/lite/micro/micro_error_reporter.h>
#include <tensorflow/lite/micro/micro_interpreter.h>
#include <tensorflow/lite/schema/schema_generated.h>
#include <tensorflow/lite/version.h>
#include "model.h"
#define LEDSTOP 2
#define LEDWALK 3
#define LEDRUN 4

tflite::MicroErrorReporter tflErrorReporter;
tflite::AllOpsResolver tflOpsResolver;

const tflite::Model* tflModel = nullptr;
tflite::MicroInterpreter* tflInterpreter = nullptr;
TfLiteTensor* tflInputTensor = nullptr;
TfLiteTensor* tflOutputTensor = nullptr;
constexpr int tensorArenaSize = 8 * 1024;
byte tensorArena[tensorArenaSize];

const char* CLASSES[] = {"Stop","Walk","Run"};
#define NUM_CLASSES (sizeof(CLASSES) / sizeof(CLASSES[0]))

struct Config {
    char hostname[32];
    int port;
    char token[32];
    char SSDI[32];
    char password[32];
};
Config config; // Estructura de datos
UART esp8266 (digitalPinToPinName(5), digitalPinToPinName(6), NC, NC);
String respuesta;
double entrada[6];
int salida[] = {0, 0, 0};
int salida_anterior[] = {0, 0, 0};
int actuales[6];
int anteriores[6];
const double conversor[]={ 2.0 * 9.81 / 32768.0, 250.0 / 32768.0 }; // {accScale, gyroScale}
const double normalizador[] = { 20.25, 18.25, 23.5, 113.25, 186.5, 131.5 };

int grupo_1[] = {0, 0, 0, 0, 0};
int grupo_2[] = {0, 0, 0, 0, 0};
int grupo_3[] = {0, 0, 0, 0, 0};
int grupo_4[] = {0, 0, 0, 0, 0};

void loadConfiguration(Config &config) { // Carga el archivo de configuración
  const char *archivoConfig = "/CONFIG.txt";
  File archivo = SD.open(archivoConfig); // Abre el archivo
  StaticJsonDocument<512> doc; // Reservamos la memoria del archivo json
  DeserializationError error = deserializeJson(doc, archivo);
  if (error) {
    Serial.println("Error de lectura");
    return;
  }
  config.port = doc["port"];
  strlcpy(config.hostname, doc["hostname"], sizeof(config.hostname));
  strlcpy(config.token, doc["token"], sizeof(config.token));
  strlcpy(config.SSDI, doc["SSDI"], sizeof(config.SSDI));
  strlcpy(config.password, doc["password"], sizeof(config.password));
  archivo.close();
}

void writeLog(String mensaje){
  Serial.println(mensaje);
  File logFile;
  logFile = SD.open("datalog.txt", FILE_WRITE);
  if (logFile) { 
        logFile.print("Time(ms)=" + String(millis()) + ", error=");
        logFile.println(mensaje);
        logFile.close();
  } 
  else {
    Serial.println("Error guardando log");
  }
  return;
}

void connection(){
    sendData("AT+RST\r\n", 2000);      // resetear módulo
    String cadena = "AT+CWJAP=\"";
    cadena.concat(config.SSDI);
    cadena += "\",\"";
    cadena.concat(config.password);
    cadena += "\"\r\n";
    sendData(cadena, 8000); //SSID y contraseña para unirse a red
    sendData("AT+CWMODE=1\r\n", 2000); // configurar como cliente
    return;
}


void sendData(String comando, const int timeout){
   long int _time = millis() + timeout;
   long int _total = millis();
   respuesta = "";
   esp8266.print(comando);
   while(_time > _total){
       _total = millis();
       while(esp8266.available()){ 
             char c = esp8266.read(); 
             respuesta += c;   
       }
   } 
 writeLog(respuesta);
 return;
}

void sendRequest(int stopped, int walked, int runed){
  respuesta = "";
  String PeticionHTTP = "POST /api/state HTTP/1.1\r\nHost: 192.168.0.20\r\nContent-Type: application/json\r\nContent-Length: 28\r\n\r\n";
  long int _time = millis() + 1000; // medir el tiempo actual para verificar timeout
  PeticionHTTP.concat(addData(stopped, walked, runed));
  esp8266.print("AT+CIPSEND=" + String(PeticionHTTP.length()) + "\r\n"); // enviar el comando al ESP8266
  writeLog(PeticionHTTP);
  long int _total = millis();
  while(_time > _total){ //mientras no haya timeout
     _total = millis();
     while(esp8266.available()){ //mientras haya datos por leer
           if (esp8266.find('>')){break;}
           char c = esp8266.read(); 
           Serial.print(c);
           respuesta += c;     
     }
  } 
  esp8266.print(PeticionHTTP);
  _time = millis() + 1000;
  while(_time > _total){
     _total = millis();
     while(esp8266.available()){ 
           char c = esp8266.read(); 
           Serial.print(c);
           respuesta += c;     
     }
  }

 writeLog(respuesta);
 return;
}

String addData(int stopped, int walked, int runed){
  String datos = "[{token:\"";
  datos.concat(config.token);
  datos += "\",\"stop\":" + String(stopped)+ ",\"walk\":" + String(walked)+ ",\"run\":" + String(runed) +"}]\r\n\r\n";
  return datos;
}

void nuevosDatosPredecir(){
  
 if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
  
    for (int i = 0; i < 5; i = i + 1) { anteriores[i] = actuales[i];}
    float ax, ay, az;
    float gx, gy, gz;
    IMU.readAcceleration(ax, ay, az);
    IMU.readGyroscope(gx, gy, gz);
    actuales[0] = ax * conversor[0];
    actuales[1] = ay * conversor[0];
    actuales[2] = az * conversor[0];
    actuales[3] = gx * conversor[1];
    actuales[4] = gy * conversor[1];
    actuales[5] = gz * conversor[1];
    
    for (int i = 0; i < 5; i = i + 1) { 
      grupo_4[i] = grupo_3[i];
      grupo_3[i] = grupo_2[i];
      grupo_2[i] = grupo_1[i];
      grupo_1[i] = abs(actuales[i] - anteriores[i]);
      entrada[i] = ((grupo_1[i] + grupo_2[i] + grupo_3[i] + grupo_4[i]) / 4) / normalizador[i];
    }

 } else {
    return;
 }
 
}

void mostrarLuces(){
  if ( salida[0] != 0 ) { digitalWrite(LEDSTOP , HIGH); } else {digitalWrite(LEDSTOP , LOW);}  
  if ( salida[1] != 0 ) { digitalWrite(LEDWALK , HIGH); } else {digitalWrite(LEDWALK , LOW);} 
  if ( salida[2] != 0 ) { digitalWrite(LEDRUN , HIGH); } else {digitalWrite(LEDRUN , LOW);} 
}

void mandarDatos(){
    sendData("AT+CIPCLOSE\r\n", 1000);
    String iniciar_conexion = "AT+CIPSTART=\"TCP\",\"";
    iniciar_conexion.concat(config.hostname);
    iniciar_conexion += "\",";
    iniciar_conexion.concat(config.port);
    iniciar_conexion += "\r\n";
    sendData(iniciar_conexion, 1000);
    if(respuesta.indexOf(F("OK"))){ sendRequest(salida[0], salida[1], salida[1]); } else { Serial.println(respuesta);}
}


void setup()
{
    Serial.begin(9600);  // monitor serial del arduino
    if (!IMU.begin()) {Serial.println("¡Error al inicializar la IMU!"); }
    Wire.begin();
    esp8266.begin(9600);
    while (!SD.begin(9)) {
      Serial.println("Error iniciar SD, reintentando");
      delay(1000);
    }
    loadConfiguration(config); // Cargar configuracion
    connection();

    // Cargamos el modelo y comprobamos la copatibilidad de versiones
    tflModel = tflite::GetModel(model);

    if (tflModel->version() != TFLITE_SCHEMA_VERSION) {
      writeLog("Error en el esquema, no coinciden");
      while (1);
    }

    // Creamos e interpretamos el modelo
    tflInterpreter = new tflite::MicroInterpreter(tflModel, tflOpsResolver, tensorArena, tensorArenaSize, &tflErrorReporter);
    tflInterpreter->AllocateTensors();
    tflInputTensor = tflInterpreter->input(0);
    tflOutputTensor = tflInterpreter->output(0);


}

void loop() {
  
    respuesta.reserve(150);
    Serial.println("Capturando datos");
    nuevosDatosPredecir();
    Serial.println("Nueva prediccion");
    
    // Pasamos los datoa al modelo
    tflInputTensor->data.f[0] = actuales[0];
    tflInputTensor->data.f[1] = actuales[1];
    tflInputTensor->data.f[2] = actuales[2];
    tflInputTensor->data.f[3] = actuales[3];
    tflInputTensor->data.f[4] = actuales[4];
    tflInputTensor->data.f[5] = actuales[5];
    
    TfLiteStatus invokeStatus = tflInterpreter->Invoke();
    if (invokeStatus != kTfLiteOk) { writeLog("Invoke failed!"); }
    
    Serial.println("Obtenemos resultados");
    // Salida de la red
    for (int i = 0; i < 3; i++) {
      Serial.print(CLASSES[i]);
      Serial.print(" ");
      Serial.print(tflOutputTensor->data.f[i]);
      Serial.print(" %\n");
      salida_anterior[i] = salida[i];
      salida[i] = round(tflOutputTensor->data.f[i]);
    }
    mostrarLuces();
    delay(1000);
    if (salida_anterior[0] != salida[0] || salida_anterior[1] != salida[1] || salida_anterior[2] != salida[2]){ mandarDatos(); }
    
}
