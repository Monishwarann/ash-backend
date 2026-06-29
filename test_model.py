import pandas as pd
import requests
import json
import joblib
import os

FEATURES = [
    "age",
    "sex",
    "plasma_C",
    "creatinine",
    "LYVE1",
    "REG1B",
    "TFF1",
    "REG1A",
    "CA19_9",
    "CEA",
    "bilirubin",
    "glucose",
    "urine_volume",
    "urine_pH"
]

def test_local_model():
    print("Testing locally loaded model...")
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pancreatic_cancer_xgboost.pkl')
    try:
        model = joblib.load(model_path)
        sample = {
            "age": 45, "sex": 1, "plasma_C": 10.0, "creatinine": 1.2, 
            "LYVE1": 2.5, "REG1B": 15.0, "TFF1": 30.0, "REG1A": 20.0, 
            "CA19_9": 10.0, "CEA": 1.5, "bilirubin": 0.8, "glucose": 95.0, 
            "urine_volume": 1200.0, "urine_pH": 6.5
        }
        df = pd.DataFrame([sample])[FEATURES]
        pred = model.predict(df)
        print(f"Prediction: {pred}")
        if hasattr(model, "predict_proba"):
            print(f"Proba: {model.predict_proba(df)}")
    except Exception as e:
        print(f"Error locally: {e}")

if __name__ == '__main__':
    test_local_model()
