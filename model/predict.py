"""
model/predict.py
 
Vorhersagemodul für das flight-delay-project.
Lädt trainierte ML-Modelle und berechnet für einen gegebenen Flug
(Airline, Flughafen, Datum, Abflugzeit, Wetterdaten) die
Wahrscheinlichkeit einer Verspätung sowie die wahrscheinlichste
Verspätungskategorie.
 
Abhängigkeiten:
- binary_model.pkl       (vortrainiertes Binär-Klassifikationsmodell)
- multiclass_model.pkl   (vortrainiertes Multi-Class-Klassifikationsmodell)
- encoders.pkl           (Label-Encoder für kategorische Spalten)
- feature_list.pkl       (Liste der erwarteten Feature-Spalten)
 
Autoren: Ben Marbacher
Datum:   Mai 2026
 
Quellen:
- CS-Unterricht: ML-Grundkonzepte (Supervised Learning, Klassifikation,
  Binary vs. Multi-Class, Labels, Features, Instanzen, train_test_split),
  pandas DataFrame-Operationen, Boolean Masking, Iteration mit for-Schleifen,
  Dictionaries, Funktionen, if/elif/else, math-Bibliothek (Unterricht Teil 1–4)
- Claude (Sonnet 4): Haversine-Formel, joblib-Modell-Laden/Speichern,
  predict_proba()-Methode, LabelEncoder-Anwendung auf unbekannte Werte,
  Strukturierung des Rückgabe-Dictionaries, Wetter-Feature-Aufbereitung,
  historische Airline-Delay-Raten, gesamte Datei-Architektur
"""
 
# ── Imports ───────────────────────────────────────────────────────────────────
import pandas as pd          # Für DataFrame-Operationen (im Unterricht behandelt)
import joblib                # Zum Laden gespeicherter ML-Modelle (.pkl-Dateien)
                             # Quelle: Claude – joblib wurde im Unterricht nicht behandelt
import os                    # Für Dateipfad-Prüfungen (os.path.exists)
import math                  # Für mathematische Funktionen (sin, cos, sqrt, radians)
                             # Grundkonzept Unterricht; Haversine-Formel via Claude
from datetime import datetime  # Zum Parsen und Verarbeiten von Datumsobjekten
                               # Quelle: Claude – datetime-Modul nicht im Unterricht
 
# ── Konfiguration ─────────────────────────────────────────────────────────────
MODEL_DIR = "models"         # Ordnerpfad, in dem die .pkl-Modelldateien liegen
 
# Dictionary: Airline-Kürzel → vollständiger Airline-Name
# Dient der lesbaren Anzeige in der Streamlit-UI
# Quelle: Claude – Dictionary-Konzept im Unterricht, Inhalt (IATA-Codes) via Claude
AIRLINE_NAMES = {
    "AA": "American Airlines",
    "AS": "Alaska Airlines",
    "B6": "JetBlue Airways",
    "DL": "Delta Air Lines",
    "F9": "Frontier Airlines",
    "HA": "Hawaiian Airlines",
    "MQ": "Envoy Air (American Eagle)",
    "OO": "SkyWest Airlines",
    "UA": "United Air Lines",
    "WN": "Southwest Airlines",
}
 
# Dictionary: IATA-Flughafenkürzel → lesbarer Flughafenname mit Code
# Quelle: Claude – Dictionary-Konzept im Unterricht, Inhalte (16 US-Airports) via Claude
AIRPORT_NAMES = {
    "ATL": "Atlanta (ATL)",
    "ORD": "Chicago O'Hare (ORD)",
    "DFW": "Dallas Fort Worth (DFW)",
    "DEN": "Denver (DEN)",
    "LAX": "Los Angeles (LAX)",
    "SFO": "San Francisco (SFO)",
    "PHX": "Phoenix (PHX)",
    "IAH": "Houston (IAH)",
    "LAS": "Las Vegas (LAS)",
    "MSP": "Minneapolis (MSP)",
    "MCO": "Orlando (MCO)",
    "SEA": "Seattle (SEA)",
    "DTW": "Detroit (DTW)",
    "BOS": "Boston (BOS)",
    "EWR": "Newark (EWR)",
    "JFK": "New York JFK (JFK)",
}
 
