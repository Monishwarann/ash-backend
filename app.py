import os
import json
import urllib.request
import pickle
import numpy as np
import joblib
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from database import User, SensorReading, Questionnaire, ScreeningLog, db
from firebase_admin import auth
from functools import wraps
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'pancreatic_risk_secret_key_135'

def verify_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        id_token = request.headers.get('Authorization')
        if not id_token:
            return jsonify({'message': 'Authorization token required'}), 401
        try:
            if id_token.startswith('Bearer '):
                id_token = id_token.split('Bearer ')[1]
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
        except Exception as e:
            return jsonify({'message': 'Invalid token', 'error': str(e)}), 401
        return f(*args, **kwargs)
    return decorated_function

# Global variables for model and scaler
model = None
scaler = None

def load_ai_model():
    global model, scaler
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'model.pkl')
    scaler_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'models', 'scaler.pkl')
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            model = joblib.load(model_path)
            scaler = joblib.load(scaler_path)
            print("AI Model and Scaler loaded successfully.")
        except Exception as e:
            print(f"Error loading AI model: {e}. Fallback to rule-based evaluation will be used.")
    else:
        print("AI model pickle files not found. Using fallback rule-based risk prediction.")



# UI Dashboard Route
@app.route('/')
def home():
    return render_template('index.html')

# API: Auth Routes
@app.route('/api/auth/register', methods=['POST'])
@verify_token
def register():
    data = request.get_json()
    uid = request.user['uid']
    email = request.user.get('email', data.get('email'))
    username = data.get('username', email.split('@')[0])
    
    User.create(uid=uid, username=username, email=email)
    return jsonify({'message': 'Registration successful', 'user_id': uid}), 201

@app.route('/api/auth/login', methods=['POST'])
@verify_token
def login():
    uid = request.user['uid']
    user = User.get_by_uid(uid)
    if not user:
        return jsonify({'message': 'User not found in database'}), 404
        
    return jsonify({
        'message': 'Login successful',
        'user_id': uid,
        'username': user.get('username'),
        'email': user.get('email')
    }), 200

# API: Profile Routes
@app.route('/api/profile/<user_id>', methods=['GET'])
@verify_token
def get_profile(user_id):
    if request.user['uid'] != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    user = User.get_by_uid(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(user), 200

@app.route('/api/profile/<user_id>', methods=['PUT'])
@verify_token
def update_profile(user_id):
    if request.user['uid'] != user_id:
        return jsonify({'message': 'Unauthorized'}), 403
    data = request.get_json()
    if not data:
        return jsonify({'message': 'No data provided'}), 400
    success = User.update_profile(user_id, data)
    if success:
        return jsonify({'message': 'Profile updated successfully'}), 200
    return jsonify({'message': 'Failed to update profile'}), 500


# API: Telemetry Route (ESP32 Post / Web Simulator Post)
@app.route('/api/telemetry', methods=['POST'])
def save_telemetry():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'message': 'User ID required'}), 400
        
    reading_id = SensorReading.create(
        user_id=data['user_id'],
        mq135_ppm=float(data.get('mq135_ppm', 0)),
        mq3_ppm=float(data.get('mq3_ppm', 0)),
        mq7_ppm=float(data.get('mq7_ppm', 0)),
        saliva_ph=float(data.get('saliva_ph', 7.0)),
        saliva_ec=float(data.get('saliva_ec', 3.0))
    )
    
    return jsonify({'message': 'Sensor reading saved successfully', 'id': reading_id}), 201

@app.route('/api/telemetry/latest/<user_id>', methods=['GET'])
def get_latest_telemetry(user_id):
    reading = SensorReading.get_latest(user_id)
    if not reading:
        return jsonify({'error': 'No real telemetry data available'}), 404
        
    return jsonify({
        'mq135_ppm': reading['mq135_ppm'],
        'mq3_ppm': reading['mq3_ppm'],
        'mq7_ppm': reading['mq7_ppm'],
        'saliva_ph': reading['saliva_ph'],
        'saliva_ec': reading['saliva_ec'],
        'timestamp': reading['timestamp']
    }), 200

