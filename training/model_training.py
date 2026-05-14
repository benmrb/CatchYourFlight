"""
training/model_training.py

Trainiert zwei XGBoost-Klassifikationsmodelle für die Verspätungsvorhersage
und speichert sie als .pkl-Dateien für die Streamlit-App.

Modell 1 (Binary):     Verspätet ja/nein (ab 15 Min = Delay)
Modell 2 (Multiclass): Verspätungskategorie (No Delay / 15-30 / 30-45 /
                        45-60 / 60-90 / 90+ min)

Voraussetzungen:
    - data_preprocessing.py muss zuerst ausgeführt werden
    - data/processed_flights.csv muss vorhanden sein

Abhängigkeiten:
- data/processed_flights.csv    (Ausgabe von data_preprocessing.py)
- scikit-learn                  (LabelEncoder, train_test_split, Metriken)
- xgboost                       (XGBClassifier)
- joblib                        (Modelle als .pkl speichern)

Autoren: Benjamin Marbacher
Datum:   Mai 2026

Quellen:
- CS-Unterricht: ML-Grundkonzepte (Supervised Learning, Klassifikation,
  Binary vs. Multi-Class, Labels, Features, Instanzen, train_test_split,
  Accuracy, Classification Report), pandas DataFrame-Operationen,
  Dictionaries, Funktionsdefinitionen, if/elif/else, for-Schleifen,
  List Comprehension
- Claude (Sonnet 4): XGBoost-Modellparameter (n_estimators, max_depth,
  learning_rate, subsample, scale_pos_weight), joblib.dump() für Modell-
  Speicherung, LabelEncoder für Multiclass-Ziele, feature_importances_
  für Feature-Analyse, stratify-Parameter in train_test_split,
  gesamte Trainings-Architektur und Speicherstruktur
"""

# ── Imports ───────────────────────────────────────────────────────────────────
import pandas as pd                             # DataFrame-Operationen (im Unterricht behandelt)
from xgboost import XGBClassifier               # XGBoost-Klassifikator
                                                # Quelle: Claude – XGBoost nicht im Unterricht
from sklearn.model_selection import train_test_split
                                                # Daten in Training/Test aufteilen (im Unterricht)
from sklearn.preprocessing import LabelEncoder  # Text → Zahlen umwandeln (im Unterricht)
from sklearn.metrics import accuracy_score, classification_report
                                                # Modell-Bewertung (im Unterricht: Accuracy)
import joblib                                   # Modelle als .pkl-Dateien speichern
                                                # Quelle: Claude – joblib nicht im Unterricht
import os                                       # Für os.makedirs() — Ordner erstellen

# ── Konfiguration ─────────────────────────────────────────────────────────────
# Basis-Features: immer vorhanden, unabhängig vom Wetter
# Quelle: Claude – Feature-Auswahl und -Benennung via Claude
BASE_FEATURES = [
    "MONTH",               # Monat des Fluges (1–12)
    "DAY_OF_WEEK",         # Wochentag (1 = Montag, 7 = Sonntag)
    "DEP_HOUR",            # Abflugstunde (0–23)
    "AIRLINE",             # Airline-Code (kategorisch)
    "ORIGIN_AIRPORT",      # Abflughafen-Code (kategorisch)
    "DESTINATION_AIRPORT", # Zielflughafen-Code (kategorisch)
    "DISTANCE_KM",         # Flugdistanz in Kilometer (numerisch)
]

# Wetter-Features: stündliche Wetterdaten am Abflugort
WEATHER_FEATURES = [
    "TEMP",    # Temperatur zur Abflugzeit in °C
    "PRCP_H",  # Niederschlag zur Abflugzeit in mm/h
    "SNOW_H",  # Schneefall zur Abflugzeit in mm/h
    "WIND",    # Windgeschwindigkeit zur Abflugzeit in m/s
    "CLOUD",   # Bewölkung zur Abflugzeit in %
]

MODEL_DIR = "models"   # Ordner für die gespeicherten Modelle


