import time
import random
import paho.mqtt.client as mqtt

BROKER_IP = "localhost" 
BROKER_PORT = 1883
TENANT = "ic3_grupo1"

DISPOSITIVOS_MOCK = [
    {"mac": "AA1122334455", "temp_actual": 24.0, "limite": 28.0},
    {"mac": "BB6677889900", "temp_actual": 20.0, "limite": 25.0},
    {"mac": "CC1122334455", "temp_actual": 29.0, "limite": 30.0}
]

client = mqtt.Client()

try:
    client.connect(BROKER_IP, BROKER_PORT, 60)
    print(" Mock de dispositivos Edge iniciado. Transmitiendo telemetría...")
    
    while True:
        for disp in DISPOSITIVOS_MOCK:
            mac = disp["mac"]
            variacion = random.uniform(-0.5, 0.5)
            disp["temp_actual"] += variacion
            rele = "ON (Auto)" if disp["temp_actual"] >= disp["limite"] else "OFF (Auto)"
            
            topico_pub = f"{TENANT}/{mac}/dht11/telemetria"
            payload = f'{{"temp": {disp["temp_actual"]:.2f}, "hum": {random.uniform(40.0, 60.0):.1f}, "limite": {disp["limite"]}, "rele": "{rele}"}}'
            
            client.publish(topico_pub, payload)
            print(f" [MOCK {mac}] -> {disp['temp_actual']:.2f}°C | Relé: {rele}")
            
        time.sleep(5)

except Exception as e:
    print(f" Error en el simulador: {e}")
except KeyboardInterrupt:
    print("\n Simulación detenida.")
    client.disconnect()