# Helper: PCRI Index Calculation
def calculate_pcri(voc_score, ph_score, ec_score, ai_score):
    pcri = (0.30 * voc_score) + (0.20 * ph_score) + (0.20 * ec_score) + (0.30 * ai_score)
    return round(max(0.0, min(100.0, pcri)), 1)

# API: Evaluate screening risk
@app.route('/api/predict', methods=['POST'])
def predict_risk():
    global model, scaler
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'message': 'User ID required'}), 400
        
    user_id = data['user_id']
    
    # 1. Fetch clinical survey values
    age = int(data.get('age', 40))
    bmi = float(data.get('bmi', 24.5))
    smoking = int(data.get('smoking_history', 0))
    alcohol = int(data.get('alcohol_consumption', 0))
    diabetes = int(data.get('diabetes', 0))
    family_history = int(data.get('family_history', 0))
    weight_loss = int(data.get('weight_loss', 0))
    pain = int(data.get('abdominal_pain', 0))
    appetite = int(data.get('appetite_changes', 0))
    jaundice = int(data.get('jaundice', 0))
    
    # Save the survey values
    Questionnaire.create(
        user_id=user_id, age=age, bmi=bmi, smoking=smoking,
        alcohol=alcohol, diabetes=diabetes, family_history=family_history,
        weight_loss=weight_loss, pain=pain, appetite=appetite, jaundice=jaundice
    )
    
    # 2. Get latest sensor reading (or fall back to passed telemetry parameters)
    latest_sensor = SensorReading.get_latest(user_id)
    
    mq135 = float(data.get('mq135_ppm', latest_sensor['mq135_ppm'] if latest_sensor else 35.0))
    mq3 = float(data.get('mq3_ppm', latest_sensor['mq3_ppm'] if latest_sensor else 12.0))
    mq7 = float(data.get('mq7_ppm', latest_sensor['mq7_ppm'] if latest_sensor else 5.0))
    ph = float(data.get('saliva_ph', latest_sensor['saliva_ph'] if latest_sensor else 7.0))
    ec = float(data.get('saliva_ec', latest_sensor['saliva_ec'] if latest_sensor else 2.8))
    
    # 3. Calculate individual PCRI Components first
    # Breath score: normal combined PPM is low. Normal VOC sum < 50. Normalize total PPM (0 to 490 max scale)
    voc_sum = mq135 + mq3 + mq7
    voc_score = min(100.0, (voc_sum / 350.0) * 100.0)
    
    # pH score: Saliva normal is 6.5 to 7.4. Max deviation is mapped to 1.5 pH units.
    ph_dev = abs(ph - 7.0)
    ph_score = min(100.0, (ph_dev / 1.5) * 100.0)
    
    # EC score: Saliva conductivity normal 1.5 - 4.5.
    ec_score = max(0.0, min(100.0, ((ec - 1.5) / 6.0) * 100.0))

    # 4. Predict via Machine Learning Model (RandomForest)
    ai_confidence = 50.0
    predicted_risk_class = 0
    ai_score = 15.0
    
    if model is None or scaler is None:
        load_ai_model()
        
    if model is not None and scaler is not None:
        try:
            mapped_features = {
                "age": float(age),
                "bmi": float(bmi),
                "smoking_history": float(smoking),
                "alcohol_consumption": float(alcohol),
                "diabetes": float(diabetes),
                "family_history": float(family_history),
                "weight_loss": float(weight_loss),
                "abdominal_pain": float(pain),
                "appetite_changes": float(appetite),
                "jaundice": float(jaundice),
                "mq135_ppm": float(mq135),
                "mq3_ppm": float(mq3),
                "mq7_ppm": float(mq7),
                "saliva_ph": float(ph),
                "saliva_ec": float(ec)
            }
            
            features = scaler.feature_names_in_
            query_df = pd.DataFrame([mapped_features], columns=features)
            scaled_input = scaler.transform(query_df)
            
            predicted_risk_class = int(model.predict(scaled_input)[0])
            prob = model.predict_proba(scaled_input)[0]
            
            ai_confidence = round(float(prob[predicted_risk_class]) * 100, 2)
            ai_score = (prob[2] + 0.5 * prob[1]) * 100.0
            
        except Exception as e:
            print(f"AI Prediction error: {e}. Fallback used.")
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
        
    # Final combined score
    pcri_score = calculate_pcri(voc_score, ph_score, ec_score, ai_score)
    
    # Categorize Risk
    if pcri_score <= 40.0:
        risk_level = 'Low'
        rec = "Screening indicates low risk. Maintain healthy diet (high fiber, low saturated fats), regular exercise, and avoid smoking. Repeat screening in 6 months for preventive tracking."
    elif pcri_score <= 70.0:
        risk_level = 'Moderate'
        rec = "Screening suggests moderate risk profile. Recommend consultation with a healthcare provider to review metabolic panels, dietary adjustments, and active blood sugar tracking. Repeat screening in 3 months."
    else:
        risk_level = 'High'
        rec = "Screening reveals high risk indicators. Immediate clinical consultation is strongly recommended. Suggest discussing blood markers (CA19-9), abdominal ultrasound or MRI scans, and pancreatic enzyme assessments with a specialist."
    # Save the Screening Log
    log_id = ScreeningLog.create(
        user_id=user_id,
        pcri_score=pcri_score,
        risk_level=risk_level,
        ai_confidence=ai_confidence,
        recommendations=rec
    )
    
    return jsonify({
        'log_id': log_id,
        'pcri_score': pcri_score,
        'risk_level': risk_level,
        'ai_confidence': ai_confidence,
        'recommendations': rec,
        'components': {
            'breath_voc_score': round(voc_score, 1),
            'saliva_ph_score': round(ph_score, 1),
            'saliva_ec_score': round(ec_score, 1),
            'ai_prediction_score': round(ai_score, 1)
        },
        'timestamp': datetime.utcnow().isoformat()
    }), 200

