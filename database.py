import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from datetime import datetime

# Initialize Firebase Admin SDK
cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'serviceAccountKey.json')
try:
    if not firebase_admin._apps:
        # Check if environment variable contains Firebase JSON
        firebase_json = os.environ.get('FIREBASE_CREDENTIALS')
        if firebase_json:
            import json
            cred_dict = json.loads(firebase_json)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin initialized via FIREBASE_CREDENTIALS environment variable.")
        elif os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin initialized via serviceAccountKey.json.")
        else:
            # Render/AppEngine might use default credentials
            firebase_admin.initialize_app()
            print("Firebase Admin initialized via default credentials.")
    db = firestore.client()
except Exception as e:
    print(f"Failed to initialize Firebase Admin: {e}")
    db = None

class User:
    @staticmethod
    def create(uid, username, email):
        if not db: return None
        user_data = {
            'username': username,
            'email': email,
            'created_at': datetime.utcnow().isoformat()
        }
        db.collection('users').document(uid).set(user_data)
        return uid
        
    @staticmethod
    def get_by_uid(uid):
        if not db: return None
        doc = db.collection('users').document(uid).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    @staticmethod
    def get_by_email(email):
        if not db: return None
        docs = db.collection('users').where('email', '==', email).limit(1).stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        return None

    @staticmethod
    def update_profile(uid, data):
        if not db: return False
        try:
            db.collection('users').document(uid).set(data, merge=True)
            return True
        except Exception as e:
            print(f"Error updating profile: {e}")
            return False

class SensorReading:
    @staticmethod
    def create(user_id, mq135_ppm, mq3_ppm, mq7_ppm, saliva_ph, saliva_ec):
        if not db: return None
        data = {
            'user_id': user_id,
            'mq135_ppm': mq135_ppm,
            'mq3_ppm': mq3_ppm,
            'mq7_ppm': mq7_ppm,
            'saliva_ph': saliva_ph,
            'saliva_ec': saliva_ec,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        _, doc_ref = db.collection('sensor_readings').add(data)
        return doc_ref.id

    @staticmethod
    def get_latest(user_id):
        if not db: return None
        try:
            docs = list(db.collection('sensor_readings').where('user_id', '==', user_id).stream())
            if not docs:
                return None
            # Sort in memory to avoid requiring a composite index in Firestore
            docs.sort(key=lambda d: d.to_dict().get('timestamp', ''), reverse=True)
            data = docs[0].to_dict()
            data['id'] = docs[0].id
            return data
        except Exception as e:
            print(f"Error fetching latest reading: {e}")
            return None

class Questionnaire:
    @staticmethod
    def create(user_id, age, bmi, smoking, alcohol, diabetes, family_history, weight_loss, pain, appetite, jaundice):
        if not db: return None
        data = {
            'user_id': user_id,
            'age': age,
            'bmi': bmi,
            'smoking_history': smoking,
            'alcohol_consumption': alcohol,
            'diabetes': diabetes,
            'family_history': family_history,
            'weight_loss': weight_loss,
            'abdominal_pain': pain,
            'appetite_changes': appetite,
            'jaundice': jaundice,
            'timestamp': datetime.utcnow().isoformat()
        }
        _, doc_ref = db.collection('questionnaires').add(data)
        return doc_ref.id
        
    @staticmethod
    def get_latest(user_id):
        if not db: return None
        try:
            docs = list(db.collection('questionnaires').where('user_id', '==', user_id).stream())
            if not docs: return None
            docs.sort(key=lambda x: x.to_dict().get('timestamp', ''), reverse=True)
            return docs[0].to_dict()
        except Exception as e:
            print(f"Error fetching questionnaire: {e}")
            return None

class ScreeningLog:
    @staticmethod
    def create(user_id, pcri_score, risk_level, ai_confidence, recommendations):
        if not db: return None
        data = {
            'user_id': user_id,
            'pcri_score': pcri_score,
            'risk_level': risk_level,
            'ai_confidence': ai_confidence,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }
        _, doc_ref = db.collection('screening_logs').add(data)
        return doc_ref.id
        
    @staticmethod
    def get_by_user(user_id, limit=5):
        if not db: return []
        try:
            docs = list(db.collection('screening_logs').where('user_id', '==', user_id).stream())
            # Sort in memory to avoid requiring a composite index in Firestore
            docs.sort(key=lambda d: d.to_dict().get('timestamp', ''), reverse=True)
            results = []
            for doc in docs[:limit]:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)
            return results
        except Exception as e:
            print(f"Error fetching screening logs: {e}")
            return []

    @staticmethod
    def get_by_id(log_id):
        if not db: return None
        try:
            doc = db.collection('screening_logs').document(log_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                return data
            return None
        except Exception as e:
            print(f"Error fetching screening log: {e}")
            return None
