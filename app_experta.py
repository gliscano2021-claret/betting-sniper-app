import streamlit as st
import requests
import time
import random

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Sniper Bet AI", page_icon="🎯", layout="centered")

# --- CREDENCIALES ---
# 1. API DE FUTBOL (Tu clave original)
API_KEY = "03fb7a2b70e5d6f841eaa05514f9a85b"

# 2. TELEGRAM (Tus datos configurados)
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
modo_demo = st.sidebar.checkbox("🛠️ Modo Simulación / Demo", value=False, help="Activa esto para probar el botón de Telegram sin gastar API.")

# --- FUNCIONES DE TELEGRAM ---
def enviar_a_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error Telegram: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error conexión Telegram: {e}")
        return False

# --- FUNCIONES MATEMÁTICAS ---
def obtener_stat(lista, tipo):
    for item in lista:
        if item['type'] == tipo:
            val = item['value']
            return int(val) if val is not None else 0
    return 0

def analizar_experto(local, visita, stats_l, stats_v, goles_l, goles_v, minuto):
    badges = []
    
    # 1. Extraer Datos
    tiros_arco_l = obtener_stat(stats_l, "Shots on Goal")
    tiros_fuera_l = obtener_stat(stats_l, "Shots off Goal")
    total_tiros_l = tiros_arco_l + tiros_fuera_l
    corners_l = obtener_stat(stats_l, "Corner Kicks")
    rojas_l = obtener_stat(stats_l, "Red Cards")
    ataques_peligrosos_l = obtener_stat(stats_l, "Dangerous Attacks")
    
    tiros_arco_v = obtener_stat(stats_v, "Shots on Goal")
    tiros_fuera_v = obtener_stat(stats_v, "Shots off Goal")
    total_tiros_v = tiros_arco_v + tiros_fuera_v
    corners_v = obtener_stat(stats_v, "Corner Kicks")
    rojas_v = obtener_stat(stats_v, "Red Cards")
    ataques_peligrosos_v = obtener_stat(stats_v, "Dangerous Attacks")

    # 2. Calcular Presión
    if ataques_peligrosos_l > 0 or ataques_peligrosos_v > 0:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2) + (ataques_peligrosos_l * 0.5)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2) + (ataques_peligrosos_v * 0.5)
    else:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2)

    # 3. Lógica de Rojas
    if rojas_l > 0: badges.append(f"🟥 **{local} CON ROJA** (10 Jugadores)")
    if rojas_v > 0: badges.append(f"🟥 **{visita} CON ROJA** (10 Jugadores)")

    # 4. Lógica de Puntería (Sniper)
    if total_tiros_l > 5:
        precision_l = (tiros_arco_l / total_tiros_l) * 100
        if precision_l < 30: badges.append(f"🔫 **{local} Descalibrado:** Puntería baja ({int(precision_l)}%)")
    
    if total_tiros_v > 5:
        precision_v = (tiros_arco_v / total_tiros_v) * 100
        if precision_v < 30: badges.append(f"🔫 **{visita} Descalibrado:** Puntería baja ({int(precision_v)}%)")

    # 5. Lógica de Dominio y Picks
    diff = presion_l - presion_v
    alerta_valida = True
    
    if diff > 20 and rojas_l > 0: alerta_valida = False
    if diff < -20 and rojas_v > 0: alerta_valida = False

    best_pick = "" 

    if alerta_valida:
        if diff > 25:
            msg = f"🔥 **DOMINIO TOTAL DE {local}**"
            badges.append(msg)
            best_pick = f"Gana {local} o Próximo Gol {local}"
        elif diff < -25:
            msg = f"🔥 **DOMINIO TOTAL DE {visita}**"
            badges.append(msg)
            best_pick = f"Gana {visita} o Próximo Gol {visita}"
        elif abs(diff) < 10 and (tiros_arco_l + tiros_arco_v) > 12:
            msg = "⚡ **PARTIDO ROTO (Ida y Vuelta)**"
            badges.append(msg)
            best_pick = "Más de 0.5 Goles (Over)"

    return badges, presion_l, presion_v, best_pick

# --- GENERADOR DE DATOS DE PRUEBA (DEMO) ---
def generar_demo():
    return [
        {
            "fixture": {"id": 9991, "status": {"elapsed": 78}},
            "teams": {"home": {"name": "Liverpool"}, "away": {"name": "Fulham"}},
            "goals": {"home": 1, "away": 1},
            "demo_stats_l": [{"type": "Shots on Goal", "value": 15}, {"type": "Corner Kicks", "value": 10}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 85}, {"type": "Shots off Goal", "value": 5}],
            "demo_stats_v": [{"type": "Shots on Goal", "value": 2}, {"type": "Corner Kicks", "value": 1}, {"type": "Red Cards", "value": 0}, {"type": "Dangerous Attacks", "value": 15}, {"type": "Shots off Goal", "value": 1}]
        }
    ]

