"""
utils/weather.py
 
Stündliche Wetterdaten für 16 US-Flughäfen via Open-Meteo API.
Wählt automatisch die passende Datenquelle je nach Datum:
  - Vergangene Daten    → Open-Meteo Archive API
  - Bis 16 Tage voraus → Open-Meteo Forecast API
  - Weiter als 16 Tage → Historischer 3-Jahres-Durchschnitt (2022–2024)
  - Kein API-Zugriff   → Monatlicher Fallback-Wert
 
Abhängigkeiten:
  - Open-Meteo Archive API  (https://archive-api.open-meteo.com)
  - Open-Meteo Forecast API (https://api.open-meteo.com)
 
Autoren: Stefanie Seiler
Datum:   Mai 2026
 
Quellen:
- CS-Unterricht: Funktionsdefinitionen, if/elif/else, for-Schleifen,
  Dictionaries, f-Strings, pandas DataFrame-Grundlagen,
  try/except-Fehlerbehandlung (Grundkonzept)
- Claude (Sonnet 4): requests-Bibliothek (HTTP-Anfragen), Open-Meteo
  API-Parametrisierung, datetime-Modul (.strptime, .replace, .strftime),
  pd.concat() für DataFrame-Zusammenführung, .mean().round(),
  Temperaturkurven-Formel im Fallback, classify_weather_condition()-Logik,
  gesamte Datei-Architektur und API-Struktur
"""
 
# ── Imports ───────────────────────────────────────────────────────────────────
import requests                     # HTTP-Anfragen an Open-Meteo API
                                    # Quelle: Claude – requests-Bibliothek nicht im Unterricht
import pandas as pd                 # DataFrame-Erstellung und -Verarbeitung
from datetime import date, datetime # Datumsoperationen
                                    # Quelle: Claude – datetime-Modul nicht im Unterricht
 
# ── Flughafen-Koordinaten ─────────────────────────────────────────────────────
# Dictionary: IATA-Code → GPS-Koordinaten und lesbarer Name
# Wird für API-Anfragen (lat/lon) und UI-Anzeige (name) verwendet
# Quelle: Claude – Koordinaten und Datenstruktur vollständig via Claude
AIRPORT_COORDS = {
    "ATL": {"lat": 33.6407,  "lon": -84.4277,  "name": "Atlanta (ATL)"},
    "ORD": {"lat": 41.9742,  "lon": -87.9073,  "name": "Chicago O'Hare (ORD)"},
    "DFW": {"lat": 32.8998,  "lon": -97.0403,  "name": "Dallas Fort Worth (DFW)"},
    "DEN": {"lat": 39.8561,  "lon": -104.6737, "name": "Denver (DEN)"},
    "LAX": {"lat": 33.9425,  "lon": -118.4081, "name": "Los Angeles (LAX)"},
    "SFO": {"lat": 37.6213,  "lon": -122.3790, "name": "San Francisco (SFO)"},
    "PHX": {"lat": 33.4373,  "lon": -112.0078, "name": "Phoenix (PHX)"},
    "IAH": {"lat": 29.9902,  "lon": -95.3368,  "name": "Houston (IAH)"},
    "LAS": {"lat": 36.0840,  "lon": -115.1537, "name": "Las Vegas (LAS)"},
    "MSP": {"lat": 44.8848,  "lon": -93.2223,  "name": "Minneapolis (MSP)"},
    "MCO": {"lat": 28.4294,  "lon": -81.3089,  "name": "Orlando (MCO)"},
    "SEA": {"lat": 47.4502,  "lon": -122.3088, "name": "Seattle (SEA)"},
    "DTW": {"lat": 42.2162,  "lon": -83.3554,  "name": "Detroit (DTW)"},
    "BOS": {"lat": 42.3656,  "lon": -71.0096,  "name": "Boston (BOS)"},
    "EWR": {"lat": 40.6895,  "lon": -74.1745,  "name": "Newark (EWR)"},
    "JFK": {"lat": 40.6413,  "lon": -73.7781,  "name": "New York JFK (JFK)"},
}
 
# Maximale Anzahl Tage ab heute für die Forecast-API (Open-Meteo-Limit)
MAX_FORECAST_DAYS = 16
 
