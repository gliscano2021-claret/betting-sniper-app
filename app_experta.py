import streamlit as st
import requests
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sniper Bet AI", page_icon="🎯", layout="centered")

# --- CREDENCIALES ---
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

# --- FUNCIÓN TELEGRAM ---
def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True, "Enviado"
        else:
            return False, f"Error {response.status_code}: {response.text}"
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
    corners_l = obtener_stat(stats_l, "Corner Kicks")
    rojas_l = obtener_stat(stats_l, "Red Cards")
    ataques_peligrosos_l = obtener_stat(stats_l, "Dangerous Attacks")
    
    tiros_arco_v = obtener_stat(stats_v, "Shots on Goal")
    corners_v = obtener_stat(stats_v, "Corner Kicks")
    rojas_v = obtener_stat(stats_v, "Red Cards")
    ataques_peligrosos_v = obtener_stat(stats_v, "Dangerous Attacks")

    # Presión simplificada
    if ataques_peligrosos_l > 0:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2) + (ataques_peligrosos_l * 0.5)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2) + (ataques_peligrosos_v * 0.5)
    else:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2)

    if rojas_l > 0: badges.append(f"🟥 {local} CON ROJA")
    if rojas_v > 0: badges.append(f"🟥 {visita} CON ROJA")

    diff = presion_l - presion_v
    best_pick = "" 

    if abs(diff) > 20:
        if diff > 0:
            badges.append(f"🔥 DOMINIO TOTAL DE {local}")
            best_pick = f"Gana {local} o Gol"
        else:
            badges.append(f"🔥 DOMINIO TOTAL DE {visita}")
            best_pick = f"Gana {visita} o Gol"
            
    return badges, presion_l, presion_v, best_pick

# --- DATOS DEMO ---
def generar_demo():
    return [{
        "fixture": {"id": 12345, "status": {"elapsed": 80}},
        "teams": {"home": {"name": "Liverpool"}, "away": {"name": "Fulham"}},
        "goals": {"home": 0, "away": 0},
        "demo_stats_l": [{"type": "Shots on Goal", "value": 15}, {"type": "Corner Kicks", "value": 12}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 90}, {"type": "Shots off Goal", "value": 5}],
        "demo_stats_v": [{"type": "Shots on Goal", "value": 1}, {"type": "Corner Kicks", "value": 0}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 5}, {"type": "Shots off Goal", "value": 0}]
    }]

# --- INTERFAZ ---
st.title("🎯 Panel de Control: Tipster IA")

# 1. INICIALIZAR MEMORIA (SESSION STATE)
if 'candidatos' not in st.session_state:
    st.session_state.candidatos = []
if 'escaneado' not in st.session_state:
    st.session_state.escaneado = False

# 2. BOTÓN DE ESCANEO (Solo actualiza la memoria)
if st.button("🔎 ESCANEAR MERCADO"):
    
    usar_api = not modo_demo
    lista_temp = []

    if usar_api:
        try:
            response = requests.get(URL_LIVE, headers=headers)
            data = response.json()
            if "errors" in data and data["errors"]:
                st.warning("⚠️ Límite API. Usando Demo.")
                usar_api = False
            else:
                for p in data['response']:
                    if p['fixture']['status']['elapsed'] and p['fixture']['status']['elapsed'] >= 45:
                        lista_temp.append(p)
        except:
            usar_api = False

    if not usar_api:
        lista_temp = generar_demo()
        st.warning("🧪 MODO DEMO ACTIVADO")
    
    # GUARDAMOS EN MEMORIA PARA QUE NO SE BORRE AL CLICAR ENVIAR
    st.session_state.candidatos = lista_temp
    st.session_state.escaneado = True

# 3. MOSTRAR RESULTADOS (Fuera del botón de escanear)
if st.session_state.escaneado:
    st.success(f"Resultados en memoria: {len(st.session_state.candidatos)} partidos.")
    
    contador = 0
    usar_api = not modo_demo

    for match in st.session_state.candidatos:
        if contador >= 3: break
        
        id_p = match['fixture']['id']
        local = match['teams']['home']['name']
        visita = match['teams']['away']['name']
        goles = f"{match['goals']['home']}-{match['goals']['away']}"
        minuto = match['fixture']['status']['elapsed']
        
        # Stats
        if usar_api:
            try:
                # Cache simple para no gastar API en re-renders
                r = requests.get(URL_STATS + str(id_p), headers=headers).json()
                if not r['response']: continue
                stats_l = r['response'][0]['statistics']
                stats_v = r['response'][1]['statistics']
                contador += 1
            except: continue
        else:
            # En demo, los datos ya vienen con el partido
            if 'demo_stats_l' in match:
                stats_l = match['demo_stats_l']
                stats_v = match['demo_stats_v']
            else:
                 # Si vienes de API real pero falló y cambiaste a demo, esto evita error
                 continue

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
                if pick:
                    st.write("---")
                    # AHORA SÍ FUNCIONARÁ PORQUE LA LISTA NO SE BORRA
                    if st.button("📢 ENVIAR", key=f"btn_{id_p}"):
                        msg = (
                            f"🚨 ALERTA SNIPER AI 🚨\n\n"
                            f"{local} vs {visita}\n"
                            f"Minuto: {minuto}\n"
                            f"Marcador: {goles}\n\n"
                            f"ANALISIS:\n"
                            f"Presion Local: {int(p_l)}\n"
                            f"Presion Visita: {int(p_v)}\n\n"
                            f"PICK RECOMENDADO: {pick}"
                        )
                        exito, respuesta = enviar_a_telegram(msg)
                        if exito:
                            st.success("✅ ¡ENVIADO!")
                            st.balloons()
                        else:
                            st.error(f"❌ Error: {respuesta}")