# Schwellenwert: Verspätungswahrscheinlichkeit ab der ein Flug als "verspätet" gilt
# Quelle: Claude – Konzept des Klassifikations-Schwellenwerts aus Unterricht (Klassifikation),
# konkreter Wert 0.33 via Claude basierend auf Modellevaluation
DELAY_BENCHMARK = 0.33
 
# Dictionary: IATA-Kürzel → GPS-Koordinaten (Breitengrad, Längengrad) jedes Flughafens
# Wird für die Haversine-Distanzberechnung benötigt
# Quelle: Claude – Koordinaten und Verwendungszweck vollständig via Claude
AIRPORT_COORDS = {
    "ATL": (33.6407, -84.4277),
    "ORD": (41.9742, -87.9073),
    "DFW": (32.8998, -97.0403),
    "DEN": (39.8561, -104.6737),
    "LAX": (33.9425, -118.4081),
    "SFO": (37.6213, -122.3790),
    "PHX": (33.4373, -112.0078),
    "IAH": (29.9902, -95.3368),
    "LAS": (36.0840, -115.1537),
    "MSP": (44.8848, -93.2223),
    "MCO": (28.4294, -81.3089),
    "SEA": (47.4502, -122.3088),
    "DTW": (42.2162, -83.3554),
    "BOS": (42.3656, -71.0096),
    "EWR": (40.6895, -74.1745),
    "JFK": (40.6413, -73.7781),
}
 
 
# ── Hilfsfunktion: Flugdistanz berechnen ──────────────────────────────────────
def _haversine(origin, destination):
    # Berechnet die Luftlinien-Distanz in km zwischen zwei Flughäfen
    # anhand der Haversine-Formel (Kugelgeometrie)
    # Quelle: Claude – Haversine-Formel und trigonometrische Umsetzung vollständig via Claude
 
    # Falls einer der Flughäfen nicht in AIRPORT_COORDS vorhanden ist: Standardwert zurückgeben
    if origin not in AIRPORT_COORDS or destination not in AIRPORT_COORDS:
        return 2500.0                               # Fallback-Distanz in km
 
    # Koordinaten beider Flughäfen von Grad in Bogenmass (Radiant) umrechnen
    # math.radians() rechnet Grad → Radiant (benötigt für trigonometrische Funktionen)
    lat1 = math.radians(AIRPORT_COORDS[origin][0])
    lon1 = math.radians(AIRPORT_COORDS[origin][1])
    lat2 = math.radians(AIRPORT_COORDS[destination][0])
    lon2 = math.radians(AIRPORT_COORDS[destination][1])
 
    # Haversine-Formel: berechnet den Zwischenwert 'a' (Quadrat des halben Sehnenabstands)
    # math.sin(), math.cos(), math.sqrt(), math.asin() → Trigonometrie-Funktionen aus math
    # Quelle: Claude – Formel und Implementierung vollständig via Claude
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
 
    # Erdradius 6371 km × 2 × arcsin(√a) = Grosskreis-Distanz in km, gerundet auf ganze km
    return round(6371 * 2 * math.asin(math.sqrt(a)), 0)
 
 
# ── Modelle laden ─────────────────────────────────────────────────────────────
def load_models():
    # Lädt alle vier benötigten .pkl-Dateien aus MODEL_DIR
    # Gibt (None, None, None, None) zurück, falls eine Datei fehlt
    # Quelle: Claude – joblib.load() und .pkl-Dateiverwaltung nicht im Unterricht
 
    # Liste der benötigten Dateien; jede muss vorhanden sein
    required = ["binary_model.pkl", "multiclass_model.pkl", "encoders.pkl", "feature_list.pkl"]
 
    # Schleife prüft mit os.path.exists(), ob jede Datei auf dem Dateisystem existiert
    for f in required:
        if not os.path.exists(f"{MODEL_DIR}/{f}"):
            return None, None, None, None           # Frühzeitiger Abbruch wenn Datei fehlt
 
    # Alle vier Dateien laden und als Tupel zurückgeben
    # joblib.load() deserialisiert ein gespeichertes Python-Objekt (Modell, Encoder, Liste)
    return (
        joblib.load(f"{MODEL_DIR}/binary_model.pkl"),      # Binär-Klassifikator (verspätet / nicht)
        joblib.load(f"{MODEL_DIR}/multiclass_model.pkl"),  # Multi-Class-Klassifikator (Kategorie)
        joblib.load(f"{MODEL_DIR}/encoders.pkl"),          # LabelEncoder-Objekte pro kategorialer Spalte
        joblib.load(f"{MODEL_DIR}/feature_list.pkl"),      # Erwartete Feature-Spaltenliste des Modells
    )
 
 
