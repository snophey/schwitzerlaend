# Streamlit Frontend - Workouts App

Ein einfaches Test-Frontend für die Workouts API, gebaut mit Streamlit.

## Installation

1. Stelle sicher, dass alle Dependencies installiert sind:
```bash
pip install -r requirements.txt
```

## Starten

### 1. FastAPI Backend starten

In einem Terminal:
```bash
cd code/backend
uvicorn main:app --reload
```

Das Backend läuft dann auf `http://localhost:8000`

### 2. Streamlit Frontend starten

In einem zweiten Terminal:
```bash
cd code/backend
streamlit run streamlit_app.py
```

Das Frontend öffnet sich automatisch im Browser auf `http://localhost:8501`

## Features

Das Streamlit Frontend bietet folgende Funktionen:

- **🏠 Home**: API Status prüfen
- **👤 User Management**: User erstellen, abrufen und löschen
- **🏋️ Workouts**: 
  - AI-generierte Workouts erstellen
  - Workout Details anzeigen
  - Workouts löschen
- **📊 Weekly Overview**: Wöchentliche Übersicht der Workouts anzeigen
- **📝 History**: 
  - Workout-Fortschritt anzeigen
  - Set Progress aktualisieren
  - Sets als komplett markieren

## Verwendung

1. Starte zuerst das FastAPI Backend
2. Starte dann das Streamlit Frontend
3. Erstelle oder wähle einen User in "User Management"
4. Nutze die verschiedenen Features zum Testen der API

## Konfiguration

Die API URL kann in `streamlit_app.py` geändert werden:
```python
API_BASE_URL = "http://localhost:8000"
```

Falls die API auf einem anderen Port läuft, passe diese Variable entsprechend an.