# Jahre für historischen Tagesdurchschnitt (falls Datum ausserhalb Forecast-Fenster)
HISTORICAL_YEARS  = [2024, 2023, 2022]
 
 
# ── Hauptfunktion: Wetterdaten abrufen ────────────────────────────────────────
def get_weather(airport_code: str, flight_date: str) -> pd.DataFrame:
    # Wählt automatisch die richtige Datenquelle für das gegebene Datum
    # und gibt einen DataFrame mit 24 Zeilen (eine pro Stunde) zurück
    # Quelle: Claude – Datums-Routing-Logik und datetime-Operationen via Claude
 
    # Unbekannten Flughafen abfangen
    if airport_code not in AIRPORT_COORDS:
        raise ValueError(f"Unbekannter Flughafen: {airport_code}")
 
    coords     = AIRPORT_COORDS[airport_code]   # Koordinaten des Flughafens holen
 
    # Datum-String in date-Objekt umwandeln; Tagesdifferenz zu heute berechnen
    # Quelle: Claude – datetime.strptime() und .days nicht im Unterricht
    target     = datetime.strptime(flight_date, "%Y-%m-%d").date()
    today      = date.today()
    days_ahead = (target - today).days          # Negativ = Vergangenheit, 0 = heute
 
    # Routing: passende API-Funktion je nach Datum aufrufen
    if target <= today:                         # Datum in Vergangenheit oder heute
        return _fetch_archive(coords, flight_date)
    elif days_ahead <= MAX_FORECAST_DAYS:       # Innerhalb des 16-Tage-Forecast-Fensters
        return _fetch_forecast(coords, flight_date)
    else:                                       # Mehr als 16 Tage in der Zukunft
        return _get_historical_day_average(coords, target)
 
 
# ── Archive API ───────────────────────────────────────────────────────────────
def _fetch_archive(coords, flight_date):
    # Ruft historische Stundendaten von der Open-Meteo Archive API ab
    # Quelle: Claude – requests.get(), params-Dict, .raise_for_status() via Claude
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude":   coords["lat"],
        "longitude":  coords["lon"],
        "start_date": flight_date,
        "end_date":   flight_date,
        "hourly": "temperature_2m,precipitation,snowfall,windspeed_10m,cloudcover",
        "timezone": "America/New_York",         # Einheitliche Zeitzone für alle US-Flughäfen
    }
    response = requests.get(url, params=params, timeout=10)  # HTTP GET mit 10s Timeout
    response.raise_for_status()                 # Wirft Exception bei HTTP-Fehler (4xx/5xx)
    return _parse_hourly(response.json())       # JSON → DataFrame
 
 
# ── Forecast API ──────────────────────────────────────────────────────────────
def _fetch_forecast(coords, flight_date):
    # Ruft Vorhersage-Stundendaten von der Open-Meteo Forecast API ab
    # Quelle: Claude – identische Struktur wie _fetch_archive, via Claude
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude":   coords["lat"],
        "longitude":  coords["lon"],
        "start_date": flight_date,
        "end_date":   flight_date,
        "hourly": "temperature_2m,precipitation,snowfall,windspeed_10m,cloudcover",
        "timezone": "America/New_York",
    }
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return _parse_hourly(response.json())
 
 
# ── JSON → DataFrame umwandeln ────────────────────────────────────────────────
def _parse_hourly(data):
    # Wandelt die JSON-Antwort der Open-Meteo API in einen pandas DataFrame um
    # data["hourly"] enthält je eine Liste mit 24 Werten pro Wettervariable
    # Quelle: Claude – API-Antwortstruktur und DataFrame-Aufbau via Claude
    return pd.DataFrame({
        "hour":          range(24),                             # Stunden 0–23
        "temperature":   data["hourly"]["temperature_2m"],      # Temperatur in °C
        "precipitation": data["hourly"]["precipitation"],       # Niederschlag in mm
        "snowfall":      data["hourly"]["snowfall"],            # Schneefall in mm
        "windspeed":     data["hourly"]["windspeed_10m"],       # Wind in km/h (10m Höhe)
        "cloudcover":    data["hourly"]["cloudcover"],          # Bewölkung in %
    })
 
 
# ── Historischer 3-Jahres-Durchschnitt ───────────────────────────────────────
def _get_historical_day_average(coords, target):
    # Berechnet den Durchschnitt desselben Tages aus den letzten 3 Jahren
    # für Daten ausserhalb des 16-Tage-Forecast-Fensters
    # Quelle: Claude – pd.concat(), .mean().round(), .replace(year=) via Claude
 
    all_days = []
    for year in HISTORICAL_YEARS:               # Für jedes der letzten 3 Jahre
        try:
            # Datum auf dasselbe Monat/Tag im jeweiligen Jahr setzen
            historical_date = target.replace(year=year)
        except ValueError:
            # Sonderfall: 29. Februar in Nicht-Schaltjahr → auf 28. Feb ausweichen
            historical_date = target.replace(year=year, day=28)
        try:
            # Archivdaten für diesen historischen Tag abrufen
            df = _fetch_archive(coords, historical_date.strftime("%Y-%m-%d"))
            all_days.append(df)
        except Exception:
            continue                            # Fehler ignorieren, nächstes Jahr versuchen
 
    # Falls kein historischer Tag geladen: monatlichen Fallback verwenden
    if not all_days:
        return _simple_fallback(target.month)
 
    # Alle geladenen Tage zusammenführen und Spaltenmittelwerte berechnen
    # pd.concat() stapelt mehrere DataFrames übereinander
    # Quelle: Claude – pd.concat() und .mean().round() via Claude
    combined  = pd.concat(all_days)
    daily_avg = combined[["temperature", "precipitation", "snowfall", "windspeed", "cloudcover"]].mean().round(1)
 
    # Einen neuen DataFrame mit 24 Zeilen aufbauen (alle Stunden = Tagesdurchschnitt)
    rows = []
    for h in range(24):
        rows.append({
            "hour":          h,
            "temperature":   daily_avg["temperature"],
            "precipitation": daily_avg["precipitation"],
            "snowfall":      daily_avg["snowfall"],
            "windspeed":     daily_avg["windspeed"],
            "cloudcover":    daily_avg["cloudcover"],
        })
    return pd.DataFrame(rows)
 
 
