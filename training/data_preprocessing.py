"""
training/data_preprocessing.py

Datenvorbereitung für das CatchYourFlight ML-Modell.
Lädt die drei Kaggle-Rohdateien (flights.csv, airlines.csv, airports.csv),
filtert auf die 16 Zielflughäfen, bereinigt die Daten, berechnet Features
und ergänzt stündliche Wetterdaten von Open-Meteo.
Das fertige Dataset wird als processed_flights.csv gespeichert.

Abhängigkeiten:
- data/flights.csv        (Kaggle: 2015 Flight Delays and Cancellations)
- data/airlines.csv       (Kaggle: Airline IATA-Codes und Namen)
- data/airports.csv       (Kaggle: Flughafencodes, Städte und Koordinaten)
- Open-Meteo Archive API  (stündliche Wetterdaten 2015)

Autoren: Benjamin Marbacher
Datum:   Mai 2026

Quellen:
- CS-Unterricht: pandas DataFrame-Grundlagen (pd.read_csv, Spaltenfilter,
  dropna, Boolean Masking, pd.cut, pd.to_datetime, .merge(), .map(),
  .fillna(), .drop()), Dictionaries, for-Schleifen, f-Strings,
  Funktionsdefinitionen mit Parametern und Rückgabewerten,
  try/except-Fehlerbehandlung (Grundkonzept)
- Claude (Sonnet 4): requests-Bibliothek (HTTP-Anfragen an Open-Meteo API),
  pd.concat() für DataFrame-Zusammenführung, time.sleep() für API-Throttling,
  .str.zfill() und .str[:2] für Stundenextraktion aus vierstelligen Zeiten,
  .dt.strftime() für Datumsformatierung, gesamte Datei-Architektur und
  Ablauflogik des Preprocessing-Pipelines
"""

# ── Imports ───────────────────────────────────────────────────────────────────
import pandas as pd     # DataFrame-Operationen (im Unterricht behandelt)
import requests         # HTTP-Anfragen an Open-Meteo API
                        # Quelle: Claude – requests-Bibliothek nicht im Unterricht
import os               # Für os.makedirs() — Ordner erstellen falls nicht vorhanden
import time             # Für time.sleep() — Pause zwischen API-Anfragen
                        # Quelle: Claude – time.sleep() nicht im Unterricht

# ── Konfiguration ─────────────────────────────────────────────────────────────
FLIGHTS_CSV  = "data/flights.csv"    # Kaggle-Rohdatei: alle US-Flüge 2015
AIRLINES_CSV = "data/airlines.csv"   # Kaggle-Hilfstabelle: Airline-Namen
AIRPORTS_CSV = "data/airports.csv"   # Kaggle-Hilfstabelle: Flughafennamen und Städte

# Verspätungsschwelle: ab 15 Minuten gilt ein Flug als verspätet (BTS-Standard)
DELAY_THRESHOLD = 15

# Liste der 16 Zielflughäfen — nur Abflüge von diesen werden berücksichtigt
TARGET_AIRPORTS = [
    "ATL", "ORD", "DFW", "DEN", "LAX",
    "SFO", "PHX", "IAH", "LAS", "MSP",
    "MCO", "SEA", "DTW", "BOS", "EWR", "JFK"
]

# GPS-Koordinaten der 16 Flughäfen für die Open-Meteo Wetter-API
# Quelle: Claude – Koordinaten und Datenstruktur vollständig via Claude
AIRPORT_COORDS = {
    "ATL": {"lat": 33.6407,  "lon": -84.4277},
    "ORD": {"lat": 41.9742,  "lon": -87.9073},
    "DFW": {"lat": 32.8998,  "lon": -97.0403},
    "DEN": {"lat": 39.8561,  "lon": -104.6737},
    "LAX": {"lat": 33.9425,  "lon": -118.4081},
    "SFO": {"lat": 37.6213,  "lon": -122.3790},
    "PHX": {"lat": 33.4373,  "lon": -112.0078},
    "IAH": {"lat": 29.9902,  "lon": -95.3368},
    "LAS": {"lat": 36.0840,  "lon": -115.1537},
    "MSP": {"lat": 44.8848,  "lon": -93.2223},
    "MCO": {"lat": 28.4294,  "lon": -81.3089},
    "SEA": {"lat": 47.4502,  "lon": -122.3088},
    "DTW": {"lat": 42.2162,  "lon": -83.3554},
    "BOS": {"lat": 42.3656,  "lon": -71.0096},
    "EWR": {"lat": 40.6895,  "lon": -74.1745},
    "JFK": {"lat": 40.6413,  "lon": -73.7781},
}


