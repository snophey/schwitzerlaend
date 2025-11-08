"""
Streamlit Frontend für die Workouts API
Einfaches Test-Frontend zum Testen der API-Funktionalität
"""
import streamlit as st
import requests
import json
from typing import Optional

# API Base URL
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Workouts App",
    page_icon="💪",
    layout="wide"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'workout_id' not in st.session_state:
    st.session_state.workout_id = None


def api_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Helper function to make API requests"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        elif method == "DELETE":
            response = requests.delete(url, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "❌ Verbindung zur API fehlgeschlagen. Stelle sicher, dass der FastAPI Server läuft (uvicorn main:app --reload)"}
    except requests.exceptions.Timeout:
        return {"error": "⏱️ Request Timeout - Die API antwortet nicht"}
    except requests.exceptions.HTTPError as e:
        try:
            error_detail = response.json().get("detail", str(e))
        except:
            error_detail = str(e)
        return {"error": f"❌ HTTP Fehler: {error_detail}"}
    except Exception as e:
        return {"error": f"❌ Fehler: {str(e)}"}


def main():
    st.title("💪 Workouts App - Test Frontend")
    st.markdown("---")
    
    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Seite wählen",
        ["🏠 Home", "👤 User Management", "🏋️ Workouts", "📊 Weekly Overview", "📝 History"]
    )
    
    # Home Page
    if page == "🏠 Home":
        st.header("Willkommen zur Workouts App")
        st.markdown("""
        Diese App ist ein Test-Frontend für die Workouts API.
        
        **Verfügbare Funktionen:**
        - 👤 User Management: User erstellen und verwalten
        - 🏋️ Workouts: Workouts erstellen und AI-generierte Workouts erstellen
        - 📊 Weekly Overview: Wöchentliche Übersicht anzeigen
        - 📝 History: Workout-Fortschritt verfolgen
        
        **API Status:**
        """)
        
        # Check API status
        status = api_request("GET", "/")
        if "error" in status:
            st.error(status["error"])
        else:
            st.success("✅ API ist erreichbar")
            st.json(status)
    
    # User Management
    elif page == "👤 User Management":
        st.header("👤 User Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("User erstellen")
            new_user_id = st.text_input("User ID", key="new_user_id", placeholder="z.B. user123")
            if st.button("User erstellen", type="primary"):
                if new_user_id:
                    result = api_request("POST", f"/users/{new_user_id}")
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success(f"✅ User '{new_user_id}' erfolgreich erstellt!")
                        st.session_state.user_id = new_user_id
                        st.json(result)
                else:
                    st.warning("Bitte gib eine User ID ein")
        
        with col2:
            st.subheader("User abrufen")
            get_user_id = st.text_input("User ID", key="get_user_id", placeholder="z.B. user123")
            if st.button("User abrufen"):
                if get_user_id:
                    result = api_request("GET", f"/users/{get_user_id}")
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success(f"✅ User '{get_user_id}' gefunden")
                        st.session_state.user_id = get_user_id
                        st.json(result)
                else:
                    st.warning("Bitte gib eine User ID ein")
        
        # Current User
        if st.session_state.user_id:
            st.markdown("---")
            st.subheader(f"🔵 Aktiver User: `{st.session_state.user_id}`")
            if st.button("User löschen", type="secondary"):
                result = api_request("DELETE", f"/users/{st.session_state.user_id}")
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"✅ User '{st.session_state.user_id}' gelöscht")
                    st.session_state.user_id = None
                    st.rerun()
    
    # Workouts
    elif page == "🏋️ Workouts":
        st.header("🏋️ Workouts")
        
        if not st.session_state.user_id:
            st.warning("⚠️ Bitte erstelle oder wähle zuerst einen User in 'User Management'")
            return
        
        tab1, tab2, tab3 = st.tabs(["AI Workout generieren", "Workout anzeigen", "Workout löschen"])
        
        with tab1:
            st.subheader("🤖 AI Workout generieren")
            prompt = st.text_area(
                "Beschreibe dein gewünschtes Workout",
                placeholder="z.B. Ich möchte ein sanftes Yoga-Workout mit hauptsächlich Stretching, mittlerer Intensität",
                height=100
            )
            
            openai_key = st.text_input(
                "OpenAI API Key (optional, falls nicht in .env gesetzt)",
                type="password",
                help="Falls OPENAI_API_KEY in .env gesetzt ist, kann dieses Feld leer bleiben"
            )
            
            if st.button("Workout generieren", type="primary"):
                if prompt:
                    with st.spinner("🤖 Generiere Workout mit AI..."):
                        data = {"prompt": prompt}
                        if openai_key:
                            data["openai_api_key"] = openai_key
                        
                        result = api_request("POST", f"/users/{st.session_state.user_id}/generate-workout", data)
                        
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            st.success("✅ Workout erfolgreich generiert!")
                            st.session_state.workout_id = result.get("workout_id")
                            st.json(result)
                else:
                    st.warning("Bitte gib eine Beschreibung ein")
        
        with tab2:
            st.subheader("Workout Details anzeigen")
            workout_id = st.text_input("Workout ID", key="get_workout_id", placeholder="Workout ID eingeben")
            if st.button("Workout abrufen"):
                if workout_id:
                    result = api_request("GET", f"/workouts/{workout_id}")
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("✅ Workout gefunden")
                        st.json(result)
                else:
                    st.warning("Bitte gib eine Workout ID ein")
        
        with tab3:
            st.subheader("Workout löschen")
            delete_workout_id = st.text_input("Workout ID", key="delete_workout_id", placeholder="Workout ID eingeben")
            if st.button("Workout löschen", type="secondary"):
                if delete_workout_id:
                    result = api_request("DELETE", f"/workouts/{delete_workout_id}")
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("✅ Workout gelöscht")
                        st.json(result)
                else:
                    st.warning("Bitte gib eine Workout ID ein")
    
    # Weekly Overview
    elif page == "📊 Weekly Overview":
        st.header("📊 Weekly Overview")
        
        if not st.session_state.user_id:
            st.warning("⚠️ Bitte erstelle oder wähle zuerst einen User in 'User Management'")
            return
        
        if st.button("Weekly Overview abrufen", type="primary"):
            with st.spinner("Lade Weekly Overview..."):
                result = api_request("GET", f"/users/{st.session_state.user_id}/weekly-overview")
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("✅ Weekly Overview geladen")
                    
                    # Display summary
                    if "overall_summary" in result:
                        summary = result["overall_summary"]
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Workouts", summary.get("total_workouts", 0))
                        with col2:
                            st.metric("Training Days", summary.get("total_training_days", 0))
                        with col3:
                            st.metric("Rest Days", summary.get("total_rest_days", 0))
                        with col4:
                            st.metric("Total Sets", summary.get("total_sets", 0))
                    
                    # Display workouts
                    if "workouts" in result:
                        for workout in result["workouts"]:
                            with st.expander(f"Workout: {workout.get('workout_id', 'Unknown')}"):
                                if "weekly_plan" in workout:
                                    for day in workout["weekly_plan"]:
                                        day_name = day.get("day", "Unknown")
                                        sets = day.get("sets", [])
                                        is_rest = day.get("is_rest_day", False)
                                        
                                        if is_rest:
                                            st.markdown(f"**{day_name}**: 🛌 Rest Day")
                                        else:
                                            st.markdown(f"**{day_name}**: {len(sets)} Set(s)")
                                            for s in sets:
                                                exercise_name = s.get("name", "Unknown")
                                                reps = s.get("reps")
                                                weight = s.get("weight")
                                                duration = s.get("duration_sec")
                                                
                                                details = []
                                                if reps:
                                                    details.append(f"{reps} reps")
                                                if weight:
                                                    details.append(f"{weight} kg")
                                                if duration:
                                                    details.append(f"{duration}s")
                                                
                                                st.markdown(f"  - {exercise_name}" + (f" ({', '.join(details)})" if details else ""))
                    
                    # Full JSON
                    with st.expander("Vollständige JSON Antwort"):
                        st.json(result)
    
    # History
    elif page == "📝 History":
        st.header("📝 Workout History")
        
        if not st.session_state.user_id:
            st.warning("⚠️ Bitte erstelle oder wähle zuerst einen User in 'User Management'")
            return
        
        tab1, tab2, tab3 = st.tabs(["Latest History", "Progress Update", "Complete Set"])
        
        with tab1:
            st.subheader("Latest History abrufen")
            if st.button("Latest History laden", type="primary"):
                with st.spinner("Lade History..."):
                    result = api_request("GET", f"/history/{st.session_state.user_id}/latest")
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("✅ History geladen")
                        
                        # Display progress
                        if "progress" in result:
                            progress = result["progress"]
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Sets", progress.get("total_sets", 0))
                            with col2:
                                st.metric("Completed", progress.get("completed_sets", 0))
                            with col3:
                                st.metric("Completion", f"{progress.get('completion_percentage', 0)}%")
                        
                        # Display sets
                        if "sets" in result:
                            st.subheader(f"Day: {result.get('day_name', 'Unknown')}")
                            for s in result["sets"]:
                                set_name = s.get("set_name", "Unknown")
                                is_complete = s.get("is_complete", False)
                                completed_reps = s.get("completed_reps", 0)
                                target_reps = s.get("target_reps")
                                
                                status = "✅" if is_complete else "⏳"
                                st.markdown(f"{status} **{set_name}**")
                                if target_reps:
                                    st.progress(completed_reps / target_reps if target_reps > 0 else 0)
                                    st.caption(f"{completed_reps} / {target_reps} reps")
                        
                        with st.expander("Vollständige JSON Antwort"):
                            st.json(result)
        
        with tab2:
            st.subheader("Set Progress aktualisieren")
            set_id = st.text_input("Set ID", key="update_set_id")
            completed_reps = st.number_input("Completed Reps", min_value=0, value=0, key="update_reps")
            completed_duration = st.number_input("Completed Duration (sec)", min_value=0, value=0, key="update_duration")
            
            if st.button("Progress aktualisieren"):
                if set_id:
                    data = {"set_id": set_id}
                    if completed_reps > 0:
                        data["completed_reps"] = completed_reps
                    if completed_duration > 0:
                        data["completed_duration_sec"] = completed_duration
                    
                    result = api_request("POST", f"/history/{st.session_state.user_id}/update", data)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("✅ Progress aktualisiert")
                        st.json(result)
                else:
                    st.warning("Bitte gib eine Set ID ein")
        
        with tab3:
            st.subheader("Set als komplett markieren")
            complete_set_id = st.text_input("Set ID", key="complete_set_id")
            if st.button("Set abschließen", type="primary"):
                if complete_set_id:
                    data = {"set_id": complete_set_id}
                    result = api_request("POST", f"/history/{st.session_state.user_id}/complete", data)
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("✅ Set abgeschlossen!")
                        if result.get("new_day_started"):
                            st.info(f"🎉 Neuer Tag gestartet: {result.get('new_day_name')}")
                        st.json(result)
                else:
                    st.warning("Bitte gib eine Set ID ein")


if __name__ == "__main__":
    main()

