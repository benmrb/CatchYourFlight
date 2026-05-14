"""
01_Dashboard.py
 
Startseite der CatchYourFlight Streamlit-App.
Zeigt ein Hero-Bild, eine Projektbeschreibung, Use Cases sowie
drei interaktive Verspätungs-Diagramme (nach Tageszeit, Wochentag
und Airline) basierend auf BTS-Flugdaten 2015.
 
Abhängigkeiten:
  - hero.png                  (Hintergrundbild im Stammverzeichnis)
  - utils/navbar.py           (globale Navigationsleiste)
  - utils/dashboard_data.py   (aggregierte Verspätungsstatistiken)
 
Autoren: Sára Jankovičová, Stefanie Seiler, Benjamin Marbacher
Datum:   Mai 2026
 
Quellen:
- CS-Unterricht: Grundkonzepte Python (Funktionen, if/elif/else,
  for-Schleifen, f-Strings, List Comprehension), pandas DataFrame-
  Grundlagen
- Claude (Sonnet 4): gesamtes CSS-Styling via st.markdown
  (Hero-Overlay, Dialog-Styling, Button-Styling), Base64-Hero-
  Einbettung via base64/pathlib, Plotly-Diagramm-Konfiguration
  (go.Figure, go.Scatter, go.Bar, update_layout), st.dialog-
  Decorator, HTML-Struktur für Hero/Problem Statement/Use Cases,
  gesamte Datei-Architektur
"""
 
# ── Imports ───────────────────────────────────────────────────────────────────
# Streamlit-Bibliothek importieren (Web-App-Framework)
import streamlit as st
import plotly.graph_objects as go               # Interaktive Diagramme
                                                # Quelle: Claude – Plotly nicht im Unterricht
 
# Gemeinsame Navbar-Funktion importieren
from utils.navbar import show_navbar
 
# Aggregierte Delay-Daten für die Charts importieren
from utils.dashboard_data import get_delay_by_hour, get_delay_by_weekday, get_delay_by_airline
 
# ── Seitenkonfiguration ───────────────────────────────────────────────────────
# Setzt Titel, Icon, Layout und Sidebar-Status der App
# Quelle: Claude – st.set_page_config() und Parameter nicht im Unterricht
st.set_page_config(
    page_title="CatchYourFlight – USA",
    page_icon="✈",
    layout="wide",
    initial_sidebar_state="collapsed",
)
 
# ── Navbar anzeigen ───────────────────────────────────────────────────────────
# Zeigt die Navigationsleiste
show_navbar()
 
# ── CSS-Ausnahme: Hero-Text weiß ─────────────────────────────────────────────
# Überschreibt die globale Schwarz-Regel speziell für den Hero-Bereich
# und definiert Dialog- sowie Button-Styling
# Quelle: Claude – gesamtes CSS vollständig via Claude
st.markdown("""
<style>
.hero-text h1, .hero-text p, .hero-text div, .hero-text span {
    color: #ffffff !important;
}
.hero-text .hero-label {
    color: #ffffff !important;
}
 
/* Dialog-Fenster: weißer Hintergrund, schwarze Schrift */
[data-testid="stDialog"] > div,
[data-testid="stDialog"] [role="dialog"] {
    background-color: #ffffff !important;
}
[data-testid="stDialog"] [role="dialog"] *,
[data-testid="stDialog"] p,
[data-testid="stDialog"] h1,
[data-testid="stDialog"] h2,
[data-testid="stDialog"] h3,
[data-testid="stDialog"] li,
[data-testid="stDialog"] label,
[data-testid="stDialog"] span,
[data-testid="stDialog"] div {
    color: #111111 !important;
    background-color: transparent !important;
}
/* Input-Felder und Dropdowns im Dialog */
[data-testid="stDialog"] input,
[data-testid="stDialog"] textarea,
[data-testid="stDialog"] select,
[data-testid="stDialog"] [data-baseweb="select"] *,
[data-testid="stDialog"] [data-baseweb="input"] *,
[data-testid="stDialog"] [data-testid="stSelectbox"] *,
[data-testid="stDialog"] [data-testid="stTextInput"] * {
    background-color: #f9fafb !important;
    color: #111111 !important;
    border-color: #d1d5db !important;
}
/* Dropdown-Liste */
[data-baseweb="popover"] *,
[data-baseweb="menu"] * {
    background-color: #ffffff !important;
    color: #111111 !important;
}
 
/* Buttons: weißer Hintergrund, schwarze Schrift, grauer Rahmen */
[data-testid="stButton"] button {
    background-color: #ffffff !important;
    color: #111111 !important;
    border: 1px solid #d1d5db !important;
    font-weight: 600 !important;
}
[data-testid="stButton"] button:hover {
    background-color: #f3f4f6 !important;
    border-color: #9ca3af !important;
}
</style>
""", unsafe_allow_html=True)
 