# ── Hilfstabellen laden ───────────────────────────────────────────────────────
def load_lookup_tables():
    """Lädt Airline- und Flughafen-Hilfstabellen als Dictionaries."""
    print("Lade Hilfstabellen...")

    # Airlines laden und als Dictionary {IATA-Code: Name} speichern
    # zip() kombiniert zwei Listen zu Paaren — Konzept aus Unterricht
    airlines     = pd.read_csv(AIRLINES_CSV)
    airline_dict = dict(zip(airlines["IATA_CODE"], airlines["AIRLINE"]))

    # Flughäfen laden: Dictionary für Namen und Städte
    airports     = pd.read_csv(AIRPORTS_CSV)
    airport_dict = dict(zip(airports["IATA_CODE"], airports["AIRPORT"]))
    city_dict    = dict(zip(airports["IATA_CODE"], airports["CITY"]))

    print(f"  {len(airline_dict)} Airlines, {len(airport_dict)} Flughäfen geladen")
    return airline_dict, airport_dict, city_dict


# ── Flugdaten laden ───────────────────────────────────────────────────────────
def load_flight_data() -> pd.DataFrame:
    """
    Lädt flights.csv (5.8 Mio Zeilen), filtert auf die 16 Zielflughäfen
    und entfernt stornierte Flüge sowie Einträge ohne Verspätungsangabe.
    """
    print("\nLade Flugdaten (2-3 Minuten)...")

    # Nur benötigte Spalten laden um Arbeitsspeicher zu sparen
    # Quelle: Claude – usecols-Parameter für selektives Laden via Claude
    cols = [
        "YEAR", "MONTH", "DAY", "DAY_OF_WEEK",
        "AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT",
        "SCHEDULED_DEPARTURE", "DEPARTURE_DELAY",
        "DISTANCE", "CANCELLED",
    ]
    df = pd.read_csv(FLIGHTS_CSV, usecols=cols, low_memory=False)
    print(f"  Geladen: {len(df):,} Flüge total")

    # Auf 16 Zielflughäfen filtern (Boolean Masking — im Unterricht behandelt)
    df = df[df["ORIGIN_AIRPORT"].isin(TARGET_AIRPORTS)]
    # Stornierte Flüge entfernen (CANCELLED == 0 = nicht storniert)
    df = df[df["CANCELLED"] == 0]
    # Einträge ohne Verspätungsangabe entfernen
    df = df.dropna(subset=["DEPARTURE_DELAY"])

    print(f"  Nach Filter: {len(df):,} Flüge")
    return df


