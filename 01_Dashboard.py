"""
pages/01_Dashboard.py
 
Dashboard-Seite der CatchYourFlight Streamlit-App.
Zeigt drei interaktive Diagramme mit Verspätungsstatistiken
für die 5 grössten US-Flughäfen basierend auf BTS-Daten 2015:
  1. Verspätungsrate nach Tageszeit (Liniendiagramm)
  2. Verspätungsrate nach Wochentag (Balkendiagramm)
  3. Verspätungsrate nach Airline (horizontales Balkendiagramm)
 
Abhängigkeiten:
  - utils/navbar.py           (eigene Navbar-Komponente)
  - utils/dashboard_data.py   (Datenaggregation aus CSV/Datenquelle)
 
Autoren: Stefanie Seiler, Ben Marbacher
Datum:   Mai 2026
 
Quellen:
- CS-Unterricht: Grundkonzepte Python (Funktionen, if/elif/else,
  for-Schleifen, f-Strings, Listen, List Comprehension),
  pandas DataFrame-Grundlagen
- Claude (Sonnet 4): gesamte Plotly-Diagramm-Konfiguration (go.Figure,
  go.Scatter, go.Bar, update_layout, Farbwahl), Streamlit-seitenspezifische
  Konfiguration (set_page_config, st.markdown CSS-Injection),
  Datei-Architektur und Struktur der Dashboard-Seite
"""
 
# ── Imports ───────────────────────────────────────────────────────────────────
# 01_Dashboard.py
import streamlit as st                          # Streamlit: Webanwendungs-Framework
import plotly.graph_objects as go               # Plotly: interaktive Diagramme
                                                # Quelle: Claude – Plotly nicht im Unterricht
from utils.navbar import show_navbar            # Eigene Navbar-Komponente (projektintern)
from utils.dashboard_data import (              # Aggregationsfunktionen für Diagrammdaten
    get_delay_by_hour,
    get_delay_by_weekday,
    get_delay_by_airline,
)
 
# ── Seitenkonfiguration ───────────────────────────────────────────────────────
# Streamlit-Seiteneinstellungen: Titel, Icon, Layout und Sidebar-Zustand
# Quelle: Claude – st.set_page_config() und Parameter nicht im Unterricht
st.set_page_config(
    page_title="Dashboard – CatchYourFlight",   # Titel im Browser-Tab
    page_icon="✈",                              # Favicon im Browser-Tab
    layout="wide",                              # Breites Layout (volle Seitenbreite)
    initial_sidebar_state="collapsed",          # Sidebar beim Laden eingeklappt
)
 
# Sidebar und Einklapp-Button per CSS komplett ausblenden
# unsafe_allow_html=True erlaubt das Einbetten von rohem HTML/CSS in Streamlit
# Quelle: Claude – CSS-Injection via st.markdown und data-testid-Selektoren via Claude
st.markdown("<style>[data-testid='stSidebar'],[data-testid='collapsedControl']{display:none!important}</style>", unsafe_allow_html=True)
 
# ── Navbar anzeigen ───────────────────────────────────────────────────────────
# Eigene Navigationsleiste aus utils/navbar.py einbinden
show_navbar()
 
# ── Titel ─────────────────────────────────────────────────────────────────────
st.title("Dashboard")                           # Seitentitel (H1)
st.markdown("Delay statistics for the 5 busiest US airports (ATL · ORD · JFK · LAX · DEN) — 2015 data.")
st.markdown("---")                              # Horizontale Trennlinie
 
# ── Daten laden ───────────────────────────────────────────────────────────────
# Aggregierte Verspätungsstatistiken aus utils/dashboard_data.py laden
# Jede Funktion gibt einen pandas DataFrame zurück
df_hour    = get_delay_by_hour()                # DataFrame: Verspätungsrate pro Stunde
df_weekday = get_delay_by_weekday()             # DataFrame: Verspätungsrate pro Wochentag
df_airline = get_delay_by_airline()             # DataFrame: Verspätungsrate pro Airline
 
