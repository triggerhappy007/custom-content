import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.metrics import accuracy_score

# Step 1: Create synthetic financial transaction data
def create_financial_data():
    np.random.seed(42)
    legitimate = np.random.normal(loc=100, scale=20, size=(1000, 2))  # Legitimate transactions
    fraud = np.random.normal(loc=200, scale=5, size=(50, 2))  # Fraudulent transactions
    X = np.vstack((legitimate, fraud))
    y = np.hstack((np.zeros(len(legitimate)), np.ones(len(fraud))))  # 0 = legitimate, 1 = fraud
    return X, y

# Step 2: Train an anomaly detection model
def train_anomaly_model(X):
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X)
    return model

# Step 3: Simulate an attack by modifying fraudulent transactions
def manipulate_data(X, y):
    """
    Modify fraudulent transactions to resemble legitimate ones.
    """
    manipulated_X = X.copy()
    manipulated_X[y == 1] -= 100  # Shift fraudulent data closer to legitimate cluster
    return manipulated_X

# Step 4: Demonstration
# Create financial data
X, y = create_financial_data()

# Train the anomaly detection model
model = train_anomaly_model(X)

# Predict anomalies before the attack
initial_predictions = model.predict(X)  # -1 = anomaly, 1 = normal
initial_anomalies = (initial_predictions == -1).sum()
print(f"Initial detected anomalies: {initial_anomalies}")

# Manipulate data to simulate the attack
manipulated_X = manipulate_data(X, y)

# Predict anomalies after the attack
manipulated_predictions = model.predict(manipulated_X)
manipulated_anomalies = (manipulated_predictions == -1).sum()
print(f"Detected anomalies after attack: {manipulated_anomalies}")

# Step 5: Visualization
plt.figure(figsize=(12, 6))

# Original data
plt.subplot(1, 2, 1)
plt.scatter(X[:, 0], X[:, 1], c=y, cmap='coolwarm', label='Original Data')
plt.title('Original Transaction Data')
plt.legend()

# Manipulated data
plt.subplot(1, 2, 2)
plt.scatter(manipulated_X[:, 0], manipulated_X[:, 1], c=y, cmap='coolwarm', label='Manipulated Data')
plt.title('Manipulated Transaction Data')
plt.legend()

plt.show()