# Modelle beim Modulstart einmalig laden und in globalen Variablen speichern
# Quelle: Claude – Modul-Level-Initialisierung via Claude
_binary_model, _multi_model, _encoders, _feature_list = load_models()
 
 
# ── Hilfsfunktion: Wetterdaten für eine bestimmte Stunde abrufen ──────────────
def _get_weather_at_hour(weather_df, dep_hour):
    # Filtert aus einem Wetter-DataFrame die Zeile mit der passenden Abflugstunde
    # Falls keine passende Stunde vorhanden: erste Zeile als Fallback verwenden
    # Quelle: Claude – Struktur und Wetter-Feature-Namen vollständig via Claude
 
    # Boolean Mask: filtert weather_df nach Zeilen, wo "hour" == dep_hour (im Unterricht behandelt)
    row = weather_df[weather_df["hour"] == dep_hour]
 
    # Falls mindestens eine Zeile gefunden: erste nehmen; sonst Fallback auf Zeile 0
    row = row.iloc[0] if not row.empty else weather_df.iloc[0]
 
    # Wetter-Features als Dictionary zurückgeben; Einheiten und Fallback-Werte via Claude
    # round() rundet auf 1 bzw. 2 Dezimalstellen für konsistente Feature-Werte
    return {
        "TEMP":   round(float(row["temperature"] or 20.0), 1),    # Temperatur in °C
        "PRCP_H": round(float(row["precipitation"] or 0.0), 2),   # Niederschlag in mm/h
        "SNOW_H": round(float(row["snowfall"] or 0.0), 2),        # Schneefall in mm/h
        "WIND":   round(float(row["windspeed"] / 3.6 if row["windspeed"] else 5.0), 2),  # km/h → m/s
        "CLOUD":  round(float(row["cloudcover"] or 50.0), 1),     # Wolkenbedeckung in %
    }
 
 