# Gemeinsame Farbkonstanten für alle drei Charts (Hex-Farbcodes)
# Quelle: Claude – Farbwahl und Hex-Codes via Claude
COLOR_LINE = "#3B82F6"   # Blau für Linien
COLOR_BAR  = "#6366F1"   # Lila für Balken
COLOR_GRID = "#f0f0f0"   # Hellgrau für Gitternetz
 
# ── CHART 1: VERSPÄTUNGEN NACH TAGESZEIT (Liniendiagramm) ─────────────────────
st.subheader("Delays by Time of Day")
st.caption("On average delays accumulate over the course of the day.")
 
# Stundenbeschriftungen für X-Achse erzeugen: [0, 1, ..., 23] → ["00:00", "01:00", ...]
# f-String mit :02d sorgt für führende Null (z.B. "06:00"); Konzept f-String aus Unterricht
hour_labels = [f"{h:02d}:00" for h in df_hour["hour"]]
 
# Leeres Plotly-Figure-Objekt erstellen
# Quelle: Claude – go.Figure() und Plotly-API vollständig via Claude
fig_hour = go.Figure()
 
# Linien-Trace mit gefülltem Bereich unter der Kurve hinzufügen
fig_hour.add_trace(go.Scatter(
    x=hour_labels,                              # X-Achse: Stunden-Labels
    y=df_hour["delay_pct"],                     # Y-Achse: Verspätungsrate in %
    mode="lines",                               # Nur Linie, keine Punkte
    line=dict(color=COLOR_LINE, width=2.5, shape="spline"),  # Glatte Kurve (spline)
    fill="tozeroy",                             # Fläche bis zur X-Achse füllen
    fillcolor="rgba(59,130,246,0.12)",          # Sehr helles Blau als Füllung (12% Deckkraft)
    name="Delay rate",
))
 
# Layout des Liniendiagramms konfigurieren (Grösse, Hintergrund, Achsen)
# Quelle: Claude – update_layout()-Parameter vollständig via Claude
fig_hour.update_layout(
    height=320,                                 # Diagrammhöhe in Pixeln
    margin=dict(l=0, r=0, t=10, b=0),          # Innenabstand: links/rechts/oben/unten
    plot_bgcolor="#ffffff",                     # Weisser Diagramm-Hintergrund
    paper_bgcolor="#ffffff",                    # Weisser Seiten-Hintergrund
    xaxis=dict(
        title="Departure Hour",
        tickangle=0,                            # Achsenbeschriftung nicht gedreht
        gridcolor=COLOR_GRID,
        showline=True,
        linecolor="#e5e7eb",
        # Nur jede zweite Stunde beschriften damit es nicht zu voll wird
        tickvals=hour_labels[::2],              # Slicing [::2]: jedes zweite Element
        ticktext=hour_labels[::2],
    ),
    yaxis=dict(
        title="% Flights Delayed",
        gridcolor=COLOR_GRID,
        ticksuffix="%",                         # Prozentzeichen hinter Y-Achsen-Werten
        range=[0, 45],                          # Y-Achse von 0 bis 45 %
    ),
    showlegend=False,                           # Legende ausblenden
)
 
# Fertig konfiguriertes Diagramm in Streamlit anzeigen (volle Containerbreite)
st.plotly_chart(fig_hour, use_container_width=True)
 
st.markdown("---")
 
# ── CHART 2: VERSPÄTUNGEN NACH WOCHENTAG (Balkendiagramm) ─────────────────────
st.subheader("Delays by Day of Week")
st.caption("Friday usually is the day with the biggest cumulated delay.")
 
# Farbliste für Balken: Freitag rot (#EF4444), alle anderen lila (COLOR_BAR)
# List Comprehension mit bedingtem Ausdruck (ternärer if) — Konzept aus Unterricht
bar_colors_weekday = [
    "#EF4444" if day == "Fri" else COLOR_BAR
    for day in df_weekday["day"]
]
 
# Leeres Plotly-Figure-Objekt für Balkendiagramm erstellen
fig_weekday = go.Figure()
 
