"""
pages/03_Prediction.py
 
ML-Vorhersage-Seite der CatchYourFlight Streamlit-App.
Ermöglicht die Eingabe von Flugdetails (Flughafen, Airline, Datum,
Abflugstunde) und berechnet mittels trainiertem ML-Modell die
Verspätungswahrscheinlichkeit inkl. Wetterdaten und Einflussfaktoren.
Boarding Pass Upload als Alternative zu manueller Eingabe.
 
Abhängigkeiten:
  - utils/navbar.py       (eigene Navigationsleiste)
  - utils/weather.py      (Wetterdaten-Abruf via Open-Meteo API)
  - model/predict.py      (ML-Vorhersagefunktionen)
  - Anthropic Claude API  (Boarding Pass OCR/Scan)
 
Autoren: Silas Marty, Ben Marbach
Datum:   Mai 2026
 
Quellen:
- CS-Unterricht: Grundkonzepte Python (Funktionen, if/elif/else,
  for-Schleifen, f-Strings, Dictionaries, Listen, List Comprehension),
  pandas DataFrame-Operationen, Boolean Masking, Supervised Learning /
  Klassifikation (ML-Grundkonzepte)
- Claude (Sonnet 4): st.session_state-Konzept, gesamte CSS-Injection via
  st.markdown (HTML/CSS-Styling), Plotly-unabhängige UI-Karten in HTML,
  Anthropic-API-Aufruf für Boarding Pass Scanning, base64-Enkodierung,
  JSON-Parsing der API-Antwort, st.dialog-Decorator, Bildkomprimierung
  via PIL, gesamte Datei-Architektur und HTML-Layoutstruktur
"""
 
# ── Imports ───────────────────────────────────────────────────────────────────
import streamlit as st                          # Streamlit: Webanwendungs-Framework
from datetime import date, datetime             # Datumsoperationen
                                                # Quelle: Claude – datetime-Modul nicht im Unterricht
import json                                     # JSON-Parsing der Claude-API-Antwort
                                                # Quelle: Claude – json-Modul nicht im Unterricht
from utils.navbar import show_navbar            # Eigene Navbar-Komponente (projektintern)
from utils.weather import get_weather, classify_weather_condition, get_airport_list
                                                # Wetterdaten-Funktionen (projektintern)
from model.predict import predict_delay, get_airline_options, get_destination_options
                                                # ML-Vorhersagefunktionen (projektintern)
 
# ── Seitenkonfiguration ───────────────────────────────────────────────────────
# Quelle: Claude – st.set_page_config() und alle Parameter nicht im Unterricht
st.set_page_config(
    page_title="Prediction – CatchYourFlight",  # Titel im Browser-Tab
    page_icon="✈",                              # Favicon im Browser-Tab
    layout="wide",                              # Breites Layout (volle Seitenbreite)
    initial_sidebar_state="collapsed",          # Sidebar beim Laden eingeklappt
)
 
# Sidebar und Einklapp-Button per CSS komplett ausblenden
# Quelle: Claude – CSS-Injection via st.markdown und data-testid-Selektoren via Claude
st.markdown("<style>[data-testid='stSidebar'],[data-testid='collapsedControl']{display:none!important}</style>", unsafe_allow_html=True)
 
# Eigene Navigationsleiste einbinden
show_navbar()
 
# Globale CSS-Stile für die Seite: Schriftgewichte, Label-Styling, HR-Transparenz
# Quelle: Claude – CSS-Styling via st.markdown und unsafe_allow_html vollständig via Claude
st.markdown("""
<style>
h1 { font-weight: 700 !important; letter-spacing: -0.02em !important; }
h2 { font-weight: 600 !important; letter-spacing: -0.01em !important; }
h3 { font-weight: 600 !important; }
.stSelectbox label, .stDateInput label, .stSlider label {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    opacity: 0.7 !important;
}
hr { opacity: 0.15 !important; }
/* Streamlit's automatischen "200MB per file" Text verstecken */
[data-testid="stFileUploaderDropzoneInstructions"] { display: none !important; }
</style>
""", unsafe_allow_html=True)
 
