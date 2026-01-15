import streamlit as st
import requests
import time
import random

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sniper Bet AI", page_icon="🎯", layout="centered")

# --- CREDENCIALES ---
API_KEY = "03fb7a2b70e5d6f841eaa05514f9a85b" # Tu clave original
TELEGRAM_TOKEN = "8348791562:AAE5pT2nySIlGT7Qc6h0ScAe-A_W59AlJ_Y"
TELEGRAM_CHAT_ID = "-1003303594959"

# --- URLs ---
URL_LIVE = "https://v3.football.api-sports.io/fixtures?live=all"
URL_STATS = "https://v3.football.api-sports.io/fixtures/statistics?fixture="

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# --- BARRA LATERAL ---
st.sidebar.title("Configuración")
modo_demo = st.sidebar.checkbox("🛠️ Modo Simulación / Demo", value=False)

# --- FUNCION TELEGRAM CORREGIDA (MÉTODO NAVEGADOR) ---
def enviar_a_telegram(mensaje):
    # Usamos la misma técnica que usaste en el navegador (GET)
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    params = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
        # Quitamos 'parse_mode' por ahora para evitar errores de formato
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return True, "Enviado"
        else:
            return False, response.text # Devolvemos el error real de Telegram
    except Exception as e:
        return False, str(e)

# --- FUNCIONES MATEMÁTICAS ---
def obtener_stat(lista, tipo):
    for item in lista:
        if item['type'] == tipo:
            val = item['value']
            return int(val) if val is not None else 0
    return 0

def analizar_experto(local, visita, stats_l, stats_v, goles_l, goles_v, minuto):
    badges = []
    
    tiros_arco_l = obtener_stat(stats_l, "Shots on Goal")
    tiros_fuera_l = obtener_stat(stats_l, "Shots off Goal")
    corners_l = obtener_stat(stats_l, "Corner Kicks")
    rojas_l = obtener_stat(stats_l, "Red Cards")
    ataques_peligrosos_l = obtener_stat(stats_l, "Dangerous Attacks")
    
    tiros_arco_v = obtener_stat(stats_v, "Shots on Goal")
    tiros_fuera_v = obtener_stat(stats_v, "Shots off Goal")
    corners_v = obtener_stat(stats_v, "Corner Kicks")
    rojas_v = obtener_stat(stats_v, "Red Cards")
    ataques_peligrosos_v = obtener_stat(stats_v, "Dangerous Attacks")

    # Cálculo de Presión
    if ataques_peligrosos_l > 0 or ataques_peligrosos_v > 0:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2) + (ataques_peligrosos_l * 0.5)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2) + (ataques_peligrosos_v * 0.5)
    else:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2)

    if rojas_l > 0: badges.append(f"🟥 {local} CON ROJA (10 Jugadores)")
    if rojas_v > 0: badges.append(f"🟥 {visita} CON ROJA (10 Jugadores)")

    diff = presion_l - presion_v
    best_pick = "" 

    if abs(diff) > 20:
        if diff > 0 and rojas_l == 0:
            badges.append(f"🔥 DOMINIO TOTAL DE {local}")
            best_pick = f"Gana {local} o Gol {local}"
        elif diff < 0 and rojas_v == 0:
            badges.append(f"🔥 DOMINIO TOTAL DE {visita}")
            best_pick = f"Gana {visita} o Gol {visita}"
            
    return badges, presion_l, presion_v, best_pick

# --- DATOS DEMO ---
def generar_demo():
    return [{
        "fixture": {"id": 12345, "status": {"elapsed": 80}},
        "teams": {"home": {"name": "Liverpool"}, "away": {"name": "Fulham"}},
        "goals": {"home": 0, "away": 0},
        "demo_stats_l": [{"type": "Shots on Goal", "value": 12}, {"type": "Corner Kicks", "value": 9}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 70}, {"type": "Shots off Goal", "value": 5}],
        "demo_stats_v": [{"type": "Shots on Goal", "value": 1}, {"type": "Corner Kicks", "value": 1}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 10}, {"type": "Shots off Goal", "value": 0}]
    }]

# --- INTERFAZ ---
st.title("🎯 Panel de Control: Tipster IA")

if st.button("🔎 ESCANEAR MERCADO"):
    
    usar_api = not modo_demo
    candidatos = []

    if usar_api:
        st.info("Conectando...")
        try:
            response = requests.get(URL_LIVE, headers=headers)
            data = response.json()
            if "errors" in data and data["errors"]:
                st.warning("⚠️ Límite API. Usando Demo.")
                usar_api = False
            else:
                for p in data['response']:
                    if p['fixture']['status']['elapsed'] and p['fixture']['status']['elapsed'] >= 45:
                        candidatos.append(p)
        except:
            usar_api = False

    if not usar_api:
        candidatos = generar_demo()
        st.warning("🧪 Usando Demo")

    contador = 0
    for match in candidatos:
        if contador >= 3: break
        
        id_p = match['fixture']['id']
        local = match['teams']['home']['name']
        visita = match['teams']['away']['name']
        goles = f"{match['goals']['home']}-{match['goals']['away']}"
        minuto = match['fixture']['status']['elapsed']
        
        if usar_api:
            try:
                r = requests.get(URL_STATS + str(id_p), headers=headers).json()
                if not r['response']: continue
                stats_l = r['response'][0]['statistics']
                stats_v = r['response'][1]['statistics']
                contador += 1
            except: continue
        else:
            stats_l = match['demo_stats_l']
            stats_v = match['demo_stats_v']

        badges, p_l, p_v, pick = analizar_experto(local, visita, stats_l, stats_v, match['goals']['home'], match['goals']['away'], minuto)

        with st.container():
            st.markdown("---")
            c1, c2 = st.columns([3, 1])
            with c1:
                st.subheader(f"{local} vs {visita}")
                st.write(f"Min {minuto} | {goles}")
                st.progress(p_l / (p_l + p_v + 1))
                for b in badges: st.info(b)
            
            with c2:
                if pick:
                    st.write("---")
                    if st.button("📢 Enviar", key=f"btn_{id_p}"):
                        # Mensaje simple SIN MARCADOS RAROS para asegurar envío
                        msg = (f"🚨 ALERTA SNIPER AI 🚨\n"
                               f"{local} vs {visita}\n"
                               f"Minuto: {minuto}\n"
                               f"Analisis: Presion {int(p_l)} vs {int(p_v)}\n"
                               f"PICK: {pick}")
                        
                        exito, error_msg = enviar_a_telegram(msg)
                        
                        if exito:
                            st.success("✅ ¡Enviado!")
                        else:
                            st.error(f"Error: {error_msg}")