# ── Features vorbereiten ──────────────────────────────────────────────────────
def prepare_features(df: pd.DataFrame, use_weather: bool = True):
    """
    Wählt die relevanten Feature-Spalten aus und wandelt kategorische
    Text-Spalten (Airline, Flughäfen) mit LabelEncoder in Zahlen um.
    Gibt X (Feature-Matrix), Encoder-Dictionary und Feature-Liste zurück.
    """
    # Feature-Liste zusammenstellen (Basis + optional Wetter)
    features = BASE_FEATURES.copy()
    if use_weather:
        # Nur Wetter-Features hinzufügen die im DataFrame vorhanden sind
        features += [f for f in WEATHER_FEATURES if f in df.columns]

    # Nochmals sicherstellen dass alle Spalten vorhanden sind
    # List Comprehension — Konzept aus Unterricht
    features = [f for f in features if f in df.columns]

    # Feature-Matrix X aus DataFrame extrahieren
    X = df[features].copy()

    # Kategorische Spalten mit LabelEncoder kodieren (Text → Zahl)
    # Modell kann nur mit Zahlen arbeiten, nicht mit Strings wie "ATL"
    # LabelEncoder-Konzept aus Unterricht; Anwendung via Claude
    encoders = {}
    for col in ["AIRLINE", "ORIGIN_AIRPORT", "DESTINATION_AIRPORT"]:
        if col in X.columns:
            le       = LabelEncoder()
            X[col]   = le.fit_transform(X[col].astype(str))
            encoders[col] = le    # Encoder speichern für spätere Verwendung in der App

    return X, encoders, features


# ── Modell 1: Binäre Klassifikation ──────────────────────────────────────────
def train_binary_classifier(X_train, y_train, X_test, y_test):
    """
    Trainiert ein XGBoost-Modell für die binäre Frage:
    "Wird dieser Flug verspätet sein?" (verspätet = Delay ≥ 15 Minuten)

    Da verspätete Flüge seltener sind als pünktliche (~33% vs 67%),
    wird scale_pos_weight verwendet um die Klassen auszubalancieren.
    """
    print("\nTrainiere Modell 1: Delayed / Not Delayed (XGBoost)...")
    print("  (3-6 Minuten)")

    # Klassengewicht berechnen: verhindert dass das Modell immer "pünktlich" vorhersagt
    # neg/pos = Anzahl pünktliche / Anzahl verspätete Flüge
    # Quelle: Claude – scale_pos_weight für unbalancierte Klassen via Claude
    neg   = (y_train == 0).sum()   # Anzahl pünktliche Flüge im Training
    pos   = (y_train == 1).sum()   # Anzahl verspätete Flüge im Training
    scale = neg / pos              # z.B. 2.0 wenn doppelt so viele pünktliche

    # XGBoost-Modell mit optimierten Hyperparametern erstellen
    # Quelle: Claude – XGBoost-Parameter vollständig via Claude
    model = XGBClassifier(
        n_estimators=300,          # Anzahl Entscheidungsbäume
        max_depth=6,               # Maximale Tiefe jedes Baums
        learning_rate=0.1,         # Lernrate (wie stark jeder Baum korrigiert)
        subsample=0.8,             # 80% der Daten pro Baum (verhindert Overfitting)
        colsample_bytree=0.8,      # 80% der Features pro Baum
        scale_pos_weight=scale,    # Klassengewicht für unbalancierte Daten
        n_jobs=-1,                 # Alle CPU-Kerne nutzen
        random_state=42,           # Reproduzierbarkeit
        eval_metric="logloss",     # Verlustfunktion für binäre Klassifikation
        verbosity=0,               # Keine Trainings-Ausgabe
    )

    # Modell auf Trainingsdaten trainieren
    model.fit(X_train, y_train)

    # Modell auf Testdaten evaluieren
    y_pred   = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"  Genauigkeit: {accuracy:.1%}")
    print(classification_report(y_test, y_pred, target_names=["On Time", "Delayed"]))

    # Wichtigste Features ausgeben (welche Variablen haben den grössten Einfluss?)
    # Quelle: Claude – feature_importances_ Attribut via Claude
    importance = pd.Series(model.feature_importances_, index=X_train.columns)
    print("  Wichtigste Features:")
    print(importance.sort_values(ascending=False).head(8).to_string())

    return model


