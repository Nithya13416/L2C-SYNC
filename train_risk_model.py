# train_risk_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# ----------------------------
# 1. Create dummy training data
# ----------------------------
# Each row = one patient record
# risk column = label (low, medium, high)
data = pd.DataFrame({
    'heart_rate': [70, 120, 90, 55, 85, 110, 65, 100, 72, 130],
    'temperature': [36.5, 38.5, 37.2, 35.5, 36.8, 39, 36, 37, 36.7, 38],
    'oxygen': [98, 90, 95, 88, 97, 92, 96, 94, 99, 89],
    'systolic': [120, 150, 130, 140, 125, 160, 118, 135, 122, 155],
    'diastolic': [80, 95, 85, 90, 82, 100, 78, 88, 81, 98],
    'bmi': [22, 30, 25, 18, 23, 32, 20, 27, 24, 29],
    'risk': [
        'low', 'high', 'medium', 'high', 'low',
        'high', 'low', 'medium', 'low', 'high'
    ]
})

# ----------------------------
# 2. Split features & labels
# ----------------------------
X = data[['heart_rate','temperature','oxygen','systolic','diastolic','bmi']]
y = data['risk']

# ----------------------------
# 3. Train model
# ----------------------------
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)

# ----------------------------
# 4. Save model
# ----------------------------
joblib.dump(model, "risk_model.pkl")
print("✅ Risk prediction model trained and saved as risk_model.pkl")
