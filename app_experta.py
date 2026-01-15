import streamlit as st
import requests
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sniper Bet AI", page_icon="🎯", layout="centered")

# --- CREDENCIALES (YA COMPROBADAS EN DIAGNÓSTICO) ---
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

# --- FUNCIÓN TELEGRAM (MODO TEXTO PLANO - SIN FALLOS) ---
def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # ELIMINAMOS 'parse_mode' PARA EVITAR ERRORES DE FORMATO
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje
    }
    
    try:
        response = requests.post(url, json=payload)
        
        # DEBUG: Imprimir resultado en consola de Streamlit (invisible al usuario pero útil)
        print(f"Status Telegram: {response.status_code}")
        
        if response.status_code == 200:
            return True, "Enviado correctamente"
        else:
            # Devolvemos el error exacto que da Telegram
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

    # Presión simplificada para el ejemplo
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

    # Forzamos alerta si la diferencia es grande
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

if st.button("🔎 ESCANEAR MERCADO"):
    
    usar_api = not modo_demo
    candidatos = []

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
                        candidatos.append(p)
        except:
            usar_api = False

    if not usar_api:
        candidatos = generar_demo()
        st.warning("🧪 MODO DEMO ACTIVADO (Liverpool vs Fulham)")

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
                # BOTÓN DE ENVÍO
                if pick:
                    st.write("---")
                    # Clave única para el botón
                    if st.button("📢 ENVIAR", key=f"btn_{id_p}"):
                        
                        st.info("⏳ Enviando a Telegram...")
                        
                        # MENSAJE EN TEXTO PLANO (Sin asteriscos ni guiones bajos)
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
                            st.success("✅ ¡ENVIADO CORRECTAMENTE!")
                            st.balloons()
                        else:
                            # SI FALLA, AQUÍ VERÁS POR QUÉ
                            st.error(f"❌ FALLÓ EL ENVÍO: {respuesta}")