# ── Monatlicher Fallback (kein API-Zugriff möglich) ───────────────────────────
def _simple_fallback(month):
    # Erzeugt synthetische Stundendaten basierend auf monatlichen Durchschnittswerten
    # Wird verwendet wenn alle API-Aufrufe fehlgeschlagen sind
    # Quelle: Claude – Tagesgang-Formel und Monatswerte vollständig via Claude
 
    # Monatliche Durchschnittswerte: (tmax, tmin, prcp_h, wind)
    # tmax/tmin: Tages-/Nachttemperatur in °C; prcp_h: Niederschlag mm/h; wind: km/h
    monthly = {
        1:  (4, -4, 0.12, 25),  2:  (6, -2, 0.10, 23),  3:  (12, 3, 0.13, 22),
        4:  (17, 7, 0.12, 20),  5:  (22, 12, 0.13, 18),  6:  (27, 17, 0.11, 16),
        7:  (30, 20, 0.13, 15), 8:  (29, 19, 0.12, 15),  9:  (25, 15, 0.11, 17),
        10: (18, 8, 0.10, 19),  11: (11, 2, 0.11, 22),   12: (5, -3, 0.12, 24),
    }
    tmax, tmin, prcp_h, wind = monthly.get(month, (20, 10, 0.10, 20))  # Fallback: 20°C
 
    # Stündlichen Tagesgang berechnen: Temperaturkurve steigt von 06:00 bis 14:00,
    # fällt bis 20:00 und bleibt nachts auf Minimum
    # Quelle: Claude – sinusähnliche Näherungsformel für Tagestemperatur via Claude
    rows = []
    for h in range(24):
        if 6 <= h <= 14:    temp = tmin + (tmax - tmin) * (h - 6) / 8   # Anstieg morgens
        elif 14 < h <= 20:  temp = tmax - (tmax - tmin) * (h - 14) / 6  # Abfall nachmittags
        else:               temp = tmin                                   # Nacht = Minimum
        rows.append({
            "hour":          h,
            "temperature":   round(temp, 1),
            "precipitation": prcp_h,
            "snowfall":      0.1 if month in [12, 1, 2] else 0.0,  # Schnee nur im Winter
            "windspeed":     float(wind),
            "cloudcover":    50,                                    # Neutraler Standardwert
        })
    return pd.DataFrame(rows)
 
 
# ── Wetterbedingung klassifizieren ────────────────────────────────────────────
def classify_weather_condition(row):
    # Gibt eine textuelle Wetterbeschreibung basierend auf den Messwerten zurück
    # Reihenfolge: Schnee > Regen > Wind > Bewölkung > Gut
    # Quelle: Claude – Schwellenwerte und Prioritätsreihenfolge via Claude;
    #         if/elif/else-Konzept aus Unterricht
    if   row["snowfall"]      is not None and row["snowfall"]      > 0.5:  return "Heavy Snow"
    elif row["snowfall"]      is not None and row["snowfall"]      > 0:    return "Light Snow"
    elif row["precipitation"] is not None and row["precipitation"] > 2.0:  return "Heavy Rain"
    elif row["precipitation"] is not None and row["precipitation"] > 0.5:  return "Light Rain"
    elif row["windspeed"]     is not None and row["windspeed"]     > 50:   return "Strong Wind"
    elif row["cloudcover"]    is not None and row["cloudcover"]    > 80:   return "Overcast"
    else: return "Good"
 
 
# ── Hilfsfunktionen für Dropdown-Optionen ─────────────────────────────────────
def get_airport_name(airport_code):
    # Gibt den lesbaren Namen eines Flughafens zurück (z.B. "Atlanta (ATL)")
    # .get() mit leerem Dict als Fallback verhindert KeyError bei unbekanntem Code
    return AIRPORT_COORDS.get(airport_code, {}).get("name", airport_code)
 
 
def get_airport_list():
    # Gibt Dictionary {lesbarer Name: IATA-Code} für Dropdown-Menüs zurück
    # Dict Comprehension: k = IATA-Code, v = Koordinaten-Dict mit "name"-Schlüssel
    # Konzept Dict Comprehension aus Unterricht; .items()-Iteration via Claude
    return {v["name"]: k for k, v in AIRPORT_COORDS.items()}