# ── Modell 2: Multiclass-Klassifikation ──────────────────────────────────────
def train_multiclass_classifier(X_train, y_train, X_test, y_test):
    """
    Trainiert ein XGBoost-Modell für die Frage:
    "In welche Verspätungskategorie fällt dieser Flug?"

    Kategorien: No Delay / 15-30 min / 30-45 min / 45-60 min / 60-90 min / 90+ min
    """
    print("\nTrainiere Modell 2: Delay-Kategorien (XGBoost)...")
    print("  (3-6 Minuten)")

    # Kategorische Labels ("No Delay", "15-30 min" etc.) in Zahlen umwandeln
    # XGBoost erwartet numerische Klassen (0, 1, 2, ...)
    # Quelle: Claude – LabelEncoder für Multiclass-Ziele via Claude
    label_enc   = LabelEncoder()
    y_train_enc = label_enc.fit_transform(y_train)   # Training: fit + transform
    y_test_enc  = label_enc.transform(y_test)         # Test: nur transform

    # XGBoost-Modell für Mehrklassen-Klassifikation
    # Quelle: Claude – multi:softprob Objective und num_class via Claude
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        n_jobs=-1,
        random_state=42,
        objective="multi:softprob",              # Wahrscheinlichkeit pro Klasse ausgeben
        num_class=len(label_enc.classes_),       # Anzahl Kategorien (6)
        eval_metric="mlogloss",                  # Verlustfunktion für Mehrklassen
        verbosity=0,
    )

    model.fit(X_train, y_train_enc)

    # Modell evaluieren
    y_pred   = model.predict(X_test)
    accuracy = accuracy_score(y_test_enc, y_pred)
    print(f"  Genauigkeit: {accuracy:.1%}")
    print(f"  Kategorien: {list(label_enc.classes_)}")

    # LabelEncoder am Modell speichern damit predict.py die Kategorienamen abrufen kann
    # Quelle: Claude – Attribut dynamisch am Modell speichern via Claude
    model._label_encoder = label_enc

    return model


# ── Hauptfunktion: Trainieren und Speichern ───────────────────────────────────
def train_and_save_models(use_weather: bool = True):
    """
    Lädt den vorbereiteten Datensatz, trainiert beide Modelle
    und speichert sie als .pkl-Dateien im models/-Ordner.
    """
    print("Lade vorbereiteten Datensatz...")
    df = pd.read_csv("data/processed_flights.csv", low_memory=False)
    print(f"  {len(df):,} Flüge geladen")

    # Features und Labels vorbereiten
    X, encoders, feature_list = prepare_features(df, use_weather=use_weather)

    # Zielvariablen: binär (0/1) und kategorisch (Strings)
    y_binary = df["IS_DELAYED"]                  # 0 = pünktlich, 1 = verspätet
    y_multi  = df["DELAY_CATEGORY"].astype(str)  # "No Delay", "15-30 min", etc.

    # Daten in Training (80%) und Test (20%) aufteilen
    # stratify=y_binary stellt sicher dass beide Splits gleich viele Delays haben
    # Quelle: Claude – stratify-Parameter für balancierte Splits via Claude
    X_train, X_test, y_bin_train, y_bin_test, y_multi_train, y_multi_test = train_test_split(
        X, y_binary, y_multi,
        test_size=0.2,
        random_state=42,
        stratify=y_binary
    )

    print(f"\nDatensatz: {len(X_train):,} Training / {len(X_test):,} Test")

    # Beide Modelle trainieren
    binary_model = train_binary_classifier(X_train, y_bin_train, X_test, y_bin_test)
    multi_model  = train_multiclass_classifier(X_train, y_multi_train, X_test, y_multi_test)

    # Modelle, Encoder und Feature-Liste als .pkl-Dateien speichern
    # joblib.dump() serialisiert Python-Objekte für späteres Laden
    # Quelle: Claude – joblib.dump() und .pkl-Format via Claude
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(binary_model,  f"{MODEL_DIR}/binary_model.pkl")      # Binär-Klassifikator
    joblib.dump(multi_model,   f"{MODEL_DIR}/multiclass_model.pkl")  # Multiclass-Klassifikator
    joblib.dump(encoders,      f"{MODEL_DIR}/encoders.pkl")          # LabelEncoder-Objekte
    joblib.dump(feature_list,  f"{MODEL_DIR}/feature_list.pkl")      # Erwartete Features

    print(f"\nAlle Modelle gespeichert in: {MODEL_DIR}/")


# ── Einstiegspunkt ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Zuerst data_preprocessing.py ausführen um processed_flights.csv zu erstellen!
    train_and_save_models(use_weather=True)
