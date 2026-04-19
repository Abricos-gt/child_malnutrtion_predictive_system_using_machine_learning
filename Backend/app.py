import pandas as pd
import joblib
import os
import numpy as np
import json
import random
import string
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from flask_cors import CORS

app = Flask(__name__)
app.secret_key = "abrha_secret_key_2026" 
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:5177"
])


# --- 1. DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456789@127.0.0.1/malnutrition_proactive_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. LOAD AI MODEL PACKAGE ---
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'malnutrition_proactive_model2.pkl')
try:
    model_pkg = joblib.load(model_path)
    rf_model = model_pkg['model']
    final_features = model_pkg['features'] 
except Exception as e:
    print(f"Error loading model: {e}")

# --- 3. WHO Z-SCORE ENGINE ---
def load_who(name):
    return pd.read_csv(os.path.join(base_dir, "who_tables", name))

wfa_b, wfa_g = load_who("wfa_boys.csv"), load_who("wfa_girls.csv")
hfa_b, hfa_g = load_who("hfa_boys.csv"), load_who("hfa_girls.csv")
wfh_b, wfh_g = load_who("wfh_boys.csv"), load_who("wfh_girls.csv")

def zscore_calc(x, L, M, S):
    if L == 0: return np.log(x / M) / S
    return ((x / M) ** L - 1) / (L * S)

def get_lms(df, col, value):
    df = df.copy()
    df["diff"] = (df[col] - value).abs()
    row = df.loc[df["diff"].idxmin()]
    return row["L"], row["M"], row["S"]

def compute_zscores(age, weight, height, gender):
    g = gender.lower()
    wfa, hfa, wfh = (wfa_b, hfa_b, wfh_b) if g == "male" else (wfa_g, hfa_g, wfh_g)
    L, M, S = get_lms(wfa, "Month", age)
    waz = zscore_calc(weight, L, M, S)
    L, M, S = get_lms(hfa, "Month", age)
    haz = zscore_calc(height, L, M, S)
    h_col = "Height_Length" if "Height_Length" in wfh.columns else "Height"
    L, M, S = get_lms(wfh, h_col, height)
    whz = zscore_calc(weight, L, M, S)
    return haz, whz, waz

# --- 4. DATABASE MODELS ---
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum('Admin', 'CHW'), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)

class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.String(50), primary_key=True) 
    name = db.Column(db.String(100), nullable=False)
    parent_full_name = db.Column(db.String(150))
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum('Male', 'Female'), nullable=False)
    address = db.Column(db.Text)
    phone_number = db.Column(db.String(20))
    registration_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    screenings = db.relationship('Screening', backref='patient', lazy=True)

class Screening(db.Model):
    __tablename__ = 'screenings'
    screening_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(50), db.ForeignKey('patients.patient_id'))
    chw_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    age_months = db.Column(db.Integer)
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    
    # --- ADDED Z-SCORE COLUMNS ---
    haz = db.Column(db.Float)  # Height-for-Age Z-score
    whz = db.Column(db.Float)  # Weight-for-Height Z-score
    waz = db.Column(db.Float)  # Weight-for-Age Z-score
    # -----------------------------

    diarrhea = db.Column(db.Integer)
    anemia = db.Column(db.Integer)
    malaria = db.Column(db.Integer)
    danger_score = db.Column(db.Float)
    status = db.Column(db.String(50))
    proactive_status = db.Column(db.String(100))
    recommendation = db.Column(db.Text)
    next_followup = db.Column(db.DateTime)
    screening_date = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- 5. AUTHENTICATION HELPERS ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated

def generate_patient_id():
    year = datetime.now().year
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PAT-{year}-{rand}"

# --- 6. ENDPOINTS ---

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        session['user_id'] = user.user_id
        session['role'] = user.role
        return jsonify({"message": "Login successful", "role": user.role, "user_id": user.user_id})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/register-patient', methods=['POST'])
