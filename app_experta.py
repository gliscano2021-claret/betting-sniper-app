import streamlit as st
import requests
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sniper Bet AI", page_icon="🎯", layout="centered")

# --- CREDENCIALES (YA VERIFICADAS) ---
API_KEY = "03fb7a2b70e5d6f841eaa05514f9a85b"
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

# --- FUNCIÓN TELEGRAM BLINDADA (MÉTODO POST) ---
def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Payload = El paquete de datos sellado
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown" # Permite negritas
    }
    
    try:
        # Usamos POST en lugar de GET para mensajes largos
        response = requests.post(url, json=payload)
        
        if response.status_code == 200:
            return True, "Enviado"
        else:
            return False, response.text
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

    # Presión
    if ataques_peligrosos_l > 0 or ataques_peligrosos_v > 0:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2) + (ataques_peligrosos_l * 0.5)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2) + (ataques_peligrosos_v * 0.5)
    else:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2)

    if rojas_l > 0: badges.append(f"🟥 {local} CON ROJA")
    if rojas_v > 0: badges.append(f"🟥 {visita} CON ROJA")

    diff = presion_l - presion_v
    best_pick = "" 

    # Lógica de Alertas
    if abs(diff) > 20:
        if diff > 0 and rojas_l == 0:
            badges.append(f"🔥 DOMINIO TOTAL DE {local}")
            best_pick = f"Gana {local} o Gol {local}"
        elif diff < 0 and rojas_v == 0:
            badges.append(f"🔥 DOMINIO TOTAL DE {visita}")
            best_pick = f"Gana {visita} o Gol {visita}"
            
    return badges, presion_l, presion_v, best_pick

# --- DATOS DEMO (Diseñados para activar la alerta SÍ o SÍ) ---
def generar_demo():
    return [{
        "fixture": {"id": 12345, "status": {"elapsed": 80}},
        "teams": {"home": {"name": "Liverpool"}, "away": {"name": "Fulham"}},
        "goals": {"home": 0, "away": 0},
        # Liverpool con stats aplastantes para forzar la alerta
        "demo_stats_l": [{"type": "Shots on Goal", "value": 15}, {"type": "Corner Kicks", "value": 12}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 90}, {"type": "Shots off Goal", "value": 5}],
        "demo_stats_v": [{"type": "Shots on Goal", "value": 1}, {"type": "Corner Kicks", "value": 0}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 5}, {"type": "Shots off Goal", "value": 0}]
    }]

# --- INTERFAZ ---
st.title("🎯 Panel de Control: Tipster IA")

if st.button("🔎 ESCANEAR MERCADO"):
    
    usar_api = not modo_demo
    candidatos = []

    # 1. Intentar API
    if usar_api:
        st.info("Conectando satélites...")
        try:
            response = requests.get(URL_LIVE, headers=headers)
            data = response.json()
            if "errors" in data and data["errors"]:
                st.warning("⚠️ API Agotada. Usando Demo.")
                usar_api = False
            else:
                for p in data['response']:
                    if p['fixture']['status']['elapsed'] and p['fixture']['status']['elapsed'] >= 45:
                        candidatos.append(p)
        except:
            usar_api = False

    # 2. Usar Demo si falló API o si el usuario quiso
    if not usar_api:
        candidatos = generar_demo()
        st.warning("🧪 Usando Demo (Liverpool vs Fulham)")

    # 3. Mostrar Resultados
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
                total = p_l + p_v + 1
                st.progress(p_l / total)
                st.caption(f"Presión: {int(p_l)} vs {int(p_v)}")
                for b in badges: st.info(b)
            
            with c2:
                # El botón solo aparece si hay un PICK claro
                if pick:
                    st.write("---")
                    # Usamos una clave única
                    if st.button("📢 ENVIAR", key=f"btn_{id_p}"):
                        
                        # Mensaje Formateado para Telegram
                        msg = (
                            f"🚨 *ALERTA SNIPER AI DETECTADA*\n\n"
                            f"⚽ {local} vs {visita}\n"
                            f"⏱ Minuto: {minuto}'\n"
                            f"📊 Marcador: {goles}\n\n"
                            f"📈 *Análisis de Presión:*\n"
                            f"{local}: {int(p_l)} pts\n"
                            f"{visita}: {int(p_v)} pts\n\n"
                            f"💡 *PICK RECOMENDADO:* {pick}\n\n"
                            f"🤖 _Generado por Inteligencia Artificial_"
                        )
                        
                        exito, error_msg = enviar_a_telegram(msg)
                        
                        if exito:
                            st.success("✅ ¡ENVIADO!")
                            st.balloons() # ¡Celebración visual!
                        else:
                            st.error(f"Error: {error_msg}")