# ── Features berechnen ────────────────────────────────────────────────────────
def engineer_features(df: pd.DataFrame, airline_dict: dict, city_dict: dict) -> pd.DataFrame:
    """
    Berechnet alle zusätzlichen Features die das ML-Modell benötigt:
    Abflugstunde, Datum, Airline-Name, Distanz in km, Delay-Label und Kategorie.
    """
    print("\nErstelle Features...")

    # Abflugstunde aus der vierstelligen HHMM-Zeit extrahieren
    # z.B. "830" → "0830" → "08" → 8
    # Quelle: Claude – .str.zfill() und .str[:2]-Slicing via Claude
    df["DEP_HOUR"] = (
        df["SCHEDULED_DEPARTURE"]
        .astype(str).str.zfill(4).str[:2].astype(int)
    )

    # Datum aus Jahr/Monat/Tag-Spalten zusammenbauen
    # Quelle: Claude – pd.to_datetime() mit rename und .dt.strftime() via Claude
    df["DATE"] = pd.to_datetime(
        df[["YEAR", "MONTH", "DAY"]]
        .rename(columns={"YEAR": "year", "MONTH": "month", "DAY": "day"})
    ).dt.strftime("%Y-%m-%d")

    # Lesbare Namen aus Dictionaries hinzufügen (.map() — Konzept aus Unterricht)
    df["AIRLINE_NAME"]     = df["AIRLINE"].map(airline_dict).fillna(df["AIRLINE"])
    df["DESTINATION_CITY"] = df["DESTINATION_AIRPORT"].map(city_dict).fillna(df["DESTINATION_AIRPORT"])

    # Distanz von Meilen in Kilometer umrechnen (1 Meile = 1.60934 km)
    df["DISTANCE_KM"] = (df["DISTANCE"] * 1.60934).round(0)

    # Binäres Delay-Label: 1 = verspätet (≥15 Min), 0 = pünktlich
    # Boolean-Ausdruck als Integer (True/False → 1/0) — Konzept aus Unterricht
    df["IS_DELAYED"] = (df["DEPARTURE_DELAY"] >= DELAY_THRESHOLD).astype(int)

    # Verspätungskategorie für Multiclass-Klassifikation
    # pd.cut() teilt numerische Werte in Kategorien ein
    # Quelle: Claude – pd.cut() mit bins und labels nicht im Unterricht
    df["DELAY_CATEGORY"] = pd.cut(
        df["DEPARTURE_DELAY"],
        bins=[-float("inf"), 15, 30, 45, 60, 90, float("inf")],
        labels=["No Delay", "15-30 min", "30-45 min", "45-60 min", "60-90 min", "90+ min"]
    )

    print(f"  Verspätungsrate: {df['IS_DELAYED'].mean():.1%}")
    return df


# ── Stündliche Wetterdaten laden ──────────────────────────────────────────────
def fetch_hourly_weather(year: int = 2015) -> pd.DataFrame:
    """
    Lädt stündliche Wetterdaten für alle 16 Flughäfen des ganzen Jahres 2015
    von der Open-Meteo Archive API. Jeder Flughafen wird einzeln abgefragt.
    """
    print("\nLade stündliche Wetterdaten von Open-Meteo...")
    all_weather = []   # Liste für DataFrames aller Flughäfen

    # Für jeden Flughafen einen separaten API-Request machen
    for airport_code, coords in AIRPORT_COORDS.items():
        print(f"  Hole Wetter für {airport_code}...")

        url = "https://archive-api.open-meteo.com/v1/archive"
        # API-Parameter: Koordinaten, Zeitraum und gewünschte Wettervariablen
        # Quelle: Claude – Open-Meteo API-Parametrisierung vollständig via Claude
        params = {
            "latitude":        coords["lat"],
            "longitude":       coords["lon"],
            "start_date":      f"{year}-01-01",
            "end_date":        f"{year}-12-31",
            "hourly":          ["temperature_2m", "precipitation", "snowfall",
                                "windspeed_10m", "cloudcover"],
            "timezone":        "America/New_York",
            "wind_speed_unit": "ms",            # m/s statt km/h
        }

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()         # Exception bei HTTP-Fehler
            data = response.json()["hourly"]    # Stündliche Daten aus JSON extrahieren

            # Zeitstempel aus API-Antwort in Datum und Stunde aufteilen
            # Quelle: Claude – pd.to_datetime() und .hour-Attribut via Claude
            times      = pd.to_datetime(data["time"])
            weather_df = pd.DataFrame({
                "DATE":           times.strftime("%Y-%m-%d"),  # Datum als String
                "DEP_HOUR":       times.hour,                  # Stunde (0–23)
                "ORIGIN_AIRPORT": airport_code,
                "TEMP":           data["temperature_2m"],      # Temperatur in °C
                "PRCP_H":         data["precipitation"],       # Niederschlag in mm/h
                "SNOW_H":         data["snowfall"],            # Schneefall in mm/h
                "WIND":           data["windspeed_10m"],       # Wind in m/s
                "CLOUD":          data["cloudcover"],          # Bewölkung in %
            })
            all_weather.append(weather_df)

            # Kurze Pause um die API nicht zu überlasten (Rate Limiting)
            # Quelle: Claude – time.sleep() für API-Throttling via Claude
            time.sleep(0.5)

        except Exception as e:
            print(f"  WARNUNG: {airport_code}: {e}")

    # Alle Flughafen-DataFrames zu einem kombinieren
    # pd.concat() stapelt mehrere DataFrames übereinander
    # Quelle: Claude – pd.concat() via Claude
    combined = pd.concat(all_weather, ignore_index=True)
    print(f"  {len(combined):,} Wetter-Einträge geladen")
    return combined


