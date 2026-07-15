import json
from django.core.management.base import BaseCommand
import paho.mqtt.client as mqtt
from telemetria.models import TelemetriaEdge


class Command(BaseCommand):
    help = "Inicia el Gateway Fog para escuchar MQTT y persistir en BD usando el ORM de Django"

    def handle(self, *args, **options):
        BROKER_IP = "localhost"
        BROKER_PORT = 1883
        TOPICO_WILDCARD = "ic3_grupo1/+/+/+"

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        " Gateway Fog conectado al Bróker Mosquitto local."
                    )
                )
                client.subscribe(TOPICO_WILDCARD)
                self.stdout.write(
                    f" Escuchando telemetría de toda la red en: {TOPICO_WILDCARD}"
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f" Error al conectar al bróker. Código: {rc}")
                )

        def on_message(client, userdata, msg):
            try:
                payload_str = msg.payload.decode("utf-8")
                partes_topico = msg.topic.split("/")

                if len(partes_topico) == 4:
                    tenant, mac, componente, variable = partes_topico

                    if variable == "telemetria":
                        datos = json.loads(payload_str)

                        registro = TelemetriaEdge.objects.create(
                            mac_dispositivo=mac,
                            componente=componente,
                            temperatura=datos.get("temp", 0.0),
                            humedad=datos.get("hum", 0.0),
                            limite_configurado=datos.get("limite", 28.0),
                            estado_rele=datos.get("rele", "OFF"),
                        )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f" [SQL INSERT OK] MAC: {mac} | Temp: {registro.temperatura}°C | Relé: {registro.estado_rele}"
                            )
                        )

            except json.JSONDecodeError:
                self.stdout.write(
                    self.style.WARNING(
                        f" Paquete ignorado (no es JSON válido): {msg.topic}"
                    )
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f" Error procesando el paquete de telemetría: {e}"
                    )
                )

        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message

        self.stdout.write(
            " Levantando servicio MQTT -> Base de Datos (Capa Fog)..."
        )

        try:
            client.connect(BROKER_IP, BROKER_PORT, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write("\n Servicio receptor detenido manualmente.")
            client.disconnect()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f" No se pudo conectar al bróker MQTT: {e}")
            )