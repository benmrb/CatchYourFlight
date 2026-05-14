# CatchYourFlight — Flight Delay Prediction App
**HSG Gruppenprojekt | Grundlagen und Methoden der Informatik**

---

**Live App:** https://catchyourflight.streamlit.app

---

## Schnellstart

**Voraussetzung:** Python 3.14 oder neuer

```bash
# 1. Ins Projektverzeichnis wechseln
cd CatchYourFlight

# 2. Dependencies installieren
python -m pip install -r requirements.txt

# 3. API Key eintragen (siehe unten)

# 4. App starten
streamlit run app.py
```

Browser öffnet sich automatisch auf `http://localhost:8501`

---

## Anthropic API Key (Boarding Pass Scanner)

Die App läuft **ohne API-Key** vollständig — alle Felder können manuell eingegeben werden.

**Mit API-Key** kann ein Foto oder PDF eines Boarding Passes hochgeladen werden,
und die App füllt Airline, Flughafen, Datum und Uhrzeit automatisch aus.

Den Key in `.streamlit/secrets.toml` eintragen (Datei selbst erstellen):

```toml
ANTHROPIC_API_KEY = "hier-den-eigenen-Key-einfügen"
```

---

## Projektstruktur

```
CatchYourFlight/
├── app.py                  # Entry Point (Streamlit Navigation)
├── 01_Dashboard.py         # Startseite mit Hero, Charts und About Us
├── requirements.txt        # Alle Dependencies
├── hero.png                # Hintergrundbild Startseite
├── logo.png                # App-Logo Navbar
│
├── .streamlit/
│   └── config.toml         # Theme (Farben, Schrift)
│
├── pages/
│   └── 02_Prediction.py    # Prediction Tool (ML + Boarding Pass Scanner)
│
├── model/
│   └── predict.py          # ML-Vorhersagelogik (XGBoost, Haversine, Features)
│
├── models/
│   ├── binary_model.pkl    # Trainiertes Binär-Klassifikationsmodell
│   ├── multiclass_model.pkl# Trainiertes Multi-Class-Modell
│   ├── encoders.pkl        # Label-Encoder für kategorische Features
│   └── feature_list.pkl    # Erwartete Feature-Spalten
│
└── utils/
    ├── navbar.py           # Globale Navigationsleiste + CSS-Styling
    ├── dashboard_data.py   # Aggregierte Verspätungsstatistiken (BTS 2015)
    └── weather.py          # Wetterdaten via Open-Meteo API
```

---

## Die 2 ML-Modelle

### 1. Binary Classification (XGBoost)
Klassifiziert ob ein Flug verspätet ist (> 15 min) oder nicht.
Trainiert auf 2.54 Millionen Flügen aus dem BTS 2015 Datensatz.
**Accuracy: 67.0%**

Features: Monat, Wochentag, Abflugstunde, Airline, Abflughafen, Zielflughafen,
Distanz (km), Temperatur, Niederschlag, Schneefall, Wind, Bewölkung.

*Quelle: Claude (Anthropic) — XGBoost, joblib, predict_proba() nicht im Lehrplan*

### 2. Multiclass Classification (XGBoost)
Klassifiziert die wahrscheinlichste Verspätungskategorie:
No Delay / 15–30 min / 30–60 min / 60–120 min / 120+ min.
**Accuracy: 80.4%**

*Quelle: Claude (Anthropic) — Multi-Class XGBoost nicht im Lehrplan*

### Boarding Pass Scanner (Anthropic Claude API)
Extrahiert Airline, Flughäfen, Datum und Abflugzeit aus einem Foto oder PDF
eines Boarding Passes mittels Vision-KI und füllt die Felder automatisch aus.

*Quelle: Claude (Anthropic) — Anthropic API, base64-Enkodierung, PIL nicht im Lehrplan*

---

## App-Seiten

| Seite | Beschreibung |
|---|---|
| **Dashboard** | 3 interaktive Charts: Verspätungen nach Tageszeit, Wochentag und Airline |
| **Prediction Tool** | Flugdetails eingeben oder Boarding Pass hochladen → Verspätungswahrscheinlichkeit |

---

## Wetterdaten

