import streamlit as st
import requests

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sniper Bet AI", page_icon="🎯", layout="centered")

API_KEY = "03fb7a2b70e5d6f841eaa05514f9a85b"  # Tu clave
URL_LIVE = "https://v3.football.api-sports.io/fixtures?live=all"
URL_STATS = "https://v3.football.api-sports.io/fixtures/statistics?fixture="

headers = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

# --- TÍTULO ---
st.title("🎯 Sniper Bet AI: Precisión Quirúrgica")
st.markdown("Algoritmo de detección de valor, tarjetas rojas y eficiencia de ataque.")

# --- FUNCIONES EXPERTAS ---

def obtener_stat(lista, tipo):
    for item in lista:
        if item['type'] == tipo:
            val = item['value']
            return int(val) if val is not None else 0
    return 0

def analizar_experto(local, visita, stats_l, stats_v, goles_l, goles_v, minuto):
    badges = []
    
    # 1. EXTRACCIÓN DE DATOS
    tiros_arco_l = obtener_stat(stats_l, "Shots on Goal")
    tiros_fuera_l = obtener_stat(stats_l, "Shots off Goal")
    total_tiros_l = tiros_arco_l + tiros_fuera_l
    corners_l = obtener_stat(stats_l, "Corner Kicks")
    rojas_l = obtener_stat(stats_l, "Red Cards") # <--- NUEVO
    ataques_peligrosos_l = obtener_stat(stats_l, "Dangerous Attacks") # <--- NUEVO
    
    tiros_arco_v = obtener_stat(stats_v, "Shots on Goal")
    tiros_fuera_v = obtener_stat(stats_v, "Shots off Goal")
    total_tiros_v = tiros_arco_v + tiros_fuera_v
    corners_v = obtener_stat(stats_v, "Corner Kicks")
    rojas_v = obtener_stat(stats_v, "Red Cards") # <--- NUEVO
    ataques_peligrosos_v = obtener_stat(stats_v, "Dangerous Attacks") # <--- NUEVO

    # 2. CÁLCULO DE PRESIÓN REFINADO
    # Si hay datos de "Ataques Peligrosos", los usamos. Si no, usamos la fórmula clásica.
    if ataques_peligrosos_l > 0 or ataques_peligrosos_v > 0:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2) + (ataques_peligrosos_l * 0.5)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2) + (ataques_peligrosos_v * 0.5)
    else:
        presion_l = (tiros_arco_l * 4) + (corners_l * 2)
        presion_v = (tiros_arco_v * 4) + (corners_v * 2)

    # 3. LÓGICA DE TARJETAS ROJAS (CRUCIAL)
    if rojas_l > 0:
        badges.append(f"🟥 **{local} TIENE ROJA:** Juega con {11-rojas_l}. La presión puede ser engañosa.")
    if rojas_v > 0:
        badges.append(f"🟥 **{visita} TIENE ROJA:** Juega con {11-rojas_v}. Oportunidad para el rival.")

    # 4. EFICIENCIA Y PUNTERÍA (SNIPER)
    # Si un equipo dispara mucho pero todo fuera
    if total_tiros_l > 5:
        precision_l = (tiros_arco_l / total_tiros_l) * 100
        if precision_l < 30:
            badges.append(f"🔫 **{local} Descalibrado:** Muchos tiros pero mala puntería ({int(precision_l)}%). Cuidado.")
    
    if total_tiros_v > 5:
        precision_v = (tiros_arco_v / total_tiros_v) * 100
        if precision_v < 30:
            badges.append(f"🔫 **{visita} Descalibrado:** Muchos tiros pero mala puntería ({int(precision_v)}%). Cuidado.")

    # 5. DETECCIÓN DE DOMINIO
    diff = presion_l - presion_v
    
    # Ajuste: Si el equipo que domina tiene Roja, anulamos la alerta de dominio
    alerta_valida = True
    if diff > 20 and rojas_l > 0: alerta_valida = False
    if diff < -20 and rojas_v > 0: alerta_valida = False

    if alerta_valida:
        if diff > 25:
            badges.append(f"🔥 **DOMINIO TOTAL DE {local}:** Índice de presión abrumador. El gol debería caer.")
        elif diff < -25:
            badges.append(f"🔥 **DOMINIO TOTAL DE {visita}:** Índice de presión abrumador. El gol debería caer.")

    return badges, presion_l, presion_v

# --- INTERFAZ ---

if st.button("🔎 RASTREAR OPORTUNIDADES PRECISAS"):
    st.info("Conectando con estadios... Filtrando ruido...")
    
    try:
        response = requests.get(URL_LIVE, headers=headers)
        data = response.json()
        
        if "errors" in data and data["errors"]:
            st.error(f"Error API: {data['errors']}")
        else:
            partidos = data['response']
            candidatos = []
            
            # FILTRO: Partidos avanzados (45+) y cerrados
            for p in partidos:
                minuto = p['fixture']['status']['elapsed']
                if minuto is None: continue
                if minuto >= 45 and abs(p['goals']['home'] - p['goals']['away']) <= 1:
                    candidatos.append(p)
            
            st.success(f"✅ Analizando a fondo {len(candidatos)} partidos candidatos.")
            
            contador = 0
            for match in candidatos:
                if contador >= 5: break
                
                id_p = match['fixture']['id']
                local = match['teams']['home']['name']
                visita = match['teams']['away']['name']
                goles_l = match['goals']['home']
                goles_v = match['goals']['away']
                minuto = match['fixture']['status']['elapsed']
                
                # Stats
                res_stats = requests.get(URL_STATS + str(id_p), headers=headers)
                d_stats = res_stats.json()
                
                if not d_stats['response']: continue
                contador += 1
                
                stats_l = d_stats['response'][0]['statistics']
                stats_v = d_stats['response'][1]['statistics']
                
                # CEREBRO EXPERTO
                badges, p_l, p_v = analizar_experto(local, visita, stats_l, stats_v, goles_l, goles_v, minuto)
                
                # SOLO MOSTRAR SI HAY ALGO QUE DECIR
                if badges:
                    with st.container():
                        st.markdown("---")
                        col1, col2, col3 = st.columns([3, 1, 3])
                        col1.subheader(f"{local}")
                        col2.markdown(f"<h2 style='text-align: center;'>{goles_l}-{goles_v}</h2>", unsafe_allow_html=True)
                        col2.caption(f"Min {minuto}")
                        col3.subheader(f"{visita}")
                        
                        # Barra Presión
                        total = p_l + p_v + 1
                        st.progress(p_l / total)
                        
                        # MOSTRAR INSIGHTS
                        for b in badges:
                            if "🟥" in b:
                                st.error(b) # Roja = Error grave
                            elif "🔥" in b:
                                st.success(b) # Fuego = Oportunidad buena
                            elif "🔫" in b:
                                st.warning(b) # Pistola = Advertencia
                            else:
                                st.info(b)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.write("Pulsa el botón para buscar Value Bets.")