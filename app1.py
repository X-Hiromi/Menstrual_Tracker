import streamlit as st
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase (Only run once)
if not firebase_admin._apps:
    cred = credentials.Certificate("E:\PROJECTS\MENSTRUAL_TRACKER_PROJECT\menstrual-tracker-19d68-firebase-adminsdk-fbsvc-2f31f30a11.json")  # 🔹 Replace with your Firebase JSON key path
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Function to analyze symptoms
def analyze_symptoms(symptoms):
    risk_level = "Low"
    risk_score = 0
    food_recommendations = []

    if "pain" in symptoms or "irregular" in symptoms:
        risk_level = "Medium"
        risk_score = 5
        food_recommendations = ["Eat more fiber", "Limit processed foods"]

    if "hair loss" in symptoms or "acne" in symptoms:
        risk_level = "High"
        risk_score = 8
        food_recommendations = ["Increase protein", "Consult a doctor"]

    return risk_level, risk_score, food_recommendations

# Function to predict cycle
def predict_cycle(last_period_str, avg_cycle):
    last_period = datetime.strptime(last_period_str, "%Y-%m-%d").date()
    next_period = last_period + timedelta(days=avg_cycle)
    ovulation = last_period + timedelta(days=avg_cycle - 14)
    luteal_phase = (ovulation, next_period)
    fertile_window = (ovulation - timedelta(days=2), ovulation + timedelta(days=2))
    return next_period, ovulation, luteal_phase, fertile_window

# Streamlit UI
st.title("Menstrual Tracker")

# Login & Registration Tabs
tab1, tab2 = st.tabs(["Login", "Register"])

# User Registration
with tab2:
    st.header("Create an Account")
    reg_username = st.text_input("Choose a Username", key="reg_user")
    reg_password = st.text_input("Choose a Password", type='password', key="reg_pass")
    
    if st.button("Register"):
        if reg_username and reg_password:
            existing_users = db.collection("users").where("username", "==", reg_username).get()
            if existing_users:
                st.error("Username already exists. Choose another one.")
            else:
                db.collection("users").add({"username": reg_username, "password": reg_password})
                st.success("Account created successfully! Please log in.")

# User Login
with tab1:
    st.header("Login")
    username = st.text_input("Username", key="login_user")
    password = st.text_input("Password", type='password', key="login_pass")

    if st.button("Login"):
        user_ref = db.collection("users").where("username", "==", username).where("password", "==", password).get()
        if user_ref:
            st.session_state.user_id = user_ref[0].id
            st.session_state.username = username
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password.")

# Show main content if logged in
if "user_id" in st.session_state:
    st.header(f"Welcome, {st.session_state.username}!")
    
    # Symptoms Analysis
    with st.expander("Symptoms Analysis"):
        st.subheader("Analyze Your Symptoms")
        symptoms_input = st.text_input("Enter Symptoms (comma separated)")
        
        if st.button("Analyze Symptoms"):
            symptoms = [s.strip().lower() for s in symptoms_input.split(",") if s.strip()]
            if symptoms:
                risk_level, risk_score, food_recommendations = analyze_symptoms(symptoms)
                st.success(f"PCOS Risk Level: {risk_level}")
                st.success(f"Risk Score: {risk_score}")
                
                st.subheader("Food Recommendations")
                for recommendation in food_recommendations:
                    st.write(f"- {recommendation}")

                # Store in Firebase using set() to prevent duplicates
                doc_ref = db.collection("symptom_analysis").document(st.session_state.user_id)
                doc_ref.set({
                    "user_id": st.session_state.user_id,
                    "username": st.session_state.username,
                    "symptoms": symptoms,
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "food_recommendations": food_recommendations,
                    "timestamp": datetime.now()
                }, merge=True)
                st.success("Symptoms analysis saved to database.")

    # Cycle Prediction
    with st.expander("Track Your Cycle"):
        st.subheader("Predict Your Next Cycle")
        last_period = st.date_input("Last Period Date")
        avg_cycle = st.number_input("Average Cycle Length (days)", min_value=20, max_value=45, step=1)
        
        if st.button("Predict"):
            next_period, ovulation, luteal_phase, fertile_window = predict_cycle(last_period.strftime("%Y-%m-%d"), avg_cycle)
            st.write(f"Next Period: {next_period}")
            st.write(f"Ovulation Date: {ovulation}")
            st.write(f"Luteal Phase: {luteal_phase[0]} to {luteal_phase[1]}")
            st.write(f"Fertile Window: {fertile_window[0]} to {fertile_window[1]}")

    # Reminder Feature
    with st.expander("Set Reminder"):
        st.subheader("Add a Reminder")
        reminder_text = st.text_input("Reminder Text")
        reminder_date = st.date_input("Select Date")
        
        if st.button("Set Reminder"):
            doc_ref = db.collection("reminders").document(st.session_state.user_id)
            doc_ref.set({
                "user_id": st.session_state.user_id,
                "username": st.session_state.username,
                "reminder_text": reminder_text,
                "reminder_date": reminder_date.strftime("%Y-%m-%d"),
                "timestamp": datetime.now()
            }, merge=True)
            st.success("Reminder set successfully!")

    # Logout Button
    with st.sidebar.expander("Logout"):
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out successfully.")
            st.rerun()