@login_required
def register_patient():
    data = request.json
    dob_date = datetime.strptime(data['dob'], '%Y-%m-%d').date()
    today = datetime.now().date()
    
    # 1. Age Validation (Under 5 Only)
    age_in_days = (today - dob_date).days
    if age_in_days > 1825:
        return jsonify({"error": "Age Limit Exceeded", "message": "Children over 5 years cannot be registered."}), 400 

    # 2. Duplicate Check
    existing = Patient.query.filter_by(name=data['name'], parent_full_name=data['parent_name']).first()
    if existing:
        return jsonify({"error": "Duplicate Detected", "message": "Already registered", "existing_id": existing.patient_id}), 409

    # 3. Save Patient
    new_id = generate_patient_id()
    new_patient = Patient(
        patient_id=new_id,
        name=data['name'],
        parent_full_name=data['parent_name'],
        dob=dob_date,
        gender=data['gender'],
        address=data.get('address'),
        phone_number=data.get('phone')
    )
    db.session.add(new_patient)
    db.session.commit()
    return jsonify({"message": "Patient registered", "patient_id": new_id}), 201

@app.route('/patient/<id>', methods=['GET'])
@login_required
def get_patient_details(id):
    patient = Patient.query.get(id)
    if not patient: return jsonify({"error": "Patient not found"}), 404
    
    # Calculate Current Age once here for UI Autofill
    today = datetime.now().date()
    age_months = (today.year - patient.dob.year) * 12 + today.month - patient.dob.month
    
    last = Screening.query.filter_by(patient_id=id).order_by(Screening.screening_date.desc()).first()
    
    return jsonify({
        "identity": {
            "id": patient.patient_id,
            "name": patient.name,
            "parent_name": patient.parent_full_name,
            "dob": patient.dob.strftime('%Y-%m-%d'),
            "current_age_months": age_months,
            "gender": patient.gender,
            "address": patient.address
        },
        "history": {
            "last_status": last.status if last else "New Patient",
            "last_weight": last.weight_kg if last else None,
            "last_date": last.screening_date.strftime('%Y-%m-%d') if last else None
        }
    })

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    data = request.json
    patient = Patient.query.get(data['patient_id'])
    if not patient: 
        return jsonify({"status": "error", "message": "Patient not found"}), 404

    # 1. DYNAMIC AGE & DATA EXTRACTION
    today = datetime.now()
    age_months = (today.year - patient.dob.year) * 12 + today.month - patient.dob.month
    weight = data.get('weight_kg')
    height = data.get('height_cm')

    # 2. VALIDATION (To prevent math errors)
    if not weight or not height:
        return jsonify({"status": "error", "message": "Weight and Height are required."}), 400

    # 3. COMPUTE WHO Z-SCORES & AI PREDICTION
    haz, whz, waz = compute_zscores(age_months, weight, height, patient.gender)
    
    # AI Prediction Logic
    gender_num = 1 if patient.gender.lower() == 'male' else 0
    input_df = pd.DataFrame([[haz, whz, waz, gender_num, data.get('diarrhea', 0), data.get('anemia', 0), data.get('malaria', 0)]], 
                            columns=['haz', 'whz', 'waz', 'Gender', 'Diarrhea', 'Anemia', 'Malaria'])
    
    probs = rf_model.predict_proba(input_df)[0]
    score = round(probs[1] * 100, 1)

    # 4. CLINICAL SEVERITY & RECOMMENDATIONS
    if score >= 70 or whz < -3:
        level, imm, treat, days = "Critical", "Urgent Referral", "Provide RUTF", 7
    elif score >= 40 or whz < -2:
        level, imm, treat, days = "At Risk", "Supplementary Feeding", "Fortified Flour", 14
    else:
        level, imm, treat, days = "Stable", "Standard Monitoring", "Nutritional Counseling", 30

    # XAI Factors for "Why" the AI chose this score
    factors = []
    if whz < -2: factors.append("Low Weight-for-Height (Wasting)")
    if haz < -2: factors.append("Low Height-for-Age (Stunting)")
    if data.get('diarrhea'): factors.append("Active Diarrhea complication")

    # 5. FETCH HISTORY (Support for "Trend" and "Previous" Buttons)
    # We get last 5 visits to provide a rich trend graph
    history_records = Screening.query.filter_by(patient_id=patient.patient_id)\
                                     .order_by(Screening.screening_date.desc())\
                                     .limit(5).all()
    
    # Reverse so the oldest visit is index 0 (correct for charting)
    history_records = history_records[::-1]

    label = "Initial Assessment"
    weight_diff = 0
    trend = "Baseline Visit"

    if history_records:
        last_v = history_records[-1] # The most recent previous visit
        weight_diff = round(weight - last_v.weight_kg, 2)
        if weight_diff > 0.15: label, trend = "Positive Growth Trajectory", "Improving"
        elif weight_diff < 0: label, trend = "High Deterioration Risk", "Declining"
        else: label, trend = "Warning: Faltering Growth", "Stagnating"

    # 6. SAVE CURRENT SCREENING (Include Z-scores in DB columns)
    new_scr = Screening(
        patient_id=patient.patient_id, chw_id=session['user_id'],
        age_months=age_months, weight_kg=weight, height_cm=height,
        haz=haz, whz=whz, waz=waz, # Ensure your DB has these columns!
        diarrhea=data.get('diarrhea', 0), anemia=data.get('anemia', 0), malaria=data.get('malaria', 0),
        danger_score=score, status=level, proactive_status=label,
        recommendation=json.dumps({"imm": imm, "treat": treat}),
        next_followup=today + timedelta(days=days)
    )
    db.session.add(new_scr)
    db.session.commit()

    # 7. FINAL STRUCTURED RESPONSE
    return jsonify({
        "status": "success",
        "timestamp": today.strftime('%Y-%m-%dT%H:%M:%SZ'),
        "child_id": patient.patient_id,
        "child_name": patient.name,

        "current_assessment": {
            "danger_score": f"{score}%",
            "danger_level": level,
            "z_scores": {"HAZ": round(haz, 2), "WAZ": round(waz, 2), "WHZ": round(whz, 2)},
            "recommendations": {
                "followup_days": days,
                "immediate_action": imm,
                "treatment": treat
            },
            "xai": {
                "summary": f"Driven by {', '.join(factors[:2])}." if factors else "Normal development.",
                "primary_factors": factors
            }
        },

       "previous_assessment": {
    "exists": len(history_records) > 0,
    "details": {
        "date": history_records[-1].screening_date.strftime('%Y-%m-%d') if history_records else None,
        "weight": history_records[-1].weight_kg if history_records else None,
        "height": history_records[-1].height_cm if history_records else None,
        "status": history_records[-1].status if history_records else None,
        
        # NULL-SAFE Z-SCORES: Only rounds if the value is not None
        "z_scores": {
            "HAZ": round(history_records[-1].haz, 2) if history_records[-1].haz is not None else None,
            "WAZ": round(history_records[-1].waz, 2) if history_records[-1].waz is not None else None,
            "WHZ": round(history_records[-1].whz, 2) if history_records[-1].whz is not None else None
        } if history_records else None
    }
},
        "comparison_summary": {
            "label": label,
            "weight_change_kg": weight_diff,
            "trend": trend
        },

       "chart_data": {
    "labels": [s.screening_date.strftime('%b %d') for s in history_records] + ["Today"],
    "danger_scores": [s.danger_score for s in history_records] + [score],
    "weights": [s.weight_kg for s in history_records] + [weight],
    # Null-safe WHZ trend
    "whz_trend": [(round(s.whz, 2) if s.whz is not None else 0) for s in history_records] + [round(whz, 2)]
}
    })
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

