# Proyecto IC3 - Implementación de Capa Fog, Telemetría y Control Bidireccional

Este repositorio contiene la extensión de arquitectura de red e infraestructura desarrollada para cumplir con los requerimientos de la materia **IC3 (Ingenieria en Computación)**. 

Sobre la base de adquisición de datos en el nodo Edge utilizado en IC2 (ESP32 + DHT11 + Relé), se implementó todo el ecosistema superior de comunicación, ingesta, persistencia relacional, control remoto y visualización en tiempo real sobre una **Raspberry Pi 5** contenerizada con Docker.

---

## Módulos Agregados para IC3

### 1. Capa Fog y Gateway MQTT (`/backend_django`)
* **Ingesta por Comodines (Wildcards):** Implementación de un servicio demonio en segundo plano (`iniciar_receptor_mqtt.py`) usando **Paho-MQTT** que escucha al bróker Mosquitto bajo el patrón `ic3_grupo1/+/+/+` para capturar la telemetría de cualquier nodo conectado a la red.
* **Persistencia Relacional:** Modelado de base de datos relacional utilizando el **ORM de Django** para almacenar de forma estructurada las variables de estado (temperatura, humedad, límite configurado y estado de actuadores) en un motor **MySQL 8.0**.

### 2. Capa de Presentación e Interfaz Web (`/frontend_streamlit`)
* **Dashboard Interactivo (Streamlit):** Aplicación web para el monitoreo de KPIs en vivo y trazado de curvas históricas de temperatura y humedad mediante *Pandas* y *Chart.js*.
* **Watchdog de Conectividad (Perro Guardián):** Algoritmo por software que monitorea el `timestamp` del último paquete recibido en la base de datos por cada MAC. Si un dispositivo deja de transmitir por más de 15 segundos, la interfaz alerta en tiempo real su estado como **DESCONECTADO (OFFLINE)**.
* **Control Remoto Bidireccional:** Panel de control web para modificar el límite de alarma de temperatura de los nodos en tiempo real. Al enviar una orden, el backend dispara una publicación MQTT (`/control/limite`) que impacta y reconfigura instantáneamente la lógica y el display LCD del microcontrolador físico.

### 3. Simulación y Concurrencia (`/mock`)
* **Emulador IoT (`mock.py`):** Script de pruebas diseñado para generar tráfico MQTT concurrente simulando múltiples placas ESP32 con diferentes direcciones MAC (`AA11...`, `BB66...`, `CC11...`) transmitiendo telemetría en paralelo, validando la capacidad de la base de datos y la interfaz a régimen industrial.

### 4. DevOps e Infraestructura (`Docker & ARM`)
* **Contenerización Multi-Servicio:** Orquestación completa mediante `docker-compose.yml` que compila y enlaza tres contenedores aislados (`ic3_mysql`, `ic3_django`, `ic3_streamlit`) optimizados para arquitectura ARM.

---