# ── Hauptfunktion: Verspätungsvorhersage ──────────────────────────────────────
def predict_delay(airline, origin, destination, flight_date, dep_hour, weather_df):
    # Erstellt eine ML-Vorhersage für einen Flug und gibt ein Ergebnis-Dictionary zurück
    # Parameter:
    #   airline      – IATA-Airline-Code (z.B. "DL")
    #   origin       – IATA-Abflughafen-Code (z.B. "ATL")
    #   destination  – IATA-Zielflughafen-Code (z.B. "LAX")
    #   flight_date  – Datum als String "YYYY-MM-DD" oder datetime-Objekt
    #   dep_hour     – Abflugstunde als Integer (0–23)
    #   weather_df   – DataFrame mit stündlichen Wetterdaten
    # Quelle: Claude – gesamte Funktionsarchitektur und Rückgabestruktur via Claude
 
    # Sicherheitsprüfung: wenn Modell nicht geladen, Fehlermeldung zurückgeben
    if _binary_model is None:
        return {"error": "Modell nicht geladen."}
 
    # Datum in datetime-Objekt umwandeln (falls als String übergeben)
    # Quelle: Claude – datetime.strptime() und datetime.combine() nicht im Unterricht
    if isinstance(flight_date, str):
        dt = datetime.strptime(flight_date, "%Y-%m-%d")     # String → datetime parsen
    else:
        dt = datetime.combine(flight_date, datetime.min.time())  # date → datetime
 
    # Aus dem Datum Monat und Wochentag extrahieren (Features für das Modell)
    # isoweekday(): 1 = Montag, 7 = Sonntag (ISO-Standard)
    month = dt.month
    day_of_week = dt.isoweekday()
 
    # Wetterdaten und Distanz für die Abflugstunde berechnen
    weather = _get_weather_at_hour(weather_df, dep_hour)
    distance_km = _haversine(origin, destination)
 
    # Feature-Dictionary mit allen Eingabewerten für das Modell zusammenstellen
    # Entspricht den Spalten, auf denen das Modell trainiert wurde
    # Quelle: Claude – Feature-Auswahl und -Benennung vollständig via Claude
    input_data = {
        "MONTH":               month,          # Monat des Fluges (1–12)
        "DAY_OF_WEEK":         day_of_week,    # Wochentag (1 = Mo, 7 = So)
        "DEP_HOUR":            dep_hour,       # Abflugstunde (0–23)
        "AIRLINE":             airline,        # Airline-Code (kategorisch)
        "ORIGIN_AIRPORT":      origin,         # Abflughafen-Code (kategorisch)
        "DESTINATION_AIRPORT": destination,    # Zielflughafen-Code (kategorisch)
        "DISTANCE_KM":         distance_km,    # Flugdistanz in km (numerisch)
        "TEMP":                weather["TEMP"],   # Temperatur in °C
        "PRCP_H":              weather["PRCP_H"], # Niederschlag mm/h
        "SNOW_H":              weather["SNOW_H"], # Schneefall mm/h
        "WIND":                weather["WIND"],   # Windgeschwindigkeit m/s
        "CLOUD":               weather["CLOUD"],  # Wolkenbedeckung %
    }
 
    # Dictionary in einzeiligen DataFrame umwandeln (Modell erwartet DataFrame als Input)
    # Quelle: Claude – pd.DataFrame([dict]) als Eingabeformat für sklearn-Modelle via Claude
    df = pd.DataFrame([input_data])
 
    # Nur die Spalten behalten, die das Modell kennt (gemäss feature_list)
    # List Comprehension filtert Features; Boolean-Masking-ähnliches Konzept aus Unterricht
    df = df[[f for f in _feature_list if f in df.columns]]
 
    # Kategorische Spalten mit LabelEncoder kodieren (Text → Zahl für das Modell)
    # Quelle: Claude – LabelEncoder, encoder.classes_, encoder.transform() via Claude
    for col, encoder in _encoders.items():
        if col in df.columns:
            # Unbekannte Werte (nicht im Training gesehen) durch erste bekannte Klasse ersetzen
            known = set(encoder.classes_)
            df[col] = df[col].apply(lambda x: x if x in known else encoder.classes_[0])
            # Spalte transformieren: Text-Label → numerischer Code
            df[col] = encoder.transform(df[col].astype(str))
 
    # Binäre Vorhersage: Wahrscheinlichkeit für "verspätet" (Klasse 1, Index [0][1])
    # predict_proba() gibt Array [[prob_klasse0, prob_klasse1]] zurück
    # Quelle: Claude – predict_proba()-Methode nicht im Unterricht behandelt
    delay_prob = _binary_model.predict_proba(df)[0][1]
 
    # Multi-Class-Vorhersage: Wahrscheinlichkeit für jede Verspätungskategorie
    all_probs  = _multi_model.predict_proba(df)[0]
    categories = _multi_model._label_encoder.classes_  # Array der Kategorienamen
 
    # Nur Verspätungs-Kategorien (ohne "No Delay") für die Kategorie-Empfehlung verwenden
    # Dictionary Comprehension filtert Kategorien; Konzept (dict) aus Unterricht
    delay_only = {c: p for c, p in zip(categories, all_probs) if c != "No Delay"}
 
    # Wahrscheinlichste Verspätungskategorie bestimmen (max über Wahrscheinlichkeiten)
    best_cat   = max(delay_only, key=delay_only.get)
 
    # Risikolevel und Anzeigemodus anhand der Delay-Wahrscheinlichkeit bestimmen
    # Drei Stufen: Low / Medium / High basierend auf DELAY_BENCHMARK und 0.66
    # if/elif/else-Struktur aus Unterricht; Farbcodes und Schwellenwerte via Claude
    if delay_prob < DELAY_BENCHMARK:
        display_mode, display_category = "low_risk", "No Delay"
        risk_level, risk_color = "Low", "#10B981"     # Grün
    elif delay_prob < 0.66:
        display_mode, display_category = "show_category", best_cat
        risk_level, risk_color = "Medium", "#F59E0B"  # Orange
    else:
        display_mode, display_category = "show_category", best_cat
        risk_level, risk_color = "High", "#EF4444"    # Rot
 
    # ── Historische Verspätungsraten pro Airline (aus BTS 2015 Daten) ──────────
    # Diese Werte spiegeln die tatsächliche Pünktlichkeit der Airline wider,
    # unabhängig von der ML-Modell-Ausgabe
    # Quelle: Claude – historische Raten und Kategorisierung vollständig via Claude
    AIRLINE_DELAY_RATES = {
        "HA": 7.9,   # Hawaiian Airlines   → sehr pünktlich
        "AS": 11.9,  # Alaska Airlines     → pünktlich
        "DL": 15.9,  # Delta Air Lines     → durchschnittlich
        "AA": 18.9,  # American Airlines   → durchschnittlich
        "OO": 19.8,  # SkyWest Airlines    → durchschnittlich
        "B6": 22.0,  # JetBlue Airways     → hoch
        "MQ": 22.4,  # Envoy Air           → hoch
        "F9": 24.0,  # Frontier Airlines   → hoch
        "WN": 24.6,  # Southwest Airlines  → hoch
        "UA": 26.3,  # United Air Lines    → sehr hoch
    }
 
    # Liste der Einflussfaktoren (für die UI-Anzeige) aufbauen
    # Jeder Faktor hat ein Label und ein Impact-Level (low / medium / high)
    # Quelle: Claude – Faktor-Logik, Schwellenwerte und Struktur vollständig via Claude
    top_factors = []
 
    # Faktor 1: Abflugzeit (Stunde des Tages)
    # Abflugzeit: 03:00–08:00 ist am sichersten (LOW)
    # Späte Nacht (00:00–02:00) ist MEDIUM wegen akkumulierter Delays vom Vortag
    # Ab 15:00 steigt die Rate stark (43–59%) → HIGH
    if dep_hour >= 15:
        top_factors.append({"label": f"Late departure ({dep_hour:02d}:00)", "impact": "high"})
    elif 3 <= dep_hour < 9:
        top_factors.append({"label": f"Early departure ({dep_hour:02d}:00)", "impact": "low"})
    else:
        top_factors.append({"label": f"Midday departure ({dep_hour:02d}:00)", "impact": "medium"})
 
    # Faktor 2: Airline (historische Verspätungsrate)
    # Airline: basiert auf historischer Verspätungsrate der Airline
    # < 16% = low, 16–22% = medium, > 22% = high
    # dict.get() mit Fallback-Wert 20.0 für unbekannte Airlines
    airline_rate   = AIRLINE_DELAY_RATES.get(airline, 20.0)
    airline_impact = "low" if airline_rate < 16 else "high" if airline_rate >= 22 else "medium"
    top_factors.append({
        "label": AIRLINE_NAMES.get(airline, airline),  # Voller Name aus AIRLINE_NAMES
        "impact": airline_impact
    })
 
    # Faktor 3: Saison / Monat
    # Saison: Jun/Jul/Aug und Dez haben höchste Delay-Raten (42–45%)
    # Jan/Feb sind überraschend niedrig (20–26%) — wenig Verkehr nach den Feiertagen
    # Rest: medium (32–36%)
    if month in [6, 7, 8]:
        top_factors.append({"label": "Summer season (peak delays)", "impact": "high"})
    elif month == 12:
        top_factors.append({"label": "December (holidays + weather)", "impact": "high"})
    elif month in [1, 2]:
        top_factors.append({"label": "Post-holiday season (low traffic)", "impact": "low"})
    else:
        top_factors.append({"label": "Mid-season", "impact": "medium"})
 
    # Faktor 4: Wetter am Abflugort
    # Wetter: Regen hat laut Modell starken Effekt (36% → 41% bei 1mm Regen → HIGH)
    # Schnee zeigt im Modell überraschend wenig Effekt (Trainingsdaten-Limitation)
    if weather["SNOW_H"] > 0.5:
        top_factors.append({"label": "Snow at departure", "impact": "medium"})
    elif weather["SNOW_H"] > 0:
        top_factors.append({"label": "Light snow at departure", "impact": "medium"})
    elif weather["PRCP_H"] > 0.5:
        top_factors.append({"label": "Rain at departure", "impact": "high"})
    elif weather["PRCP_H"] > 0:
        top_factors.append({"label": "Light rain at departure", "impact": "medium"})
    else:
        top_factors.append({"label": "Favorable weather", "impact": "low"})
 
    # Faktor 5: Wochentag
    # Wochentag: Modell zeigt Montag als höchsten (40%), Samstag als niedrigsten (34%)
    # Dictionary bildet isoweekday-Zahl auf englischen Tagesnamen ab
    weekdays = {1:"Monday", 2:"Tuesday", 3:"Wednesday", 4:"Thursday",
                5:"Friday", 6:"Saturday", 7:"Sunday"}
    if day_of_week == 1:                        # Montag: höchste Delay-Rate laut Modell
        dow_impact = "high"
    elif day_of_week == 6:                      # Samstag: niedrigste Delay-Rate
        dow_impact = "low"
    else:                                       # Alle anderen Tage: mittel
        dow_impact = "medium"
    top_factors.append({
        "label": f"{weekdays.get(day_of_week, '')} flight",
        "impact": dow_impact
    })
 
    # Ergebnis-Dictionary mit allen relevanten Vorhersage-Werten zurückgeben
    # Quelle: Claude – Struktur und Schlüsselnamen des Rückgabe-Dicts vollständig via Claude
    return {
        "delay_probability":     round(float(delay_prob), 3),      # Wahrscheinlichkeit als Dezimalzahl
        "delay_probability_pct": f"{delay_prob:.0%}",              # Formatiert als Prozent-String
        "display_mode":          display_mode,                     # "low_risk" oder "show_category"
        "display_category":      display_category,                 # Wahrscheinlichste Verspätungskategorie
        "risk_level":            risk_level,                       # "Low" / "Medium" / "High"
        "risk_color":            risk_color,                       # Hex-Farbcode für UI-Darstellung
        "all_categories":        {c: round(float(p), 3) for c, p in zip(categories, all_probs)},
                                                                   # Alle Kategorien mit Wahrscheinlichkeit
        "weather_used":          weather,                          # Verwendete Wetterwerte (für Anzeige)
        "distance_km":           distance_km,                      # Berechnete Flugdistanz
        "is_likely_delayed":     delay_prob >= DELAY_BENCHMARK,    # Boolean: verspätet ja/nein
        "top_factors":           top_factors,                      # Liste der Einflussfaktoren für UI
    }
 
 
