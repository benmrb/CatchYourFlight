"""
utils/navbar.py
 
Globale Navigationsleiste für die CatchYourFlight Streamlit-App.
Wird auf jeder Seite eingebunden und stellt einheitliches CSS-Styling
sowie die Navigations-Links (Dashboard / Prediction) bereit.
Enthält ausserdem das App-Logo als Base64-kodiertes Inline-Bild.
 
Abhängigkeiten:
  - logo.png   (Projektlogo im Stammverzeichnis)
 
Autoren: Sára Jankovičová, Stefanie Seiler
Datum:   Mai 2026
 
Quellen:
- CS-Unterricht: Funktionsdefinition, f-Strings, String-Operationen
- Claude (Sonnet 4): gesamtes CSS-Styling via st.markdown
  (data-testid-Selektoren, data-baseweb-Selektoren, Farb- und
  Schriftkonfiguration), Base64-Logo-Einbettung via base64/pathlib,
  st.columns()-Layout, st.page_link(), HTML-Navbar-Struktur
"""
 
# ── Imports ───────────────────────────────────────────────────────────────────
import streamlit as st              # Streamlit: Webanwendungs-Framework
import base64, pathlib              # base64: Logo-Bild kodieren; pathlib: Dateipfad lesen
                                    # Quelle: Claude – base64 und pathlib nicht im Unterricht
 
 
def show_navbar():
    # Rendert das globale CSS-Styling und die Navigationsleiste.
    # Wird auf jeder Seite am Anfang aufgerufen.
 
    # ── Globales CSS-Styling ──────────────────────────────────────────────────
    # Weißer Hintergrund, schwarze Schrift, Helvetica Neue, Sidebar ausgeblendet
    # Quelle: Claude – gesamtes CSS vollständig via Claude; CSS-Injection-Konzept nicht im Unterricht
    st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
 
    /* Weißer Hintergrund */
    [data-testid="stAppViewContainer"] { background-color: #ffffff; }
    [data-testid="stHeader"] { background-color: transparent; }
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu, footer { visibility: hidden; }
 
    /* Anker-Link-Icon beim Hovern verstecken */
    a.anchor-link,
    h1 a, h2 a, h3 a, h4 a,
    [data-testid="stMarkdownContainer"] a[href^="#"],
    .stMarkdown a[href^="#"] {
        display: none !important;
        visibility: hidden !important;
    }
 
    /* Alle Texte schwarz */
    html, body, p, span, div, label, li, a,
    h1, h2, h3, h4, h5, h6,
    [data-testid="stMarkdownContainer"] *,
    [data-testid="stText"] *,
    [data-testid="metric-container"] *,
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"],
    [data-testid="stMetricDelta"],
    .stSlider label, .stDateInput label,
    .stSelectbox label, .stTextInput label,
    [data-testid="stWidgetLabel"] *,
    [data-testid="stCaptionContainer"] *,
    [data-testid="stDataFrameResizable"] * {
        color: #111111 !important;
    }
 
    /* Ausnahme: Text im Hero-Bild bleibt weiß */
    .hero-text, .hero-text * {
        color: inherit !important;
    }
 
    /* Selectbox: Eingabefeld Hintergrund hellblau */
    [data-baseweb="select"] > div {
        background-color: #EFF6FF !important;
        border-color: #BFDBFE !important;
    }
 
    /* Selectbox: Dropdown-Liste Hintergrund hellblau */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background-color: #EFF6FF !important;
    }
 
    /* Selectbox: einzelne Einträge in der Liste */
    [role="option"] {
        background-color: #EFF6FF !important;
    }
 
    /* Selectbox: Hover auf einem Eintrag etwas dunkler blau */
    [role="option"]:hover {
        background-color: #DBEAFE !important;
    }
 
    /* Dataframe: Tabellen-Hintergrund hellblau */
    [data-testid="stDataFrame"] iframe {
        background-color: #EFF6FF !important;
    }
    .stDataFrame, [data-testid="stDataFrameResizable"] {
        background-color: #EFF6FF !important;
        border-radius: 8px;
    }
 
    /* page_link Buttons als Navbar-Links stylen */
    div[data-testid="stPageLink"] a {
        text-decoration: none !important;
        color: #111111 !important;
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.01em !important;
    }
    div[data-testid="stPageLink"] a:hover { color: #3B82F6 !important; }
    div[data-testid="stPageLink"] p {
        font-size: 1.05rem !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)
 
    # ── Navigationsleiste ─────────────────────────────────────────────────────
    # App-Name links, Seiten-Links rechts — breitere Spalten damit kein Text abgeschnitten wird
    # st.columns(): Vier Spalten mit Breitenverhältnis 3 : 4.5 : 1.5 : 1.5
    # Quelle: Claude – st.columns() und Spaltengewichte via Claude
    nav_logo, nav_space, nav1, nav2 = st.columns([3, 4.5, 1.5, 1.5])
 
    with nav_logo:
        # Logo aus Datei lesen, als Base64-String kodieren und als Inline-Bild einbetten
        # pathlib.Path().read_bytes() liest die Binärdaten der PNG-Datei
        # base64.b64encode() wandelt Bytes in Base64-String um (für data:image/png-URL)
        # Quelle: Claude – base64-Einbettung von Bildern in HTML via Claude
        _logo_b64 = base64.b64encode(pathlib.Path("logo.png").read_bytes()).decode()
 
        # Navbar-Logo und App-Name als HTML-Block anzeigen
        # f-String mit inline Base64-Bild-URL; Styling via inline CSS
        # Quelle: Claude – HTML-Struktur, inline CSS und Base64-data-URL via Claude
        st.markdown(
            f"<div style='display:flex; align-items:center; gap:0; padding-top:0.4rem;'>"
            f"<img src='data:image/png;base64,{_logo_b64}' style='height:3rem; width:auto;'/>"
            f"<span style='font-size:2rem; font-weight:800; font-family:Helvetica Neue, Helvetica, Arial, sans-serif;'>CatchYourFlight</span>"
            f"<span style='color:#6B7280; font-weight:400; font-size:1.5rem; margin:0 0.35rem; font-family:Helvetica Neue, Helvetica, Arial, sans-serif;'>·</span>"
            f"<span style='color:#6B7280; font-weight:400; font-size:1.5rem; font-family:Helvetica Neue, Helvetica, Arial, sans-serif;'>USA</span></div>",
            unsafe_allow_html=True
        )
 
    with nav1:
        # Dashboard verlinkt auf die Startseite (app.py) mit Hero und Charts
        # st.page_link() erzeugt einen internen Streamlit-Navigations-Link
        # Quelle: Claude – st.page_link() nicht im Unterricht behandelt
        st.page_link("app.py", label="Dashboard")
 
    with nav2:
        # Prediction-Link zur Vorhersage-Seite
        st.page_link("pages/02_Prediction.py", label="Prediction")
 
    # Trennlinie unter der Navbar (dünne graue Linie, margin-bottom für Abstand zum Inhalt)
    # Quelle: Claude – HTML-hr-Styling via Claude
    st.markdown("<hr style='border:none; border-top:1px solid #e0e0e0; margin:0 0 2rem 0;'>", unsafe_allow_html=True)