# ── Hero-Sektion mit Hintergrundbild ─────────────────────────────────────────
# Zeigt ein Flugzeug-Bild über die volle Breite ohne Rahmen
# Bild wird als Base64-String inline eingebettet (kein externer Link nötig)
# Quelle: Claude – base64/pathlib-Einbettung und HTML-Hero-Struktur via Claude
import base64, pathlib
_hero_b64 = base64.b64encode(pathlib.Path("hero.png").read_bytes()).decode()
_hero_src = f"data:image/png;base64,{_hero_b64}"
 
# Hero-Block: Hintergrundbild + dunkler Overlay + weisser Text darüber
# Quelle: Claude – CSS position:absolute / z-index / linear-gradient via Claude
st.markdown(f"""
<div style="
    position: relative;
    overflow: hidden;
    margin: -1rem -4rem 2.5rem -4rem;
    height: 340px;
">
    <!-- Hintergrundbild -->
    <img
        src="{_hero_src}"
        style="
            position: absolute; top: 0; left: 0;
            width: 100%; height: 100%;
            object-fit: cover;
            object-position: center 40%;
        "
    />
    <!-- Dunkler Overlay -->
    <div style="
        position: absolute; top: 0; left: 0;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, rgba(5,10,30,0.45) 40%, rgba(5,10,30,0.1) 100%);
    "></div>
    <!-- Text darüber -->
    <div class="hero-text" style="
        position: relative; z-index: 2;
        padding: 3rem 3rem;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        color: #ffffff;
    ">
        <div class="hero-label" style="font-size:0.7rem; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.75rem;">
            ATL · BOS · DEN · DFW · DTW · EWR · IAH · JFK · LAS · LAX · MCO · MSP · ORD · PHX · SEA · SFO
        </div>
        <h1 style="font-size:3rem; font-weight:700; color:#ffffff; margin:0 0 0.75rem; line-height:1.1; letter-spacing:-0.02em;">
            CatchYourFlight
        </h1>
        <p style="color:#ffffff; font-size:1rem; margin:0 0 1.5rem; max-width:480px; line-height:1.6;">
            Analyze delay patterns from the 16 busiest US airports — by airline, departure time and airports.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)
 
# ── Problem Statement ─────────────────────────────────────────────────────────
# Zeigt den Projektzweck als kursives Zitat mit blauem linken Rand
# Quelle: Claude – HTML/CSS-Karten-Layout via Claude
st.markdown("""
<div style="
    background: #f8f9fa;
    border-left: 3px solid #3B82F6;
    padding: 1rem 1.25rem;
    margin-bottom: 2rem;
    color: #333333;
    font-size: 0.95rem;
    line-height: 1.7;
    border-radius: 0 8px 8px 0;
">
    <em>When planning a trip everybody crosses the issue of planning the right amount of buffer time at the airport. CatchYourFlight solves this problem by estimating the delay probability for your specific flight from the 16 busiest US airports by deriving historical delay patterns.</em>
</div>
""", unsafe_allow_html=True)
 
# ── Use Cases ─────────────────────────────────────────────────────────────────
# Listet drei konkrete Anwendungsfälle für das Tool auf
# Quelle: Claude – HTML/CSS-Karten-Layout via Claude
st.markdown("""
<div style="
    background: #f8f9fa;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 2rem;
">
    <div style="font-size:0.7rem; color:#888888; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:0.75rem;">
        Why this tool?
    </div>
    <div style="color:#333333; font-size:0.9rem; line-height:2.1;">
        ✈ &nbsp; The Monday morning flight is often delayed — consider booking on a Saturday instead.<br>
        ✈ &nbsp; Got a connecting flight? Check the risk and plan enough buffer time.<br>
        ✈ &nbsp; Which airline is the most reliable on your route?
    </div>
</div>
""", unsafe_allow_html=True)
 
 
# ── About Us & Stay Informed ──────────────────────────────────────────────────
# Zwei klickbare Buttons zentriert, öffnen jeweils ein Modal-Fenster
 
# @st.dialog definiert ein modales Popup-Fenster
# Quelle: Claude – @st.dialog-Decorator nicht im Unterricht behandelt
@st.dialog("About Us")
def show_about():
    # Informationen über das Projektteam und das Projekt
    st.markdown("""
    **CatchYourFlight** is a student project developed at the University of St. Gallen.
 
    Our goal is to help travelers make smarter booking decisions by deriving historical flight delay data from the 16 busiest US airports.
 
    ---
    **Team**
    - Data Research · Nils Wälti
    - Machine Learning · Benjamin Marbacher & Silas Marty
    - Meteo API · Stefanie Seiler
    - Website Design · Sára Jankovičová
 
    ---
    **Data Sources & APIs**
 
    - Flight data: 2.54M flights from 16 US airports (ATL, BOS, DEN, DFW, DTW, EWR, IAH, JFK, LAS, LAX, MCO, MSP, ORD, PHX, SEA, SFO) — Bureau of Transportation Statistics (BTS) 2015, via Kaggle
    - Weather data: Open-Meteo API (historical archive & forecast)
    - Boarding pass scanning: Anthropic Claude API
 
    ---
    **Model Accuracy**
 
    - Binary Classification (XGBoost): 67.0% accuracy
    - Multiclass Classification (XGBoost): 80.4% accuracy
    """)
 
 
# ── DELAY CHARTS ─────────────────────────────────────────────────────────────
# Drei interaktive Diagramme basierend auf 2015 BTS-Flugdaten
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div style='border-top:1px solid #e0e0e0; margin-bottom:2rem;'></div>", unsafe_allow_html=True)
 
# Daten aus dashboard_data.py laden (je ein DataFrame pro Diagramm)
df_hour    = get_delay_by_hour()
df_weekday = get_delay_by_weekday()
df_airline = get_delay_by_airline()
 
# Gemeinsame Farb- und Stil-Konstanten für alle drei Charts
# Quelle: Claude – Farbwahl und LAYOUT_BASE-Struktur via Claude
COLOR_LINE = "#3B82F6"   # Blau für Linien
COLOR_BAR  = "#6366F1"   # Lila für Balken
COLOR_GRID = "#f0f0f0"   # Hellgrau für Gitternetz
LAYOUT_BASE = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(family="sans-serif", size=12, color="#333333"),
)
 
# ── Chart 1: Verspätungen nach Tageszeit ──────────────────────────────────────
st.subheader("Delays by Time of Day")
st.caption("Late night flights around 02:00 show a surprising delay spike — caused by delays carried over from the previous day.")
 
# Stundenbeschriftungen für die X-Achse: [0, ..., 23] → ["00:00", ..., "23:00"]
hour_labels = [f"{h:02d}:00" for h in df_hour["hour"]]
 
# Leeres Plotly-Figure-Objekt erstellen
# Quelle: Claude – go.Figure() und gesamte Plotly-Konfiguration via Claude
fig_hour = go.Figure()
 
# Gefüllte Fläche unter der Kurve für bessere Lesbarkeit
fig_hour.add_trace(go.Scatter(
    x=hour_labels,
    y=df_hour["delay_pct"],
    mode="lines",                               # Nur Linie, keine Punkte
    line=dict(color=COLOR_LINE, width=2.5, shape="spline"),  # Glatte Kurve
    fill="tozeroy",                             # Fläche bis X-Achse füllen
    fillcolor="rgba(59,130,246,0.12)",          # Sehr helles Blau als Füllung
    hovertemplate="%{x}: %{y}%<extra></extra>", # Tooltip-Format beim Hovern
))
fig_hour.update_layout(
    **LAYOUT_BASE,                              # Gemeinsame Basis-Einstellungen entpacken
    height=300,
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(
        title="Departure Hour",
        gridcolor=COLOR_GRID,
        tickvals=hour_labels[::2],              # Slicing [::2]: nur jede zweite Stunde
        ticktext=hour_labels[::2],
    ),
    yaxis=dict(title="% Flights Delayed", gridcolor=COLOR_GRID, ticksuffix="%", range=[0, 45]),
    showlegend=False,
)
st.plotly_chart(fig_hour, use_container_width=True)
 
st.markdown("---")
 
# ── Chart 2: Verspätungen nach Wochentag ──────────────────────────────────────
st.subheader("Delays by Day of Week")
st.caption("Monday usually is the day with the highest probability of delay.")
 
# Montag rot hervorheben, alle anderen lila
# List Comprehension mit bedingtem Ausdruck — Konzept aus Unterricht
bar_colors_weekday = ["#EF4444" if d == "Mon" else COLOR_BAR for d in df_weekday["day"]]
 
fig_weekday = go.Figure()
fig_weekday.add_trace(go.Bar(
    x=df_weekday["day"],                        # X-Achse: Wochentag-Kürzel
    y=df_weekday["delay_pct"],                  # Y-Achse: Verspätungsrate in %
    marker_color=bar_colors_weekday,            # Montag rot, Rest lila
    marker_line_width=0,                        # Kein Rahmen um Balken
    text=[f"{v}%" for v in df_weekday["delay_pct"]],   # Beschriftung auf Balken
    textposition="outside",                     # Beschriftung über dem Balken
    hovertemplate="%{x}: %{y}%<extra></extra>",
))
fig_weekday.update_layout(
    **LAYOUT_BASE,
    height=300,
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(title="Day of Week", gridcolor=COLOR_GRID),
    yaxis=dict(title="% Flights Delayed", gridcolor=COLOR_GRID, ticksuffix="%", range=[0, 30]),
    showlegend=False,
    bargap=0.35,                                # Abstand zwischen Balken
)
st.plotly_chart(fig_weekday, use_container_width=True)
 
st.markdown("---")
 
# ── Chart 3: Verspätungen nach Airline ────────────────────────────────────────
st.subheader("Delays by Airline")
st.caption("Hawaiian Airlines is your best choice when searching for a flight with statistically low delay probability!")
 
# Hilfsfunktion: Ampelfarbe je nach Verspätungsrate
# if/elif/else-Konzept aus Unterricht; Schwellenwerte via Claude
def airline_color(pct):
    if pct < 16:   return "#10B981"   # Grün: sehr pünktlich
    elif pct < 22: return "#F59E0B"   # Gelb: durchschnittlich
    else:          return "#EF4444"   # Rot: viele Verspätungen
 
fig_airline = go.Figure()
fig_airline.add_trace(go.Bar(
    x=df_airline["delay_pct"],                  # X-Achse: Verspätungsrate in %
    y=df_airline["airline"],                    # Y-Achse: Airline-Namen
    orientation="h",                            # Horizontal ausrichten
    marker_color=[airline_color(p) for p in df_airline["delay_pct"]],  # Ampelfarben
    marker_line_width=0,
    text=[f"{v}%" for v in df_airline["delay_pct"]],
    textposition="outside",
    hovertemplate="%{y}: %{x}%<extra></extra>",
))
fig_airline.update_layout(
    **LAYOUT_BASE,
    height=420,
    margin=dict(l=0, r=50, t=30, b=0),
    xaxis=dict(title="% Flights Delayed", gridcolor=COLOR_GRID, ticksuffix="%", range=[0, 34]),
    yaxis=dict(title="", gridcolor=COLOR_GRID, automargin=True),
    showlegend=False,
    bargap=0.25,
)
st.plotly_chart(fig_airline, use_container_width=True)
 
# ── Footer ────────────────────────────────────────────────────────────────────
# Zeigt Projektinfo zentriert am Seitenende
st.markdown("<br>", unsafe_allow_html=True)
 
# ── About Us & Stay Informed Buttons ─────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
# Button mittig platzieren (Spalten-Verhältnis 3:1:3)
_, btn_col, _ = st.columns([3, 1, 3])
 
with btn_col:
    # Button öffnet show_about()-Dialog bei Klick
    if st.button("About Us", use_container_width=True):
        show_about()
 
# Footer-Zeile mit Projektinformation
# Quelle: Claude – HTML-Footer-Styling via Claude
st.markdown("""
<div style="border-top:1px solid #e0e0e0; padding-top:1rem; text-align:center;
    color:#aaaaaa; font-size:0.72rem;">
    Computer Science Project · University of St. Gallen · CatchYourFlight · 2026
</div>
""", unsafe_allow_html=True)
