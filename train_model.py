import pandas as pd
import numpy as np
import os
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

def train_risk_model():
    print("Loading dataset...")
    csv_path = 'data/pancreatic_cancer_screening_dataset.csv'
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found at {csv_path}. Run generate_dataset.py first.")
        
    df = pd.read_csv(csv_path)
    
    # Features and Target
    feature_cols = [
        'age', 'bmi', 'smoking_history', 'alcohol_consumption', 'diabetes', 
        'family_history', 'weight_loss', 'abdominal_pain', 'appetite_changes', 
        'jaundice', 'mq135_ppm', 'mq3_ppm', 'mq7_ppm', 'saliva_ph', 'saliva_ec'
    ]
    
    X = df[feature_cols]
    y = df['risk_level']
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print(f"Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")
    
    # Standardize numerical features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest Classifier
    print("Training Random Forest Classifier...")
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, class_weight='balanced')
    model.fit(X_train_scaled, y_train)
    
    # Predictions and Evaluation
    y_pred = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, y_pred)
    
    print("\n=== MODEL PERFORMANCE ===")
    print(f"Accuracy: {acc * 100:.2f}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Low Risk', 'Moderate Risk', 'High Risk']))
    
    print("Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature Importance Analysis
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    print("\n=== FEATURE IMPORTANCE RANKING ===")
    for rank in range(X.shape[1]):
        col_idx = indices[rank]
        print(f"{rank + 1}. {feature_cols[col_idx]}: {importances[col_idx] * 100:.2f}%")
        
    # Save the model and scaler
    os.makedirs('models', exist_ok=True)
    model_path = 'models/model.pkl'
    scaler_path = 'models/scaler.pkl'
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
        
    print(f"\nModel successfully saved to {model_path}!")
    print(f"Scaler successfully saved to {scaler_path}!")

if __name__ == "__main__":
    train_risk_model()
