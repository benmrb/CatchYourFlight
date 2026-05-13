"""
utils/dashboard_data.py
 
Liefert aggregierte Verspätungsstatistiken für die drei Dashboard-Diagramme.
Die Werte stammen aus dem verarbeiteten BTS-Datensatz (processed_flights.csv)
und sind als hartcodierte DataFrames hinterlegt, um Ladezeiten zu minimieren.
 
Datenquelle:
  Bureau of Transportation Statistics (BTS) —
  US-Inlandsflüge 2015, 16 Flughäfen (ATL, BOS, DEN, DFW, DTW,
  EWR, IAH, JFK, LAS, LAX, MCO, MSP, ORD, PHX, SEA, SFO)
 
Abhängigkeiten:
  - pandas
 
Autoren: Ben Marbacher, Sára Jankovičová
Datum:   Mai 2026
 
Quellen:
- CS-Unterricht: pandas DataFrame-Grundlagen (pd.DataFrame(), Spalten,
  Sortierung), Dictionaries, Listen, Funktionsdefinitionen mit
  Rückgabewerten, Typannotationen (->)
- Claude (Sonnet 4): Idee der hartcodierten Aggregations-DataFrames als
  Performance-Optimierung, .sort_values() / .reset_index(drop=True),
  list(data.items()) zum Umwandeln eines Dicts in DataFrame-Zeilen
"""
 
# ── Import ────────────────────────────────────────────────────────────────────
import pandas as pd             # Für DataFrame-Erstellung und Sortierung
 
 
# ── Funktion 1: Verspätungsrate nach Tageszeit ────────────────────────────────
def get_delay_by_hour() -> pd.DataFrame:
    """Verspätungsrate nach Abflugstunde aus dem echten Datensatz."""
    # Gibt einen DataFrame mit 24 Zeilen zurück (Stunde 0–23 und Verspätungsrate in %)
    # Die delay_pct-Werte wurden aus dem BTS-Datensatz voraggregiert
    # Reihenfolge entspricht den Stunden 0:00–23:00
    # Quelle: Claude – Idee der vorausberechneten hartcodierten Werte via Claude;
    #         pd.DataFrame()-Konzept aus Unterricht
    return pd.DataFrame({
        "hour": list(range(24)),        # [0, 1, 2, ..., 23] — Stunden des Tages
        "delay_pct": [
            18.7, 16.6, 24.0, 21.0, 13.0, 6.4,   # 00:00–05:00 (Nacht / früher Morgen)
            7.8, 10.4, 11.9, 14.9, 16.6, 18.8,   # 06:00–11:00 (Morgen)
            19.4, 20.4, 22.7, 23.5, 24.7, 25.9,  # 12:00–17:00 (Mittag / Nachmittag)
            29.1, 27.9, 29.3, 27.2, 25.2, 21.9,  # 18:00–23:00 (Abend / Nacht)
        ],
    })
 
 
# ── Funktion 2: Verspätungsrate nach Wochentag ────────────────────────────────
def get_delay_by_weekday() -> pd.DataFrame:
    """Verspätungsrate nach Wochentag. Montag höchste Rate, Samstag niedrigste."""
    # Gibt einen DataFrame mit 7 Zeilen zurück (Mon–Sun)
    # day_order dient der korrekten Sortierung im Diagramm (Montag = 1)
    # Quelle: pd.DataFrame()-Konzept aus Unterricht; Struktur via Claude
    return pd.DataFrame({
        "day":       ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],  # Tageskürzel
        "day_order": [1,      2,     3,     4,     5,     6,     7],     # Sortierschlüssel
        "delay_pct": [22.1,   20.2,  19.8,  21.6,  20.4,  17.8,  20.7], # Rate in %
    })
 
 
# ── Funktion 3: Verspätungsrate nach Airline ──────────────────────────────────
def get_delay_by_airline() -> pd.DataFrame:
    """Verspätungsrate nach Airline. Nur die 10 unterstützten Airlines."""
    # Dictionary: Airline-Name → Verspätungsrate in %
    # Nur die 10 im Modell unterstützten Airlines sind enthalten
    # Quelle: Dictionary-Konzept aus Unterricht; Werte aus BTS-Datensatz
    data = {
        "Hawaiian Airlines":        7.9,   # Pünktlichste Airline
        "Alaska Airlines":         11.9,
        "Delta Air Lines":         15.9,
        "American Airlines":       18.9,
        "SkyWest Airlines":        19.8,
        "JetBlue Airways":         22.0,
        "American Eagle Airlines": 22.4,
        "Frontier Airlines":       24.0,
        "Southwest Airlines":      24.6,
        "United Air Lines":        26.3,   # Meiste Verspätungen
    }
 
    # Dictionary in DataFrame umwandeln:
    # list(data.items()) erzeugt Liste von (Name, Rate)-Tupeln → zwei Spalten
    # Quelle: Claude – list(data.items()) und columns-Parameter via Claude;
    #         pd.DataFrame()-Grundkonzept aus Unterricht
    df = pd.DataFrame(list(data.items()), columns=["airline", "delay_pct"])
 
    # Nach Verspätungsrate aufsteigend sortieren (pünktlichste Airline zuerst)
    # reset_index(drop=True) setzt den Index nach Sortierung neu (0, 1, 2, ...)
    # Quelle: Claude – .sort_values() und .reset_index(drop=True) via Claude
    return df.sort_values("delay_pct", ascending=True).reset_index(drop=True)