# API: Get User Statistics
@app.route('/api/stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    user_doc = db.collection('users').document(user_id).get()
    if not user_doc.exists:
        return jsonify({'error': 'User not found'}), 404
        
    user_data = user_doc.to_dict()
    created_at = user_data.get('created_at', datetime.utcnow().isoformat())
    last_active = user_data.get('last_active', created_at)
    
    # Update last_active on stats fetch
    try:
        db.collection('users').document(user_id).update({'last_active': datetime.utcnow().isoformat()})
    except Exception:
        pass
    
    # Fetch all screening logs for this user
    docs = db.collection('screening_logs').where('user_id', '==', user_id).stream()
    logs = [d.to_dict() for d in docs]
    
    total_tests = len(logs)
    positive_predictions = sum(1 for log in logs if log.get('risk_level') == 'High')
    negative_predictions = total_tests - positive_predictions
    
    avg_confidence = 0.0
    if total_tests > 0:
        avg_confidence = sum(log.get('ai_confidence', 0.0) for log in logs) / total_tests
        
    logs.sort(key=lambda d: d.get('timestamp', ''), reverse=True)
    last_prediction_date = logs[0].get('timestamp') if total_tests > 0 else None
    last_prediction_result = logs[0].get('risk_level') if total_tests > 0 else None
    
    # Fetch last sensor reading time
    latest_sensor = SensorReading.get_latest(user_id)
    last_sensor_reading = latest_sensor.get('timestamp') if latest_sensor else None
    
    return jsonify({
        'total_tests': total_tests,
        'positive_predictions': positive_predictions,
        'negative_predictions': negative_predictions,
        'average_confidence': round(avg_confidence, 1),
        'last_prediction_date': last_prediction_date,
        'last_prediction_result': last_prediction_result,
        'last_sensor_reading': last_sensor_reading,
        'account_created_date': created_at,
        'last_active_date': last_active
    }), 200

# API: Live prediction for dashboard (no DB writes)
@app.route('/api/predict/live/<user_id>', methods=['GET'])
def predict_live(user_id):
    global model, scaler
    
    # 1. Get latest sensor reading
    latest_sensor = SensorReading.get_latest(user_id)
    if not latest_sensor:
        return jsonify({'error': 'No real telemetry data available'}), 404
        
    mq135 = float(latest_sensor['mq135_ppm'])
    mq3 = float(latest_sensor['mq3_ppm'])
    mq7 = float(latest_sensor['mq7_ppm'])
    ph = float(latest_sensor['saliva_ph'])
    ec = float(latest_sensor['saliva_ec'])
    
    # 2. Fetch clinical survey values from user profile
    user_doc = db.collection('users').document(user_id).get()
    profile = user_doc.to_dict() if user_doc.exists else {}
    age = int(profile.get('age', 40))
    
    smoking = 0
    diabetes = 0
    jaundice = 0
    weight_loss = 0
    family_history = 0
    
    # 3. Calculate individual PCRI Components
    voc_sum = mq135 + mq3 + mq7
    voc_score = min(100.0, (voc_sum / 350.0) * 100.0)
    
    ph_dev = abs(ph - 7.0)
    ph_score = min(100.0, (ph_dev / 1.5) * 100.0)
    
    ec_score = max(0.0, min(100.0, ((ec - 1.5) / 6.0) * 100.0))

    # 4. Predict via Machine Learning Model (RandomForest)
    ai_confidence = 50.0
    predicted_risk_class = 0
    ai_score = 15.0
    
    if model is None or scaler is None:
        load_ai_model()
        
    if model is not None and scaler is not None:
        try:
            mapped_features = {
                "age": float(age),
                "bmi": float(profile.get('bmi', 24.5)),
                "smoking_history": float(smoking),
                "alcohol_consumption": float(profile.get('alcohol_consumption', 0)),
                "diabetes": float(diabetes),
                "family_history": float(family_history),
                "weight_loss": float(weight_loss),
                "abdominal_pain": float(profile.get('abdominal_pain', 0)),
                "appetite_changes": float(profile.get('appetite_changes', 0)),
                "jaundice": float(jaundice),
                "mq135_ppm": float(mq135),
                "mq3_ppm": float(mq3),
                "mq7_ppm": float(mq7),
                "saliva_ph": float(ph),
                "saliva_ec": float(ec)
            }
            
            features = scaler.feature_names_in_
            query_df = pd.DataFrame([mapped_features], columns=features)
            scaled_input = scaler.transform(query_df)
            
            predicted_risk_class = int(model.predict(scaled_input)[0])
            prob = model.predict_proba(scaled_input)[0]
            
            ai_confidence = round(float(prob[predicted_risk_class]) * 100, 2)
            ai_score = (prob[2] + 0.5 * prob[1]) * 100.0
            
        except Exception as e:
            print(f"AI Live Prediction error: {e}")
            ai_score = 15.0
            if age > 60: ai_score += 15.0
            ai_score = min(ai_score, 100.0)
            ai_confidence = 100.0
    else:
        ai_score = 15.0
        if age > 60: ai_score += 15.0
        ai_score = min(ai_score, 100.0)
        ai_confidence = 100.0
        
    pcri_score = calculate_pcri(voc_score, ph_score, ec_score, ai_score)
    
    if pcri_score <= 40.0:
        risk_level = 'Low'
    elif pcri_score <= 70.0:
        risk_level = 'Moderate'
    else:
        risk_level = 'High'
        
    # Note: No ScreenLog or Questionnaire is saved here.
    
    return jsonify({
        'pcri_score': pcri_score,
        'risk_level': risk_level,
        'ai_confidence': ai_confidence,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

# Feature names in the exact order used for the new RandomForest AI model
FEATURES = [
    'age',
    'bmi',
    'smoking_history',
    'alcohol_consumption',
    'diabetes',
    'family_history',
    'weight_loss',
    'abdominal_pain',
    'appetite_changes',
    'jaundice',
    'mq135_ppm',
    'mq3_ppm',
    'mq7_ppm',
    'saliva_ph',
    'saliva_ec'
]

# Class labels
LABELS = {
    0: "Healthy",
    1: "Benign",
    2: "Pancreatic Cancer"
}

@app.route("/predict", methods=["POST"])
def predict():
    try:
        # Read JSON data
        data = request.get_json()

        # Check if JSON exists
        if data is None:
            return jsonify({
                "error": "No JSON data received."
            }), 400

        # Check for missing features
        missing_features = [feature for feature in FEATURES if feature not in data]

        if missing_features:
            return jsonify({
                "error": "Missing required features.",
                "missing_features": missing_features
            }), 400

        # Create DataFrame from input
        query_df = pd.DataFrame([data])

        # Ensure columns are in the correct order
        query_df = query_df[FEATURES]

        # Make prediction
        if model is None or scaler is None:
            return jsonify({
                "error": "AI model is not loaded on the server."
            }), 500

        scaled_input = scaler.transform(query_df)
        prediction = model.predict(scaled_input)
        predicted_class = int(prediction[0])

        # Predict probabilities if available
        probabilities = None
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(scaled_input)[0].tolist()

        # Return response
        return jsonify({
            "prediction": predicted_class,
            "prediction_label": LABELS.get(predicted_class, "Unknown"),
            "probabilities": probabilities,
            "message": "Prediction successful"
        })

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500

# API: Historical trend
@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    history = ScreeningLog.get_by_user(user_id)
    return jsonify(history), 200

# API: Generate and download screening report PDF
@app.route('/api/generate-pdf/<log_id>', methods=['GET'])
def generate_pdf(log_id):
    log = ScreeningLog.get_by_id(log_id)
    if not log: return jsonify({'error': 'No log found'}), 404
    
    user_id = log.get('user_id')
    user = User.get_by_uid(user_id) or {'username': 'Unknown', 'email': 'Unknown'}
    
    # Just grab latest for PDF
    sensors = SensorReading.get_latest(user_id) or {}
    survey = Questionnaire.get_latest(user_id) or {}
    
    
    pdf_filename = f"PCRI_Report_Log_{log.get('id', 'new')}.pdf"
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), pdf_filename)
    
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    # Styling
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#1E3A8A'),
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray,
        spaceAfter=20
    )
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#2563EB'),
        spaceBefore=12,
        spaceAfter=8,
        borderPadding=2
    )
    body_style = styles['Normal']
    alert_style = ParagraphStyle(
        'Alert',
        parent=styles['Normal'],
        fontSize=11,
        fontName='Helvetica-Bold',
        textColor=colors.white
    )
    
    # Document Header
    story.append(Paragraph("PANCREATIC CANCER RISK ASSESSMENT REPORT", title_style))
    story.append(Paragraph(f"AI-driven Multi-Sensor Non-Invasive Screening Device • Generated on: {datetime.fromisoformat(log['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Patient Info Table
    info_data = [
        [Paragraph("<b>Patient Username:</b>", body_style), Paragraph(user.get('username', 'N/A'), body_style),
         Paragraph("<b>Email:</b>", body_style), Paragraph(user.get('email', 'N/A'), body_style)],
        [Paragraph("<b>Age:</b>", body_style), Paragraph(str(survey.get('age', 'N/A')) if survey else "N/A", body_style),
         Paragraph("<b>BMI:</b>", body_style), Paragraph(str(survey.get('bmi', 'N/A')) if survey else "N/A", body_style)]
    ]
    info_table = Table(info_data, colWidths=[120, 130, 100, 150])
    info_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F9FAFB'))
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))
    
    # Screening Summary (Colored risk box)
    risk_color = '#EF4444' if log.get('risk_level', 'Low') == 'High' else ('#F59E0B' if log.get('risk_level', 'Low') == 'Moderate' else '#10B981')
    risk_summary_data = [
        [Paragraph(f"PCRI SCORE: {log.get('pcri_score', 0)} / 100", alert_style), 
         Paragraph(f"RISK LEVEL: {log.get('risk_level', 'Low').upper()}", alert_style),
         Paragraph(f"AI CONFIDENCE: {log.get('ai_confidence', 0)}%", alert_style)]
    ]
    risk_table = Table(risk_summary_data, colWidths=[160, 170, 170])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(risk_color)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 15))
    
    # Biomarker Reading
    story.append(Paragraph("Biomarker and Sensor Readings", section_style))
    sensor_data = [
        [Paragraph("<b>Biomarker Sensor Channel</b>", body_style), Paragraph("<b>Measured Value</b>", body_style), Paragraph("<b>Standard Reference Range</b>", body_style)],
        [Paragraph("MQ135 (Breath VOC / Amines)", body_style), Paragraph(f"{sensors.get('mq135_ppm', 35.0) if sensors else 35.0} PPM", body_style), Paragraph("< 80 PPM (Low Background)", body_style)],
        [Paragraph("MQ3 (Breath Alcohol / Organics)", body_style), Paragraph(f"{sensors.get('mq3_ppm', 12.0) if sensors else 12.0} PPM", body_style), Paragraph("< 35 PPM (Low Background)", body_style)],
        [Paragraph("MQ7 (Breath Carbon Monoxide)", body_style), Paragraph(f"{sensors.get('mq7_ppm', 5.0) if sensors else 5.0} PPM", body_style), Paragraph("< 20 PPM (Low Background)", body_style)],
        [Paragraph("Salivary pH (Acidic Dev)", body_style), Paragraph(f"{sensors.get('saliva_ph', 7.0) if sensors else 7.0} pH", body_style), Paragraph("6.5 - 7.5 pH (Normal Saliva)", body_style)],
        [Paragraph("Salivary Electrical Conductivity", body_style), Paragraph(f"{sensors.get('saliva_ec', 2.8) if sensors else 2.8} mS/cm", body_style), Paragraph("1.5 - 4.5 mS/cm (Normal range)", body_style)]
    ]
    sensor_table = Table(sensor_data, colWidths=[200, 150, 150])
    sensor_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F9FAFB')])
    ]))
    story.append(sensor_table)
    story.append(Spacer(1, 15))
    
    # Clinical Symptoms Checklist
    story.append(Paragraph("Clinical Risk Checklist", section_style))
    def yes_no(val):
        return "Yes" if val == 1 else "No"
    
    symp_data = [
        [Paragraph("<b>Risk Metric</b>", body_style), Paragraph("<b>Status</b>", body_style),
         Paragraph("<b>Risk Metric</b>", body_style), Paragraph("<b>Status</b>", body_style)],
        [Paragraph("Smoking History", body_style), Paragraph(yes_no(survey.get('smoking_history', 0)) if survey else "No", body_style),
         Paragraph("Diabetes History", body_style), Paragraph(yes_no(survey.get('diabetes', 0)) if survey else "No", body_style)],
        [Paragraph("Family Cancer History", body_style), Paragraph(yes_no(survey.get('family_history', 0)) if survey else "No", body_style),
         Paragraph("Unexplained Weight Loss", body_style), Paragraph(yes_no(survey.get('weight_loss', 0)) if survey else "No", body_style)],
        [Paragraph("Abdominal Pain (Back-radiating)", body_style), Paragraph(yes_no(survey.get('abdominal_pain', 0)) if survey else "No", body_style),
         Paragraph("Jaundice (Skin/Eye Yellowing)", body_style), Paragraph(yes_no(survey.get('jaundice', 0)) if survey else "No", body_style)]
    ]
    symp_table = Table(symp_data, colWidths=[160, 90, 160, 90])
    symp_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('PADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E5E7EB'))
    ]))
    story.append(symp_table)
    story.append(Spacer(1, 15))
    
    # Recommendations
    story.append(Paragraph("Clinical Recommendations", section_style))
    story.append(Paragraph(log.get('recommendations', ''), body_style))
    story.append(Spacer(1, 20))
    
    # Disclaimer
    story.append(Paragraph("<b>Disclaimer:</b> This system is designed as an AI-driven, multi-sensor early non-invasive screening aid for estimating risk metrics. It does not replace a clinical diagnosis. Pancreatic cancer screenings must be confirmed using standard hospital pathology tests (MRI, CT Scan, biopsy, and serum CA19-9 tests) under a physician's guidance.", ParagraphStyle('Disc', parent=body_style, fontSize=8, textColor=colors.HexColor('#4B5563'))))
    
    # Build Document
    doc.build(story)
    
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    # Initial load of AI model
    load_ai_model()
    
    # Retrieve port dynamically for cloud environments
    port = int(os.environ.get('PORT', 5000))
    # Turn off debug mode in production to ensure safety
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