Implementiert in `utils/weather.py`:

Die App lädt stündliche Wetterdaten für den gewählten Abflughafen automatisch:
- Vergangene Daten → Open-Meteo Archive API
- Bis 16 Tage voraus → Open-Meteo Forecast API
- Weiter in der Zukunft → Historischer 3-Jahres-Durchschnitt (2022–2024)

*Quelle: Claude (Anthropic) — requests-Bibliothek und API-Architektur nicht im Lehrplan*

---

## Datensatz

Bureau of Transportation Statistics (BTS) — US-Inlandsflüge 2015
**2.54 Millionen Flüge** · 16 Flughäfen: ATL, BOS, DEN, DFW, DTW, EWR, IAH, JFK, LAS, LAX, MCO, MSP, ORD, PHX, SEA, SFO
Bezogen via Kaggle.

---

## Limitierungen

**Veraltete Trainingsdaten (2015)**
Das ML-Modell wurde auf BTS-Flugdaten aus dem Jahr 2015 trainiert. 
Seitdem haben sich Airline-Strukturen, Flughafenkapazitäten und 
Verspätungsmuster verändert — die Vorhersagen spiegeln historische 
Muster wider, nicht den aktuellen Stand.

**Begrenzte Flughäfen und Airlines**
Die App unterstützt nur 16 US-Flughäfen und 10 Airlines. 
Andere Routen und Carrier können nicht vorhergesagt werden.

**Modell-Accuracy**
Die Binary Classification erreicht 67.0% Genauigkeit — besser als 
Zufall, aber keine zuverlässige Garantie. Unerwartete Ereignisse 
(Streiks, technische Defekte, extreme Wetterereignisse) können 
nicht vorhergesagt werden.

**Wetterdaten für weit entfernte Daten**
Für Daten mehr als 16 Tage in der Zukunft werden historische 
Durchschnittswerte (2022–2024) statt echter Vorhersagen verwendet.

**Boarding Pass Scanner**
Der Scanner funktioniert nur mit unterstützten Flughäfen und Airlines. 
Er benötigt einen Anthropic API Key — ohne Key ist nur manuelle 
Eingabe möglich.

**Nur US-Inlandsflüge**
Die App ist ausschliesslich auf US-Domestic-Flüge ausgerichtet. 
Internationale Flüge werden nicht unterstützt.

---

## Einsatz von Generativer KI

Gemäss den Referenzierungsregeln für Generative KI wird der Einsatz von
Claude (Anthropic) wie folgt offengelegt:

**Mit Claude erarbeitet (über Lehrplan hinausgehend):**

| Komponente | Datei | Begründung |
|---|---|---|
| XGBoost Modelltraining | `model/predict.py` | XGBoost nicht im Lehrplan |
| Haversine-Formel (Distanz) | `model/predict.py` | Trigonometrische Formel nicht im Lehrplan |
| joblib Modell-Laden | `model/predict.py` | joblib nicht im Lehrplan |
| Open-Meteo API-Architektur | `utils/weather.py` | requests-Bibliothek nicht im Lehrplan |
| Anthropic API (Boarding Pass) | `pages/02_Prediction.py` | Vision-API nicht im Lehrplan |
| CSS-Styling via unsafe_allow_html | alle Seiten | CSS nicht im Lehrplan |
| Plotly-Diagramme | `01_Dashboard.py` | Plotly nicht im Lehrplan |
| st.session_state Konzept | `pages/02_Prediction.py` | Session State nicht im Lehrplan |

**Eigenleistung (selbst erarbeitet):**

| Komponente | Datei |
|---|---|
| Feature Engineering (12 Features) | `model/predict.py` |
| Contributing Factors Logik | `model/predict.py` |
| Aggregierte Dashboard-Statistiken | `utils/dashboard_data.py` |
| Filter- und Routing-Logik (Wetter) | `utils/weather.py` |
| App-Navigation + Session-Management | `app.py` |
| Boarding Pass Validierung (KNOWN_AIRPORTS) | `pages/02_Prediction.py` |

Alle KI-generierten Stellen sind im Quellcode mit `# Quelle: Claude (Sonnet 4)` markiert.