# Seitentitel und Untertitel
st.title("Prediction Tool")
st.markdown("Enter your flight details to get a delay probability estimate.")
st.markdown("---")                              # Horizontale Trennlinie
 
# ── SESSION STATE für Boarding Pass Daten ────────────────────────────────────
# st.session_state speichert Werte über Streamlit-Reruns hinweg
# Quelle: Claude – st.session_state-Konzept nicht im Unterricht behandelt
# Initialisierung: falls Key noch nicht vorhanden → mit None/False belegen
if "bp_airline" not in st.session_state:    st.session_state.bp_airline    = None
if "bp_origin"  not in st.session_state:    st.session_state.bp_origin     = None
if "bp_dest"    not in st.session_state:    st.session_state.bp_dest       = None
if "bp_date"    not in st.session_state:    st.session_state.bp_date       = None
if "bp_hour"    not in st.session_state:    st.session_state.bp_hour       = None
if "bp_scanned" not in st.session_state:    st.session_state.bp_scanned    = False
 
def reset_boarding_pass():
    """Setzt alle Boarding Pass Daten zurück, damit ein neuer Upload möglich ist."""
    # Alle session_state-Werte für Boarding Pass auf Ausgangszustand zurücksetzen
    st.session_state.bp_airline = None
    st.session_state.bp_origin  = None
    st.session_state.bp_dest    = None
    st.session_state.bp_date    = None
    st.session_state.bp_hour    = None
    st.session_state.bp_scanned = False
 
# ─────────────────────────────────────────────
# EINGABE-FORMULAR
# ─────────────────────────────────────────────
st.subheader("Your Flight Details")
 
# Alle verfügbaren Flughäfen aus model/predict.py laden
# airport_options = {Name: Code}, z.B. {"Atlanta (ATL)": "ATL", ...}
airport_options    = get_airport_list()
airport_codes_list = list(airport_options.values())   # ["ATL", "ORD", ...]
airport_names_list = list(airport_options.keys())     # ["Atlanta (ATL)", ...]
 
# Standard-Index für Abflughafen-Dropdown; überschreiben falls Boarding Pass gescannt
default_origin_idx = 2
if st.session_state.bp_origin and st.session_state.bp_origin in airport_codes_list:
    # Index des gescannten Flughafens in der Liste suchen
    default_origin_idx = airport_codes_list.index(st.session_state.bp_origin)
 
# Zwei-Spalten-Layout für Eingabefelder
# Quelle: Claude – st.columns() und gap-Parameter via Claude
col1, col2 = st.columns(2, gap="large")
 
with col1:
    # Dropdown: Abflughafen auswählen
    origin_name = st.selectbox(
        "Departure Airport",
        options=airport_names_list,
        index=default_origin_idx,           # Vorauswahl aus Boarding Pass oder Standard
    )
    origin_code = airport_options[origin_name]  # Kürzel aus Dictionary lesen
 
    # Airline-Optionen laden (ohne stillgelegte Airlines)
    airline_options    = get_airline_options()
    airline_names_list = list(airline_options.keys())
    default_airline_idx = 0
    # Falls Boarding Pass gescannt: passende Airline in Dropdown vorauswählen
    if st.session_state.bp_airline:
        for i, (name, code) in enumerate(airline_options.items()):  # Iteration über Dict
            if code == st.session_state.bp_airline:
                default_airline_idx = i
                break
    # Dropdown: Airline auswählen
    airline_name = st.selectbox("Airline", options=airline_names_list, index=default_airline_idx)
    airline_code = airline_options[airline_name]
 