# ── Hilfsfunktionen für Dropdown-Optionen in der UI ───────────────────────────
 
def get_airline_options():
    # Gibt ein Dictionary {Airline-Name: Code} zurück, gefiltert auf aktive Airlines
    # Quelle: Claude – Filterung veralteter Codes und Encoder-Logik via Claude
 
    # Airlines, die 2015 existierten, aber heute nicht mehr aktiv sind
    DEFUNCT = {"NK", "US", "VX", "EV"}
 
    # Falls Encoder geladen: Airline-Codes aus Encoder-Klassen holen; sonst Fallback auf dict
    if _encoders and "AIRLINE" in _encoders:
        codes = sorted(_encoders["AIRLINE"].classes_.tolist())  # Alle bekannten Codes sortiert
    else:
        codes = list(AIRLINE_NAMES.keys())                      # Fallback: aus dem hartcodierten Dict
 
    # Dictionary Comprehension: nur aktive, bekannte Airlines zurückgeben
    # Filtert: nicht in DEFUNCT-Set und vorhanden in AIRLINE_NAMES
    return {
        AIRLINE_NAMES.get(c, c): c
        for c in codes
        if c not in DEFUNCT and c in AIRLINE_NAMES
    }
 
 
def get_destination_options(origin):
    # Gibt alle Zielflughäfen zurück, ausser dem gewählten Abflughafen (origin)
    # Quelle: Claude – Filterlogik und Dictionary Comprehension-Struktur via Claude
    return {name: code for code, name in AIRPORT_NAMES.items() if code != origin}
 
 
def get_airport_list():
    # Gibt alle verfügbaren Flughäfen als {Name: Code}-Dictionary zurück
    return {name: code for code, name in AIRPORT_NAMES.items()}