# ── Flug- und Wetterdaten zusammenführen ──────────────────────────────────────
def merge_hourly_weather(flights_df, weather_df):
    """
    Fügt die stündlichen Wetterdaten zu den Flugdaten hinzu.
    Jeder Flug erhält das Wetter seines Abflughafens zur Abflugstunde.
    """
    if weather_df.empty:
        return flights_df

    print("\nKombiniere Flug- und Wetterdaten...")

    # Left Join: Flugdaten bleiben erhalten, Wetterdaten werden hinzugefügt
    # Join-Schlüssel: Datum + Stunde + Flughafen (drei-spaltige Verknüpfung)
    # Quelle: Claude – .merge() mit mehreren Keys und how="left" via Claude
    merged = flights_df.merge(
        weather_df[["DATE", "DEP_HOUR", "ORIGIN_AIRPORT",
                    "TEMP", "PRCP_H", "SNOW_H", "WIND", "CLOUD"]],
        on=["DATE", "DEP_HOUR", "ORIGIN_AIRPORT"],
        how="left"
    )

    # Fehlende Wetterwerte mit 0 füllen (falls API-Daten für eine Stunde fehlen)
    for col in ["TEMP", "PRCP_H", "SNOW_H", "WIND", "CLOUD"]:
        merged[col] = merged[col].fillna(0)

    print(f"  Fertig: {len(merged):,} Einträge")
    return merged


# ── Hauptfunktion: Gesamtes Preprocessing ────────────────────────────────────
def prepare_dataset(use_weather: bool = True) -> pd.DataFrame:
    """
    Führt den gesamten Preprocessing-Pipeline aus:
    Laden → Filtern → Features berechnen → Wetter hinzufügen → Speichern.
    """
    # Schritt 1: Hilfstabellen laden
    airline_dict, airport_dict, city_dict = load_lookup_tables()

    # Schritt 2: Rohdaten laden und filtern
    df = load_flight_data()

    # Schritt 3: Features berechnen
    df = engineer_features(df, airline_dict, city_dict)

    # Schritt 4: Wetterdaten hinzufügen (optional)
    if use_weather:
        weather = fetch_hourly_weather(year=2015)
        df = merge_hourly_weather(df, weather)

    # Schritt 5: Nicht mehr benötigte Rohdaten-Spalten entfernen
    drop_cols = ["YEAR", "DAY", "CANCELLED", "SCHEDULED_DEPARTURE", "DISTANCE"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Schritt 6: Fertiges Dataset als CSV speichern
    os.makedirs("data", exist_ok=True)    # Ordner erstellen falls nicht vorhanden
    df.to_csv("data/processed_flights.csv", index=False)
    print(f"\nGespeichert: {len(df):,} Flüge, {len(df.columns)} Spalten")
    return df


# ── Einstiegspunkt ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Wird nur ausgeführt wenn das Skript direkt gestartet wird
    # (nicht wenn es von einem anderen Skript importiert wird)
    prepare_dataset(use_weather=True)
