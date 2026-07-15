import streamlit as st
import pymysql
import pandas as pd
import paho.mqtt.publish as publish
import os
import datetime

# Configuración de la página
st.set_page_config(
    page_title="Dashboard IoT - IC3",
    page_icon="📡",
    layout="wide"
)

st.title(" Centro de Control IoT - Arquitectura Edge/Fog")
st.markdown("---")

DB_HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
DB_USER = os.environ.get("MYSQL_USER", "berni")
DB_PASS = os.environ.get("MYSQL_PASSWORD", "password_segura")
DB_NAME = os.environ.get("MYSQL_DATABASE", "ic3_telemetria_db")
BROKER_HOST = os.environ.get("MQTT_HOST", "127.0.0.1")

@st.cache_data(ttl=3)
def obtener_datos():
    try:
        conexion = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            port=3306
        )
        query = "SELECT mac_dispositivo, temperatura, humedad, limite_configurado, estado_rele, timestamp FROM telemetria_telemetriaedge ORDER BY timestamp DESC LIMIT 500;"
        df = pd.read_sql(query, conexion)
        conexion.close()
        return df
    except Exception as e:
        st.error(f" Error conectando a MySQL: {e}")
        return pd.DataFrame()

df = obtener_datos()

if df.empty:
    st.warning(" No hay datos de telemetría en la base de datos todavía. Encendé la ESP32 o el Mock.")
else:
    macs_disponibles = df["mac_dispositivo"].unique()
    mac_seleccionada = st.sidebar.selectbox("🔍 Seleccionar Dispositivo (MAC):", macs_disponibles)

    if st.sidebar.button(" Actualizar Datos"):
        st.cache_data.clear()
        st.rerun()

    df_dispositivo = df[df["mac_dispositivo"] == mac_seleccionada]
    ultima_lectura = df_dispositivo.iloc[0]

    # --- WATCHDOG: CÁLCULO DE ESTADO DE CONEXIÓN ---
    # Convertimos el timestamp de la BD y quitamos zona horaria para comparar limpio
    tiempo_ultima_lectura = pd.to_datetime(ultima_lectura['timestamp']).tz_localize(None)
    tiempo_actual = datetime.datetime.now()
    segundos_silencio = (tiempo_actual - tiempo_ultima_lectura).total_seconds()

    # Si pasaron menos de 15 segundos, asumimos que el nodo está online
    if segundos_silencio <= 15:
        st.success(f" **ESTADO: CONECTADO (ONLINE)** | Último paquete recibido hace **{int(segundos_silencio)} seg**.")
    else:
        st.error(f" **ESTADO: DESCONECTADO (OFFLINE)** | Sin señal hace **{int(segundos_silencio)} seg** (Revisar alimentación o conexión WiFi del nodo).")
    # -----------------------------------------------

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(" Temperatura", f"{ultima_lectura['temperatura']:.1f} °C")
    with col2:
        st.metric(" Humedad", f"{ultima_lectura['humedad']:.1f} %")
    with col3:
        st.metric(" Límite Actual", f"{ultima_lectura['limite_configurado']} °C")
    with col4:
        estado_rele = ultima_lectura["estado_rele"]
        color = "🟢" if "ON" in estado_rele else "🔴"
        st.metric("💡 Estado Relé", f"{color} {estado_rele}")

    st.markdown("---")

    st.subheader(f" Historial temporal - Dispositivo: {mac_seleccionada}")
    df_grafico = df_dispositivo.sort_values("timestamp")
    df_grafico = df_grafico.set_index("timestamp")[["temperatura", "humedad", "limite_configurado"]]
    st.line_chart(df_grafico)

    st.markdown("---")

    st.subheader(" Control Remoto del Nodo Edge")
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        nuevo_limite = st.slider(
            "Seleccionar nuevo límite de temperatura:",
            min_value=15.0,
            max_value=35.0,
            value=float(ultima_lectura['limite_configurado']),
            step=0.5
        )
    with col_ctrl2:
        st.write("")
        st.write("") 
        if st.button(" Enviar Nuevo Límite al ESP32", use_container_width=True):
            topico_control = f"ic3_grupo1/{mac_seleccionada}/control/limite"
            payload = str(nuevo_limite)
            try:
                publish.single(topico_control, payload, hostname=BROKER_HOST, port=1883)
                st.success(f" ¡Orden enviada! Tópico: `{topico_control}` -> Valor: `{payload}`")
                st.cache_data.clear()
            except Exception as e:
                st.error(f" Error enviando MQTT: {e}")