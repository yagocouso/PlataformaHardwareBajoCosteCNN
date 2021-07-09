#include "I2Cdev.h"
#include "Wire.h"
#include <avr/pgmspace.h>
#include <Arduino_LSM9DS1.h> // Incluye la biblioteca para la IMU de 9 ejes

UART esp8266 (digitalPinToPinName(5), digitalPinToPinName(6), NC, NC);
const PROGMEM double conversor[]={2.0 * 9.81 / 32768.0, 250.0 / 32768.0}; // {accScale, gyroScale}
const PROGMEM float umbrales[] = {4.0, 3.5, 3.0}; // Umbrales de cargas, maximo, medio y minimo
String respuesta;
String cabeceras = "POST /api HTTP/1.1\r\nHost: 192.168.43.207\r\nContent-Type: application/json\r\nContent-Length: ";
String datos;

void setup()
{
    Serial.begin(9600);  // monitor serial del arduino
    if (!IMU.begin()) {Serial.println("¡Error al inicializar la IMU!"); }
    Wire.begin();
    esp8266.begin(9600); // baud rate del ESP8255
    sendData(F("AT+RST\r\n"),2000);      // resetear módulo
    sendData(F("AT+CWJAP=\"Xperia Z3 Compact_3746\",\"12345678\"\r\n"),8000); //SSID y contraseña para unirse a red
    sendData(F("AT+CWMODE=1\r\n"),1000); // configurar como cliente
}

void loop() {
    datos.reserve(350);
    respuesta.reserve(300);
    datos = "[";
    // addData();
    addData();
    sendData(F("AT+CIPCLOSE\r\n"), 350);
    sendData(F("AT+CIPSTART=\"TCP\",\"178.139.12.198\",8592\r\n"), 600);
    // addData();
    if(respuesta.indexOf(F("OK"))){
        addData();
        datos.remove(datos.length()-1, 1);
        datos = datos + "]\r\n\r\n";
        sendRequest();
    } else {
        Serial.println(respuesta);
    }
}

void sendData(String comando, const int timeout){
   long int time = millis();
   respuesta = "";
   esp8266.print(comando);
   while((time + timeout) > millis()){ 
       while(esp8266.available()){ 
             char c = esp8266.read(); 
             respuesta += c;   
       }
   } 
 Serial.print(respuesta);
 return;
}

void sendRequest(){
  respuesta = "";
  String PeticionHTTP = cabeceras + String(datos.length() - 4) + "\r\n\r\n";
  PeticionHTTP.concat(datos);
  long int time = millis(); // medir el tiempo actual para verificar timeout
  esp8266.print("AT+CIPSEND=" + String(PeticionHTTP.length()) + "\r\n"); // enviar el comando al ESP8266
  // Serial.println(PeticionHTTP);
  while((time + 800) > millis()){ //mientras no haya timeout
     while(esp8266.available()){ //mientras haya datos por leer
           if (esp8266.find(">")){break;}
           char c = esp8266.read(); 
           // Serial.print(c);
           respuesta += c;     
     }
  } 
  esp8266.print(PeticionHTTP);
  //esp8266.print(datos);
  while((time + 800) > millis()){ 
     while(esp8266.available()){ 
           char c = esp8266.read(); 
           //Serial.print(c);
           respuesta += c;     
     }
  }

 Serial.print(respuesta);
 return;
}

void addData(){
  float ax, ay, az;
  float gx, gy, gz;
  if (IMU.accelerationAvailable() && IMU.gyroscopeAvailable()) {
      IMU.readAcceleration(ax, ay, az);
      IMU.readGyroscope(gx, gy, gz);
      ax *= conversor[0];
      ay *= conversor[0];
      az *= conversor[0];
      gx *= conversor[1];
      gy *= conversor[1];
      gz *= conversor[1];
      datos = datos + "{\"t\":" + String(millis())+ ",\"x\":" + String(ax)+ ",\"y\":" + String(ay) + ",\"z\":" + String(az) + ",\"u\":" + String(gx) + ",\"v\":" + String(gy) + ",\"w\":" + String(gz)+"},";
  }

  return;
}