with col2:
    # Zielflughafen-Optionen laden (origin wird ausgeschlossen)
    dest_options  = get_destination_options(origin_code)
    dest_names    = list(dest_options.keys())
    dest_codes    = list(dest_options.values())
    default_dest_idx = 0
    # Falls Boarding Pass gescannt: passenden Zielflughafen vorauswählen
    if st.session_state.bp_dest and st.session_state.bp_dest in dest_codes:
        default_dest_idx = dest_codes.index(st.session_state.bp_dest)
    # Dropdown: Zielflughafen auswählen
    dest_name = st.selectbox("Destination Airport", options=dest_names, index=default_dest_idx)
    dest_code = dest_options[dest_name]
 
    # Datumseingabe: Wert aus Boarding Pass oder heutiges Datum als Standard
    default_date = st.session_state.bp_date if st.session_state.bp_date else date.today()
    flight_date  = st.date_input("Flight Date", value=default_date, min_value=date(2020, 1, 1))
 
# Schieberegler für Abflugstunde (0–23 Uhr); Wert aus Boarding Pass oder 12 als Standard
default_hour = st.session_state.bp_hour if st.session_state.bp_hour is not None else 12
dep_hour = st.slider("Departure Hour", min_value=0, max_value=23, value=default_hour, format="%d:00")
 
# ── BOARDING PASS UPLOAD ──────────────────────────────────────────────────────
# Visueller Trenner mit zentriertem Text (HTML/CSS)
# Quelle: Claude – HTML-Divider mit Flexbox-Layout via Claude
st.markdown("""
<div style="display:flex;align-items:center;gap:1rem;margin:1.5rem 0 0.5rem;">
    <div style="flex:1;height:1px;background:rgba(255,255,255,0.15);"></div>
    <div style="font-size:0.75rem;color:#9ca3af;letter-spacing:0.08em;white-space:nowrap;">
        or upload your boarding pass instead of selecting everything
    </div>
    <div style="flex:1;height:1px;background:rgba(255,255,255,0.15);"></div>
</div>
""", unsafe_allow_html=True)
 
# ── Bekannte Werte für Validierung ───────────────────────────────────────────
# Diese Listen werden verwendet um extrahierte Werte zu prüfen
# Quelle: Claude – Validierungslisten und Verwendung via Claude
KNOWN_AIRPORTS = ["ATL","ORD","DFW","DEN","LAX","SFO","PHX","IAH","LAS","MSP","MCO","SEA","DTW","BOS","EWR","JFK"]
KNOWN_AIRLINES = ["AA","AS","B6","DL","F9","HA","MQ","OO","UA","WN"]
 
# Wenn bereits gescannt: Reset-Button anzeigen statt Upload-Widget
if st.session_state.bp_scanned:
    scan_col, reset_col = st.columns([3, 1])
    with scan_col:
        st.success("✅ Boarding pass scanned! Adjust the fields above if needed, then press Predict Delay.")
    with reset_col:
        # Reset-Button: löscht alle Boarding Pass Daten und ermöglicht neuen Upload
        if st.button("🔄 Scan new boarding pass", use_container_width=True):
            reset_boarding_pass()
            st.rerun()                          # Seite neu laden um Upload-Widget anzuzeigen