# --- INTERFAZ PRINCIPAL ---

st.title("🎯 Panel de Control: Tipster IA")
st.markdown("Escáner de Value Bets con integración a Telegram VIP.")

if st.button("🔎 ESCANEAR MERCADO EN VIVO"):
    
    candidatos = []
    usar_api = not modo_demo

    # 1. OBTENCIÓN DE DATOS
    if usar_api:
        status_text = st.empty()
        status_text.info("📡 Conectando con satélites...")
        try:
            response = requests.get(URL_LIVE, headers=headers)
            data = response.json()
            
            # DETECCIÓN DE ERRORES (LÍMITE ALCANZADO)
            if "errors" in data and data["errors"]:
                errores = data["errors"]
                # A veces el error viene como lista o diccionario
                st.warning(f"⚠️ Aviso de API: {errores}")
                st.warning("🔄 Cambiando automáticamente a MODO DEMO para que puedas seguir trabajando.")
                usar_api = False
            else:
                partidos = data['response']
                for p in partidos:
                    minuto = p['fixture']['status']['elapsed']
                    if minuto is None: continue
                    if minuto >= 45 and abs(p['goals']['home'] - p['goals']['away']) <= 1:
                        candidatos.append(p)
                status_text.success(f"✅ {len(candidatos)} partidos analizados.")
        except Exception as e:
            st.error(f"Error de conexión: {e}")
            usar_api = False

    # 2. SI ES MODO DEMO (Por error de API o manual)
    if not usar_api:
        candidatos = generar_demo()
        st.warning("🧪 MODO DEMO ACTIVADO: Usando datos simulados.")

    # 3. PROCESAMIENTO Y VISUALIZACIÓN
    contador = 0
    if not candidatos and usar_api:
        st.info("No se encontraron partidos interesantes (Min 45+ y cerrados) en este momento.")

    for match in candidatos:
        if contador >= 5: break # Límite de seguridad
        
        id_p = match['fixture']['id']
        local = match['teams']['home']['name']
        visita = match['teams']['away']['name']
        goles_l = match['goals']['home']
        goles_v = match['goals']['away']
        minuto = match['fixture']['status']['elapsed']
        
        # Obtener Stats
        if usar_api:
            res_stats = requests.get(URL_STATS + str(id_p), headers=headers)
            d_stats = res_stats.json()
            if not d_stats['response']: continue
            stats_l = d_stats['response'][0]['statistics']
            stats_v = d_stats['response'][1]['statistics']
            contador += 1
        else:
            stats_l = match['demo_stats_l']
            stats_v = match['demo_stats_v']
            
        # ANÁLISIS IA
        badges, p_l, p_v, pick_sugerido = analizar_experto(local, visita, stats_l, stats_v, goles_l, goles_v, minuto)
        
        # RENDERIZADO DE TARJETA
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.subheader(f"{local} vs {visita}")
                st.write(f"⏱ **{minuto}'** | ⚽ **{goles_l}-{goles_v}**")
                
                # Barra de Presión
                total = p_l + p_v + 1
                st.progress(p_l / total)
                st.caption(f"Presión: {local} ({int(p_l)}) - {visita} ({int(p_v)})")
                
                # Badges
                if badges:
                    for b in badges:
                        if "🔥" in b: st.success(b)
                        elif "🟥" in b: st.error(b)
                        elif "⚡" in b: st.info(b)
                        else: st.warning(b)
            
            with col2:
                # BOTÓN DE TELEGRAM (Solo aparece si hay una sugerencia clara)
                if pick_sugerido:
                    st.write("---")
                    # Usamos una key única con el ID del partido
                    if st.button(f"📢 Enviar al VIP", key=f"btn_{id_p}"):
                        
                        # CONSTRUCCIÓN DEL MENSAJE VIP
                        mensaje_vip = (
                            f"🚨 **ALERTA SNIPER AI DETECTADA** 🚨\n\n"
                            f"⚽ *{local} vs {visita}*\n"
                            f"⏱ Minuto: {minuto}'\n"
                            f"📊 Marcador: {goles_l} - {goles_v}\n\n"
                            f"🧠 **Análisis:**\n"
                            f"El algoritmo detecta una presión abrumadora de {local if p_l > p_v else visita} ({int(p_l)} vs {int(p_v)} pts).\n\n"
                            f"💡 **PICK SUGERIDO:** {pick_sugerido}\n\n"
                            f"📉 *Entrar con responsabilidad.*\n"
                            f"🤖 _Powered by SniperBet AI_"
                        )
                        
                        exito = enviar_a_telegram(mensaje_vip)
                        if exito:
                            st.toast("✅ ¡Enviado al Canal!", icon="🚀")
                        else:
                            st.error("Revisa el Token de Telegram.")
                else:
                    st.write("\n\nWait...")
