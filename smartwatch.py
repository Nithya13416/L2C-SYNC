import streamlit as st
from datetime import datetime
import random

# ------------------------
# Setup
# ------------------------
st.set_page_config(page_title="⌚ Smartwatch Health Dashboard", layout="wide")

# ------------------------
# Fake user & patient data
# ------------------------
USERS = {"doctor111": "password123"}

PATIENTS = [
    {"name": "Mr X", "age": 54, "gender": "Male", "weight": 62, "height": 168, "contact": "x_contact@gmail.com"},
    {"name": "Mr Y", "age": 47, "gender": "Male", "weight": 70, "height": 172, "contact": "y_contact@gmail.com"},
    {"name": "Mr Z", "age": 60, "gender": "Male", "weight": 80, "height": 175, "contact": "z_contact@gmail.com"},
    {"name": "saif ben hmida", "age": 54, "gender": "Male", "weight": 62, "height": 168, "contact": "ss@gmail.com"},
]

# ------------------------
# Utility
# ------------------------
def generate_metrics():
    return {
        "heart_rate": random.randint(60, 100),
        "temperature": round(random.uniform(35.5, 37.5), 1),
        "bmi": round(random.uniform(18, 28), 2),
        "systolic_bp": random.randint(110, 150),
        "diastolic_bp": random.randint(70, 95),
        "spo2": random.randint(90, 100),
    }

# ------------------------
# Session State Setup
# -----------------------