else:
    # Datei-Upload Widget (nur sichtbar wenn noch nicht gescannt)
    # Akzeptiert PNG, JPG, JPEG und PDF bis 5MB
    uploaded_file = st.file_uploader(
        "📎 Drop your boarding pass here (photo or PDF, max. 5MB) — we'll fill in the details automatically",
        type=["png", "jpg", "jpeg", "pdf"],
        label_visibility="visible",
    )
 
    if uploaded_file is not None:
        # Spinner während der Verarbeitung anzeigen
        with st.spinner("Analyzing boarding pass with AI..."):
            try:
                # Imports für Bildverarbeitung und API-Kommunikation
                # Quelle: Claude – anthropic, base64, PIL-Imports und Verwendung vollständig via Claude
                import anthropic                # Anthropic Python SDK für Claude API
                import base64                   # Base64-Kodierung für Bildübertragung
                from PIL import Image           # PIL: Bildverarbeitung und -komprimierung
                import io                       # Byte-Stream-Verarbeitung
 
                file_bytes = uploaded_file.read()   # Dateiinhalt als Bytes lesen
                # Medientyp bestimmen: PDF oder Bild
                media_type = "application/pdf" if uploaded_file.type == "application/pdf" else uploaded_file.type
 
                # Bilder über 4MB werden komprimiert bevor sie an die Claude API geschickt werden
                # (API-Limit: 5MB — Streamlit erlaubt bis 200MB, daher brauchen wir diese Zwischenstufe)
                # Quelle: Claude – Bildkomprimierungslogik vollständig via Claude
                if media_type != "application/pdf" and len(file_bytes) > 4 * 1024 * 1024:
                    img = Image.open(io.BytesIO(file_bytes))
                    img = img.convert("RGB")           # PNG mit Transparenz → JPEG-kompatibel
                    buffer = io.BytesIO()
                    quality = 85                       # Startqualität 85%
                    img.save(buffer, format="JPEG", quality=quality)
                    # Falls immer noch zu gross: Qualität weiter reduzieren
                    while buffer.tell() > 4 * 1024 * 1024 and quality > 30:
                        buffer = io.BytesIO()
                        quality -= 15              # Qualität schrittweise um 15% reduzieren
                        img.save(buffer, format="JPEG", quality=quality)
                    file_bytes = buffer.getvalue()
                    media_type = "image/jpeg"
 
                # Dateiinhalt in Base64 kodieren (API erwartet Base64-String)
                # Quelle: Claude – base64.standard_b64encode() via Claude
                b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
 
                # Anthropic-Client mit API-Key aus Streamlit Secrets initialisieren
                # Quelle: Claude – anthropic.Anthropic(), st.secrets, Client-Initialisierung via Claude
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
 
                # Verbesserter Prompt: listet bekannte Flughäfen und Airlines auf
                # damit Claude keine unbekannten Codes zurückgibt
                # Quelle: Claude – Prompt-Engineering und JSON-Ausgabeformat via Claude
                prompt = f"""You are analyzing a boarding pass image. Extract the flight information carefully.
 
The app only supports these airports: {', '.join(KNOWN_AIRPORTS)}
The app only supports these airline codes: {', '.join(KNOWN_AIRLINES)}
 
Return ONLY a valid JSON object with these exact keys (no other text, no markdown):
{{
  "airline_code": "2-letter IATA airline code from the list above, or null if not found/not supported",
  "origin": "3-letter IATA airport code from the list above, or null if not found/not supported",
  "destination": "3-letter IATA airport code from the list above, or null if not found/not supported",
  "date": "departure date in YYYY-MM-DD format, or null if not found",
  "departure_hour": departure hour as integer 0-23 (look for scheduled departure time), or null if not found
}}
 
Look carefully at all text on the boarding pass. Flight numbers, gate info, and barcodes are not needed."""
 
                # API-Inhalt je nach Dateityp aufbauen (PDF oder Bild unterschiedlich)
                # Quelle: Claude – Anthropic Messages API content-Format vollständig via Claude
                if media_type == "application/pdf":
                    content = [
                        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64}},
                        {"type": "text", "text": prompt}
                    ]
                else:
                    content = [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                        {"type": "text", "text": prompt}
                    ]
 
                # API-Anfrage an Claude senden; Antwort enthält extrahierte Flugdaten als JSON
                # Quelle: Claude – client.messages.create() und Parameter via Claude
                response = client.messages.create(
                    model="claude-opus-4-5",            # Modellversion für OCR-Aufgabe
                    max_tokens=400,                     # Kurze Antwort reicht (nur JSON)
                    messages=[{"role": "user", "content": content}]
                )
 
                # JSON parsen (Backticks entfernen falls Claude sie trotzdem schreibt)
                # Quelle: Claude – json.loads() und Bereinigung via Claude
                raw       = response.content[0].text.strip().replace("```json", "").replace("```", "").strip()
                extracted = json.loads(raw)             # JSON-String → Python-Dictionary
 
                # Extrahierte Werte validieren: nur bekannte Codes in session_state speichern
                # Unbekannte Codes (nicht in KNOWN_*) werden als None gesetzt → manuelle Eingabe nötig
                airline_raw = extracted.get("airline_code")
                origin_raw  = extracted.get("origin")
                dest_raw    = extracted.get("destination")
 
                st.session_state.bp_airline = airline_raw if airline_raw in KNOWN_AIRLINES else None
                st.session_state.bp_origin  = origin_raw  if origin_raw  in KNOWN_AIRPORTS else None
                st.session_state.bp_dest    = dest_raw    if dest_raw    in KNOWN_AIRPORTS else None
                st.session_state.bp_hour    = extracted.get("departure_hour")
                st.session_state.bp_scanned = True      # Scan als abgeschlossen markieren
 
                # Datum parsen falls vorhanden (Format "YYYY-MM-DD" → date-Objekt)
                if extracted.get("date"):
                    try:
                        st.session_state.bp_date = datetime.strptime(extracted["date"], "%Y-%m-%d").date()
                    except Exception:
                        pass                            # Ungültiges Datum ignorieren
 
                # Warnung anzeigen wenn nicht alle Felder gefunden wurden
                missing = []
                if not st.session_state.bp_airline: missing.append("airline")
                if not st.session_state.bp_origin:  missing.append("departure airport")
                if not st.session_state.bp_dest:    missing.append("destination airport")
 
                if missing:
                    st.warning(f"⚠️ Could not extract: {', '.join(missing)}. Please select manually above.")
                else:
                    st.success("✅ Boarding pass scanned! Fields updated above — press Predict Delay.")
 
                st.rerun()                              # Seite neu laden um Dropdowns zu aktualisieren
 
            except Exception as e:
                # Fehlerbehandlung: bei beliebigem Fehler Warnung ausgeben, manuelle Eingabe möglich
                st.warning(f"Could not scan boarding pass automatically: {e}. Please fill in the details manually.")
 
