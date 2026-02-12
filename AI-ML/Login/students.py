import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest


# ------------------ Load Dataset ------------------
data = pd.read_csv("students_logins.csv")

# Features: login_time and duration
X = data[['login_time', 'duration']]

# ------------------ Data Preprocessing ------------------
# Scale features for better performance
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ------------------ Anomaly Detection ------------------
# Using Isolation Forest to detect anomalies
iso_forest = IsolationForest(contamination=0.2, random_state=42)
anomalies = iso_forest.fit_predict(X_scaled)

# The model predicts 1 for normal, -1 for anomalies
data['anomaly'] = anomalies

# ------------------ Display Results ------------------
print("Detected Anomalies:")
print(data[data['anomaly'] == -1])

# Visualize anomalies
print("\nFull Data with Anomalies Detected:")
print(data)

