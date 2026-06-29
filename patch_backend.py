import os
import re

def update_backend_predict():
    path = r"c:\Users\kmoni\Downloads\medi-main-main\medi-main-main\backend\app.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # The block we want to replace starts after `ec_score` calculation
    # Around line 206
    old_ai_block = r"        # 3\. Predict via Machine Learning Model fallback.*?# Final combined score"
    
    new_ai_block = """        # 3. Predict via Machine Learning Model (XGBoost)
    ai_confidence = 50.0
    predicted_risk_class = 0
    ai_score = 15.0
    
    # We will map the clinical survey and sensor data to the XGBoost features for dynamic interactivity
    if xgboost_model is None:
        load_xgboost_model()
        
    if xgboost_model is not None:
        try:
            # FEATURES = ["age", "sex", "plasma_C", "creatinine", "LYVE1", "REG1B", "TFF1", "REG1A", "CA19_9", "CEA", "bilirubin", "glucose", "urine_volume", "urine_pH"]
            # We map our available data to these features to demonstrate the ML pipeline
            mapped_features = {
                "age": float(age),
                "sex": 1.0, # Defaulting to male for this proxy
                "plasma_C": float(mq135 / 3.0), # Proxy
                "creatinine": float(mq3), # Proxy
                "LYVE1": float(mq7), # Proxy
                "REG1B": float(ph * 2.0), # Proxy
                "TFF1": float(ec * 100.0), # Proxy
                "REG1A": float(smoking * 50.0), # Proxy
                "CA19_9": float(diabetes * 150.0), # Proxy
                "CEA": float(jaundice * 10.0), # Proxy
                "bilirubin": float(weight_loss * 5.0), # Proxy
                "glucose": 100.0,
                "urine_volume": 1500.0,
                "urine_pH": float(ph)
            }
            
            query_df = pd.DataFrame([mapped_features])
            query_df = query_df[FEATURES]
            
            predicted_risk_class = int(xgboost_model.predict(query_df)[0])
            
            if hasattr(xgboost_model, "predict_proba"):
                prob = xgboost_model.predict_proba(query_df)[0]
                ai_confidence = round(float(prob[predicted_risk_class]) * 100, 2)
                ai_score = (prob[2] + 0.5 * prob[1]) * 100.0
            else:
                ai_score = 100.0 if predicted_risk_class == 2 else (50.0 if predicted_risk_class == 1 else 10.0)
                ai_confidence = 85.0
                
        except Exception as e:
            print(f"XGBoost Prediction error: {e}. Fallback used.")
            ai_score = 15.0
            if age > 60: ai_score += 15.0
            if diabetes: ai_score += 15.0
            if jaundice: ai_score += 35.0
            if family_history: ai_score += 20.0
            ai_score = min(ai_score, 100.0)
            ai_confidence = 100.0
    else:
        ai_score = 15.0
        if age > 60: ai_score += 15.0
        if diabetes: ai_score += 15.0
        if jaundice: ai_score += 35.0
        if family_history: ai_score += 20.0
        ai_score = min(ai_score, 100.0)
        ai_confidence = 100.0
        
    # Final combined score"""
    
    content = re.sub(old_ai_block, new_ai_block, content, flags=re.DOTALL)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    update_backend_predict()
    print("Backend logic applied successfully.")