# ── About Us Dialog ───────────────────────────────────────────────────────────
# @st.dialog definiert ein modales Popup-Fenster
# Quelle: Claude – st.dialog-Decorator nicht im Unterricht behandelt
@st.dialog("About Us")
def show_about():
    # Projektinfos als Markdown-Text anzeigen
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
 
# ── PREDICT BUTTON ────────────────────────────────────────────────────────────
st.markdown("---")
# Primärer Button (type="primary" = farblich hervorgehoben) über volle Breite
predict_btn = st.button("✈ Predict Delay", type="primary", use_container_width=True)
 
if predict_btn:
    # Datum als String formatieren (für predict_delay-Funktion benötigt)
    date_str = flight_date.strftime("%Y-%m-%d")
 
    with st.spinner("Loading weather & running prediction..."):
        # Wetterdaten für Abflughafen und Datum laden
        try:
            weather_df = get_weather(origin_code, date_str)
        except Exception as e:
            st.error(f"Could not load weather data: {e}")
            st.stop()                           # Ausführung hier stoppen falls Wetter fehlt
 
        # ML-Vorhersage mit allen Eingabewerten aufrufen
        result = predict_delay(
            airline     = airline_code,
            origin      = origin_code,
            destination = dest_code,
            flight_date = flight_date,
            dep_hour    = dep_hour,
            weather_df  = weather_df,
        )
 
    # Falls Modell nicht geladen: Fehlermeldung anzeigen und stoppen
    if "error" in result:
        st.error(result["error"])
        st.stop()
 
    # Ergebniswerte aus dem Rückgabe-Dictionary extrahieren
    risk_color = result["risk_color"]           # Hex-Farbcode je nach Risiko
    prob_pct   = result["delay_probability_pct"]# Verspätungswahrscheinlichkeit als "XX%"
    category   = result["display_category"]     # Wahrscheinlichste Verspätungskategorie
    risk_level = result["risk_level"]           # "Low" / "Medium" / "High"
    factors    = result["top_factors"]          # Liste der Einflussfaktoren
 
    # Dictionary: Wetterbedingung → Emoji-Label für die Anzeige
    # Quelle: Claude – Dictionary-Konzept aus Unterricht; Inhalte und Emoji via Claude
    condition_icons = {
        "Heavy Snow":  "❄️ Heavy Snow", "Light Snow":  "🌨️ Light Snow",
        "Heavy Rain":  "🌧️ Heavy Rain", "Light Rain":  "🌦️ Light Rain",
        "Strong Wind": "💨 Strong Wind", "Overcast":   "☁️ Overcast",
        "Good":        "☀️ Good",
    }
 
    st.markdown("---")
 
    # ── KPI CARDS ─────────────────────────────────────────────────────────────
    # Drei nebeneinander angeordnete Kennzahl-Karten (HTML/CSS Grid)
    # Quelle: Claude – gesamtes HTML/CSS-Layout der KPI-Karten vollständig via Claude
    st.markdown(f"""
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.25rem;margin-bottom:2rem;">
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:3px solid {risk_color};border-radius:0 0 12px 12px;padding:1.75rem 1.5rem;text-align:center;">
<div style="font-size:0.65rem;color:#9ca3af;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.75rem;">Delay Probability</div>
<div style="font-size:3rem;font-weight:700;color:{risk_color};line-height:1;margin-bottom:0.25rem;">{prob_pct}</div>
<div style="font-size:0.8rem;color:#9ca3af;">chance of delay</div>
</div>
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:3px solid #6366F1;border-radius:0 0 12px 12px;padding:1.75rem 1.5rem;text-align:center;">
<div style="font-size:0.65rem;color:#9ca3af;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.75rem;">Expected Delay</div>
<div style="font-size:2rem;font-weight:700;color:#111111;line-height:1.2;margin-bottom:0.25rem;">{category}</div>
<div style="font-size:0.8rem;color:#9ca3af;">most likely category</div>
</div>
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:3px solid {risk_color};border-radius:0 0 12px 12px;padding:1.75rem 1.5rem;text-align:center;">
<div style="font-size:0.65rem;color:#9ca3af;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:0.75rem;">Risk Level</div>
<div style="display:inline-block;background:{risk_color}20;color:{risk_color};font-weight:700;font-size:1.4rem;padding:0.35rem 1.25rem;border-radius:20px;margin-top:0.25rem;">{risk_level}</div>
<div style="font-size:0.8rem;color:#9ca3af;margin-top:0.5rem;">{origin_code} → {dest_code}</div>
</div>
</div>
""", unsafe_allow_html=True)
 
    # ── WEATHER ───────────────────────────────────────────────────────────────
    # Wetterdaten für die gewählte Abflugstunde aus DataFrame filtern (Boolean Masking)
    # Konzept Boolean Masking aus Unterricht; .iloc[0] via Claude
    weather_at_hour = weather_df[weather_df["hour"] == dep_hour].iloc[0]
    condition       = classify_weather_condition(weather_at_hour)   # Wetterkategorie bestimmen
    condition_label = condition_icons.get(condition, condition)     # Emoji-Label holen
 
    # Wetter-Karte als HTML-Block anzeigen (vier Wetterwerte nebeneinander)
    # Quelle: Claude – HTML/CSS-Layoutstruktur und Styling vollständig via Claude
    st.markdown(f"""
<div style="background:#f8f9fa;border:1px solid #e5e7eb;border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1.5rem;">
<div style="font-size:0.65rem;color:#9ca3af;letter-spacing:0.12em;text-transform:uppercase;margin-bottom:1rem;">Weather at Departure · {dep_hour:02d}:00</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:1rem;">
<div style="text-align:center;"><div style="font-size:1.5rem;">🌡️</div>
<div style="font-size:0.7rem;color:#9ca3af;margin:0.25rem 0;">Temperature</div>
<div style="font-weight:600;color:#111111;">{weather_at_hour['temperature']} °C</div></div>
<div style="text-align:center;"><div style="font-size:1.5rem;">🌧️</div>
<div style="font-size:0.7rem;color:#9ca3af;margin:0.25rem 0;">Precipitation</div>
<div style="font-weight:600;color:#111111;">{weather_at_hour['precipitation']} mm</div></div>
<div style="text-align:center;"><div style="font-size:1.5rem;">💨</div>
<div style="font-size:0.7rem;color:#9ca3af;margin:0.25rem 0;">Wind Speed</div>
<div style="font-weight:600;color:#111111;">{weather_at_hour['windspeed']} km/h</div></div>
<div style="text-align:center;"><div style="font-size:1.5rem;">☁️</div>
<div style="font-size:0.7rem;color:#9ca3af;margin:0.25rem 0;">Condition</div>
<div style="background:{risk_color}20;color:{risk_color};font-weight:600;font-size:0.8rem;padding:0.2rem 0.5rem;border-radius:10px;display:inline-block;">{condition_label}</div></div>
</div></div>
""", unsafe_allow_html=True)
 
    st.markdown("---")
 
    # ── FULL DAY OVERVIEW ─────────────────────────────────────────────────────
    # Prüfen ob stündliche Daten vorliegen oder nur ein Tagesdurchschnitt
    # .nunique() gibt Anzahl eindeutiger Werte zurück; 1 = alle Stunden haben denselben Wert
    is_daily_avg = weather_df["temperature"].nunique() == 1
 
    if not is_daily_avg:
        st.subheader("Full Day Weather Overview")
 
        # Emoji-Dictionary für Wetterkondition → Icon
        cond_emoji = {
            "Heavy Snow": "❄️", "Light Snow": "🌨️",
            "Heavy Rain": "🌧️", "Light Rain": "🌦️",
            "Strong Wind": "💨", "Overcast": "☁️", "Good": "☀️",
        }
 
        # HTML-Karten für jede Stunde des Tages aufbauen (for-Schleife über DataFrame-Zeilen)
        # Abflugstunde wird farblich hervorgehoben
        # Quelle: Claude – HTML-Karten-Generierung in Python-Schleife vollständig via Claude
        cards_html = ""
        for _, row in weather_df.iterrows():        # iterrows() iteriert über DataFrame-Zeilen
            h      = int(row["hour"])
            is_dep = h == dep_hour                  # Boolean: ist dies die Abflugstunde?
            cond   = classify_weather_condition(row)
            emoji  = cond_emoji.get(cond, "🌤️")
            prcp   = float(row["precipitation"] or 0)
            wind   = float(row["windspeed"] or 0)
            temp   = float(row["temperature"] or 0)
 
            # Abflugstunde: farbiger Gradient-Hintergrund; andere Stunden: helles Grau
            if is_dep:
                card_style = f"background:linear-gradient(160deg,{risk_color} 0%,#6366f1 100%);border:none;box-shadow:0 4px 14px {risk_color}55;"
                text_main  = "color:#ffffff;"
                text_sub   = "color:rgba(255,255,255,0.75);"
                hour_style = "color:rgba(255,255,255,0.85);font-weight:700;"
                dot        = f'<div style="width:6px;height:6px;border-radius:50%;background:#fff;margin:0 auto 4px;opacity:0.9;"></div>'
            else:
                card_style = "background:#f8fafc;border:1px solid #e5e7eb;"
                text_main  = "color:#111111;"
                text_sub   = "color:#9ca3af;"
                hour_style = "color:#6b7280;font-weight:500;"
                dot        = ""
 
            # HTML-Karte für diese Stunde zum Gesamtstring hinzufügen
            cards_html += f"""<div style="flex:0 0 auto;width:80px;border-radius:16px;padding:0.9rem 0.5rem;text-align:center;{card_style}">
{dot}
<div style="font-size:0.7rem;letter-spacing:0.04em;{hour_style}margin-bottom:0.4rem;">{h:02d} h</div>
<div style="font-size:1.5rem;font-weight:700;{text_main}margin-bottom:0.2rem;">{temp:.0f}°</div>
<div style="font-size:1.6rem;margin-bottom:0.4rem;">{emoji}</div>
<div style="font-size:0.7rem;{text_sub}margin-bottom:0.15rem;">💧 {prcp:.0f}%</div>
<div style="font-size:0.7rem;{text_sub}">💨 {wind:.0f}</div>
</div>"""
 
        # Alle Stunden-Karten in scrollbarem Container anzeigen
        st.markdown(f"""
<div style="background:#f1f5f9;border-radius:20px;padding:1.25rem 1rem;">
<div style="display:flex;gap:0.5rem;overflow-x:auto;padding-bottom:0.25rem;scrollbar-width:thin;scrollbar-color:#cbd5e1 transparent;">
{cards_html}
</div>
</div>
""", unsafe_allow_html=True)
    else:
        # Falls nur Tagesdurchschnitt verfügbar: Hinweis anzeigen
        st.caption("📅 Weather based on historical daily average (same day, last 3 years) — hourly breakdown not available for dates beyond 16 days.")
 
    st.markdown("---")
 
    # ── CONTRIBUTING FACTORS ──────────────────────────────────────────────────
    st.subheader("Contributing Factors")
    if factors:
        # Farb- und Label-Dictionaries für Impact-Level
        # if/elif/else-Konzept aus Unterricht; Hex-Codes via Claude
        _impact_colors = {"high": "#EF4444", "medium": "#F59E0B", "low": "#10B981"}
        _impact_labels = {"high": "high impact", "medium": "medium", "low": "low"}
 
        # HTML-Zellen für jeden Faktor aufbauen (for-Schleife über Faktoren-Liste)
        # Quelle: Claude – HTML-Zellen-Generierung und Grid-Layout vollständig via Claude
        cells = ""
        for f in factors:
            color = _impact_colors.get(f["impact"], "#9ca3af")   # Farbe für Impact
            label = _impact_labels.get(f["impact"], f["impact"]) # Lesbares Label
            cells += f"""<div style="background:#f8f9fa;border:1px solid #e5e7eb;border-radius:10px;padding:0.85rem 1.1rem;display:flex;align-items:center;gap:0.75rem;">
<div style="width:10px;height:10px;border-radius:50%;background:{color};flex-shrink:0;"></div>
<div><span style="font-size:0.9rem;color:#111111;font-weight:500;">{f['label']}</span>
<span style="font-size:0.78rem;color:#9ca3af;margin-left:0.4rem;">({label})</span></div></div>"""
 
        # Faktoren-Karten in 2-spaltiger Grid-Ansicht anzeigen
        st.markdown(f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;margin-bottom:1.5rem;">{cells}</div>', unsafe_allow_html=True)
 
    w = result["weather_used"]                  # Verwendete Wetterdaten (für spätere Nutzung)
 
 
# ── About Us Button ───────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
# Drei Spalten: Button mittig platzieren (Spalten-Verhältnis 3:1:3)
_, btn_col, _ = st.columns([3, 1, 3])
with btn_col:
    # Button öffnet show_about()-Dialog bei Klick
    if st.button("About Us", use_container_width=True):
        show_about()
 
# ── Footer ────────────────────────────────────────────────────────────────────
# Projektinformation als zentrierter Fusszeilen-Text
# Quelle: Claude – HTML-Footer-Styling via Claude
st.markdown("""
<div style="border-top:1px solid #e0e0e0; padding-top:1rem; text-align:center;
    color:#aaaaaa; font-size:0.72rem;">
    Computer Science Project · University of St. Gallen · CatchYourFlight · 2026
</div>
""", unsafe_allow_html=True)
