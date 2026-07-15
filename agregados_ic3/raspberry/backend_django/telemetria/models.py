from django.db import models


class TelemetriaEdge(models.Model):
    mac_dispositivo = models.CharField(max_length=17, db_index=True)
    componente = models.CharField(max_length=50, default="dht11")
    temperatura = models.FloatField()
    humedad = models.FloatField()
    limite_configurado = models.FloatField()
    estado_rele = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Telemetría Edge"
        verbose_name_plural = "Telemetrías Edge"

    def __str__(self):
        return f"[{self.mac_dispositivo}] Temp: {self.temperatura}°C - {self.timestamp.strftime('%H:%M:%S')}"