fig_weekday.add_trace(go.Bar(
    x=df_weekday["day"],                        # X-Achse: Wochentag-Kürzel (Mon, Tue, ...)
    y=df_weekday["delay_pct"],                  # Y-Achse: Verspätungsrate in %
    marker_color=bar_colors_weekday,            # Freitag rot, Rest lila
    marker_line_width=0,                        # Kein Rahmen um die Balken
    text=[f"{v}%" for v in df_weekday["delay_pct"]],  # Prozentangabe auf dem Balken
    textposition="outside",                     # Beschriftung über dem Balken
    textfont=dict(size=12, color="#333333"),     # Schriftgrösse und -farbe der Beschriftung
))
 
# Layout des Balkendiagramms konfigurieren
fig_weekday.update_layout(
    height=320,
    margin=dict(l=0, r=0, t=30, b=0),
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    xaxis=dict(
        title="Day of Week",
        gridcolor=COLOR_GRID,
        showline=True,
        linecolor="#e5e7eb",
    ),
    yaxis=dict(
        title="% Flights Delayed",
        gridcolor=COLOR_GRID,
        ticksuffix="%",
        range=[0, 30],                          # Y-Achse von 0 bis 30 %
    ),
    showlegend=False,
    bargap=0.35,                                # Abstand zwischen den Balken (35%)
)
 
st.plotly_chart(fig_weekday, use_container_width=True)
 
st.markdown("---")
 
# ── CHART 3: VERSPÄTUNGEN NACH AIRLINE (horizontales Balkendiagramm) ──────────
st.subheader("Delays by Airline")
st.caption("Sorted from most to least punctual - Hawaiian Airlines has the lowest delay rate of all airlines.")
 
# Hilfsfunktion: gibt Farbe basierend auf Verspätungsrate zurück
# Grün / Gelb / Rot als Ampelsystem — Konzept if/elif/else aus Unterricht
# Schwellenwerte und Hex-Farbcodes via Claude
def airline_color(pct: float) -> str:
    """Gibt eine Farbe abhängig von der Verspätungsrate zurück."""
    if pct < 16:   return "#10B981"   # Grün: unter 16% = sehr pünktlich
    elif pct < 22: return "#F59E0B"   # Gelb: 16–22% = durchschnittlich
    else:          return "#EF4444"   # Rot: über 22% = viele Verspätungen
 
# Farbliste für alle Airlines erstellen via List Comprehension + airline_color()
bar_colors_airline = [airline_color(p) for p in df_airline["delay_pct"]]
 
# Leeres Plotly-Figure-Objekt für horizontales Balkendiagramm erstellen
fig_airline = go.Figure()
 
fig_airline.add_trace(go.Bar(
    x=df_airline["delay_pct"],                  # X-Achse: Verspätungsrate in %
    y=df_airline["airline"],                    # Y-Achse: Airline-Namen
    orientation="h",                            # Horizontal ausrichten (h = horizontal)
    marker_color=bar_colors_airline,            # Ampelfarben je nach Rate
    marker_line_width=0,                        # Kein Rahmen um die Balken
    text=[f"{v}%" for v in df_airline["delay_pct"]],  # Prozent rechts vom Balken
    textposition="outside",                     # Beschriftung ausserhalb des Balkens
    textfont=dict(size=11, color="#333333"),
))
 
# Layout des horizontalen Balkendiagramms konfigurieren
fig_airline.update_layout(
    height=420,                                 # Höher, da mehr Einträge (10 Airlines)
    margin=dict(l=0, r=60, t=10, b=0),         # Rechts mehr Platz für Beschriftungen
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    xaxis=dict(
        title="% Flights Delayed",
        gridcolor=COLOR_GRID,
        ticksuffix="%",
        range=[0, 34],                          # X-Achse von 0 bis 34 %
    ),
    yaxis=dict(
        title="",                               # Kein Achsentitel (Airline-Namen genügen)
        gridcolor=COLOR_GRID,
        automargin=True,                        # Automatisch Platz für lange Airline-Namen
    ),
    showlegend=False,
    bargap=0.25,                                # Abstand zwischen den Balken (25%)
)
 
st.plotly_chart(fig_airline, use_container_width=True)
 
# ── Fussnote ──────────────────────────────────────────────────────────────────
st.markdown("---")
# Datenquelle als Fussnote angeben
st.caption("Source: Bureau of Transportation Statistics (BTS) · 2015 US Domestic Flights · Airports: ATL, ORD, JFK, LAX, DEN")
