"""
Datei:    app.py
Zweck:    Einstiegspunkt der Streamlit-App – konfiguriert die Navigation
          zwischen den Unterseiten (Dashboard und Prediction) und startet
          die jeweils aktive Seite.
Hinweis:  st.navigation(), st.Page() und position="hidden" sind nicht
          Bestandteil des Unterrichts; diese Konzepte wurden mit Hilfe
          von Claude (KI-Assistenz) erarbeitet.
"""

import streamlit as st  # Streamlit importieren (Web-App-Framework, im Unterricht eingeführt)

# Navigation mit mehreren Seiten konfigurieren
# HINWEIS: st.navigation() ist nicht Teil der Unterrichtstheorie – mit Claude erarbeitet
pg = st.navigation(
    [
        # Startseite: lädt 01_Dashboard.py, wird als Standard-Seite angezeigt
        # HINWEIS: st.Page() mit dem Parameter default=True ist nicht Teil der
        #          Unterrichtstheorie – mit Claude erarbeitet
        st.Page("01_Dashboard.py",                title="Home",       default=True),

        # Unterseite: lädt pages/02_Prediction.py
        # HINWEIS: st.Page() für Unterseiten in einem Unterordner (pages/) ist
        #          nicht Teil der Unterrichtstheorie – mit Claude erarbeitet
        st.Page("pages/02_Prediction.py", title="Prediction"),
    ],
    # Navigationsmenü ausblenden (kein Sidebar-Menü anzeigen)
    # HINWEIS: Der Parameter position="hidden" ist nicht Teil der
    #          Unterrichtstheorie – mit Claude erarbeitet
    position="hidden",
)

pg.run()  # Aktuell aktive Seite ausführen und rendern
          # HINWEIS: .run() auf dem Navigation-Objekt ist nicht Teil der
          #          Unterrichtstheorie – mit Claude erarbeitet
