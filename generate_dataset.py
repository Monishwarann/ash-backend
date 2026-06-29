import numpy as np
import pandas as pd
import os

# Set random seed for reproducibility
np.random.seed(42)

def generate_synthetic_data(num_samples=1200):
    print(f"Generating synthetic dataset of {num_samples} samples...")
    
    # Demographics & Habits
    age = np.random.randint(18, 90, size=num_samples)
    
    # BMI: Normal (18.5-24.9), Overweight (25-29.9), Obese (>30)
    # Higher BMI increases risk slightly
    bmi = np.random.normal(26.0, 5.0, size=num_samples)
    bmi = np.clip(bmi, 15.0, 48.0)
    
    # Binary variables: Smoking, Alcohol, Diabetes, Family History
    # Smoking and Diabetes are major risk factors. Family history is extremely significant.
    smoking_history = np.random.choice([0, 1], size=num_samples, p=[0.7, 0.3])
    alcohol_consumption = np.random.choice([0, 1], size=num_samples, p=[0.6, 0.4])
    diabetes = np.random.choice([0, 1], size=num_samples, p=[0.85, 0.15]) # 15% diabetes rate in this screening cohort
    family_history = np.random.choice([0, 1], size=num_samples, p=[0.93, 0.07]) # 7% family history
    
    # Symptoms: Weight Loss, Abdominal Pain, Appetite Changes, Jaundice
    # These appear more frequently in actual high-risk or cancer cases
    weight_loss = np.random.choice([0, 1], size=num_samples, p=[0.85, 0.15])
    abdominal_pain = np.random.choice([0, 1], size=num_samples, p=[0.80, 0.20])
    appetite_changes = np.random.choice([0, 1], size=num_samples, p=[0.85, 0.15])
    jaundice = np.random.choice([0, 1], size=num_samples, p=[0.97, 0.03]) # Jaundice is rare but highly predictive of pancreatic head obstruction
    
    # Sensor Values (Breath VOCs)
    # MQ135: general VOCs/amines/benzene. Base: 10-60 PPM. Spikes to 100-300 PPM.
    # MQ3: alcohol/ketones/methyl mercaptan. Base: 5-30 PPM. Spikes to 40-120 PPM.
    # MQ7: carbon monoxide/combustibles. Base: 2-15 PPM. Spikes to 20-70 PPM.
    mq135_ppm = np.random.exponential(scale=35.0, size=num_samples) + 15.0
    mq3_ppm = np.random.exponential(scale=15.0, size=num_samples) + 5.0
    mq7_ppm = np.random.exponential(scale=8.0, size=num_samples) + 2.0
    
    # Saliva Markers
    # pH: Standard range 6.2 - 7.6. Acidic deviations (<6.2) or highly basic correlate with risk.
    saliva_ph = np.random.normal(6.9, 0.4, size=num_samples)
    
    # Electrical Conductivity (EC): Standard range 1.5 - 4.5 mS/cm. Spikes up to 8.0 mS/cm under inflammation.
    saliva_ec = np.random.normal(3.0, 1.0, size=num_samples)
    saliva_ec = np.clip(saliva_ec, 1.0, 9.0)
    
    # Calculate Risk Score (PCRI Basis) to assign classes probabilistically
    # Build a linear/non-linear risk index then inject noise.
    risk_score = np.zeros(num_samples)
    
    for i in range(num_samples):
        score = 0.0
        
        # Clinical Risk Factors
        if age[i] > 55: score += 12.0
        if age[i] > 70: score += 8.0
        if bmi[i] > 30.0: score += 5.0
        if smoking_history[i] == 1: score += 15.0
        if diabetes[i] == 1: score += 12.0
        if family_history[i] == 1: score += 18.0
        
        # Symptoms
        if weight_loss[i] == 1: score += 10.0
        if abdominal_pain[i] == 1: score += 8.0
        if appetite_changes[i] == 1: score += 6.0
        if jaundice[i] == 1: score += 30.0 # Huge clinical marker
        
        # Sensor VOCs (correlate with high risk states)
        # We simulate that true risk states also drive VOC elevations
        if mq135_ppm[i] > 80.0: score += 15.0
        if mq135_ppm[i] > 180.0: score += 10.0
        if mq3_ppm[i] > 35.0: score += 10.0
        if mq7_ppm[i] > 20.0: score += 8.0
        
        # Saliva deviation from normal pH (7.0)
        ph_dev = abs(saliva_ph[i] - 7.0)
        if ph_dev > 0.6:
            score += 10.0
        if ph_dev > 1.2:
            score += 10.0
            
        # Saliva Electrical Conductivity elevation
        if saliva_ec[i] > 5.0:
            score += 12.0
            
        # Correlate sensor readings with the target risk:
        # If score is high, we push up their sensor readings to make the ML learn the relationship
        if score > 50.0:
            mq135_ppm[i] += np.random.uniform(50.0, 150.0)
            mq3_ppm[i] += np.random.uniform(20.0, 60.0)
            mq7_ppm[i] += np.random.uniform(10.0, 30.0)
            saliva_ph[i] -= np.random.uniform(0.3, 0.9) # shifts acidic
            saliva_ec[i] += np.random.uniform(1.5, 3.5)
            score += 15.0 # Feedback effect
            
        # Normalize and add standard normal noise
        score += np.random.normal(0.0, 5.0)
        risk_score[i] = np.clip(score, 0.0, 100.0)

    # Classify based on score boundaries
    # 0 - 40: Low Risk (0)
    # 41 - 70: Moderate Risk (1)
    # 71 - 100: High Risk (2)
    risk_level = []
    for s in risk_score:
        if s <= 40.0:
            risk_level.append(0)  # Low Risk
        elif s <= 70.0:
            risk_level.append(1)  # Moderate Risk
        else:
            risk_level.append(2)  # High Risk
            
    # Compile into DataFrame
    df = pd.DataFrame({
        'age': age,
        'bmi': np.round(bmi, 1),
        'smoking_history': smoking_history,
        'alcohol_consumption': alcohol_consumption,
        'diabetes': diabetes,
        'family_history': family_history,
        'weight_loss': weight_loss,
        'abdominal_pain': abdominal_pain,
        'appetite_changes': appetite_changes,
        'jaundice': jaundice,
        'mq135_ppm': np.round(mq135_ppm, 2),
        'mq3_ppm': np.round(mq3_ppm, 2),
        'mq7_ppm': np.round(mq7_ppm, 2),
        'saliva_ph': np.round(saliva_ph, 2),
        'saliva_ec': np.round(saliva_ec, 2),
        'risk_score': np.round(risk_score, 1),
        'risk_level': risk_level
    })
    
    # Save directory setup
    os.makedirs('data', exist_ok=True)
    csv_path = 'data/pancreatic_cancer_screening_dataset.csv'
    df.to_csv(csv_path, index=False)
    print(f"Dataset saved successfully to {csv_path}!")
    
    # Print distribution
    print("\nDataset Class Distribution:")
    print(df['risk_level'].value_counts())
    print("\nSample Data:")
    print(df.head())

if __name__ == "__main__":
    generate_synthetic_data()
