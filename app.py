import streamlit as st  # Streamlit importieren (Web-App-Framework)

# Navigation mit mehreren Seiten konfigurieren
pg = st.navigation(
    [
        # Startseite: lädt pages/01_Dashboard.py, wird als Standard-Seite angezeigt
        st.Page("pages/01_Dashboard.py",                title="Home",       default=True),
        # Unterseite: lädt pages/02_Prediction.py
        st.Page("pages/02_Prediction.py", title="Prediction"),
    ],
    position="hidden",  # Navigationsmenü ausblenden (kein Sidebar-Menü anzeigen)
)

pg.run()  # Aktuell aktive Seite ausführen und rendern