# --- 7. ADMIN & DASHBOARDS ---

@app.route('/admin/create-chw', methods=['POST'])
@login_required
def create_chw():
    if session.get('role') != 'Admin': return jsonify({"message": "Unauthorized"}), 403
    data = request.json
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(username=data['username'], email=data['email'], password_hash=hashed_pw, role='CHW', is_verified=True)
    db.session.add(new_user); db.session.commit()
    return jsonify({"message": "CHW created successfully!"}), 201

@app.route('/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    if session.get('role') != 'Admin': return jsonify({"message": "Unauthorized"}), 403
    total = Screening.query.count()
    critical = Screening.query.filter_by(status='Critical').count()
    prevalence = db.session.query(Screening.status, db.func.count(Screening.screening_id)).group_by(Screening.status).all()
    return jsonify({"total": total, "critical": critical, "prevalence": dict(prevalence)})

@app.route('/search-patients', methods=['GET'])
@login_required
def search_patients():
    query = request.args.get('q', '')
    results = Patient.query.filter((Patient.name.like(f"%{query}%")) | (Patient.patient_id.like(f"%{query}%"))).all()
    return jsonify([{
        "id": p.patient_id, "name": p.name, "parent": p.parent_full_name,
        "dob": p.dob.strftime('%Y-%m-%d'), "gender": p.gender,
        "last_status": p.screenings[-1].status if p.screenings else "New Patient"
    } for p in results])

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)