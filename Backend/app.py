import pandas as pd
import joblib
import os
import shap
import numpy as np
import json
import secrets
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "abrha_secret_key_2026" 

# --- 1. DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456789@127.0.0.1/malnutrition_proactive_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. LOAD AI MODEL PACKAGE ---
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'malnutrition_proactive_model2.pkl')
model_pkg = joblib.load(model_path)
rf_model = model_pkg['model']
final_features = model_pkg['features'] 

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

# --- 4. DATA VALIDATION (PROFESSIONAL GUARDRAILS) ---
def validate_pediatric_input(data):
    """Ensures input is biologically plausible for children under 5."""
    errors = []
    # Limits based on WHO growth extreme percentiles
    if not (0 <= data.get('age_months', -1) <= 60):
        errors.append("Age must be between 0 and 60 months (Under-5 only).")
    if not (1.5 <= data.get('weight_kg', 0) <= 30.0):
        errors.append("Weight must be between 1.5kg and 30kg.")
    if not (45.0 <= data.get('height_cm', 0) <= 125.0):
        errors.append("Height must be between 45cm and 125cm.")
    return errors

# --- 5. DATABASE MODELS ---
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.Enum('Admin', 'CHW'), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)

class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum('Male', 'Female'))
    screenings = db.relationship('Screening', backref='patient', lazy=True)

class Screening(db.Model):
    __tablename__ = 'screenings'
    screening_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'))
    chw_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    age_months = db.Column(db.Integer)
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    diarrhea = db.Column(db.Integer)
    anemia = db.Column(db.Integer)
    malaria = db.Column(db.Integer)
    danger_score = db.Column(db.Float)
    status = db.Column(db.String(50))
    proactive_status = db.Column(db.String(100))
    recommendation = db.Column(db.Text) # Stored as JSON string
    next_followup = db.Column(db.DateTime)
    screening_date = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- 6. AUTHENTICATION HELPERS ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        if not user.is_verified:
            return jsonify({"message": "Account not verified."}), 403
        session['user_id'] = user.user_id
        session['role'] = user.role
        return jsonify({"message": "Login successful", "role": user.role})
    return jsonify({"message": "Invalid credentials"}), 401

# --- 7. PREDICTION & PROACTIVE ENGINE ---
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    data = request.json
    
    # Validation Check
    errors = validate_pediatric_input(data)
    if errors:
        return jsonify({"error": "Biological Limit Exceeded", "messages": errors}), 400

    gender_str = data['gender'].capitalize()
    gender_num = 1 if gender_str == 'Male' else 0
    haz, whz, waz = compute_zscores(data['age_months'], data['weight_kg'], data['height_cm'], gender_str)
    
    # 1. AI Prediction
    final_features = ['haz', 'whz', 'waz', 'Gender', 'Diarrhea', 'Anemia', 'Malaria']
    input_df = pd.DataFrame([[haz, whz, waz, gender_num, data['diarrhea'], data['anemia'], data['malaria']]], columns=final_features)
    probs = rf_model.predict_proba(input_df)[0]
    score = round(probs[1] * 100, 1)
    
    # 2. SHAP Filtering
    explainer = shap.TreeExplainer(rf_model)
    shap_values = explainer.shap_values(input_df)
    local_contrib = np.array(shap_values[1] if isinstance(shap_values, list) else shap_values).flatten()

    clinical_names = {'haz': 'Chronic Stunting', 'whz': 'Acute Wasting', 'waz': 'Underweight'}
    symptoms_map = {'Diarrhea': 'diarrhea', 'Anemia': 'anemia', 'Malaria': 'malaria'}
    
    risks = []
    for i, val in enumerate(local_contrib):
        if i < len(final_features):
            feat_name = final_features[i]
            is_present = data.get(symptoms_map[feat_name]) == 1 if feat_name in symptoms_map else True
            if is_present and val > 0:
                risks.append({"display": feat_name, "val": float(val)})
    
    risks = sorted(risks, key=lambda x: x['val'], reverse=True)

    # 3. Interpretation & Severity
    if any(data.get(s) == 1 for s in ['diarrhea', 'anemia', 'malaria']):
        top_driver = risks[0]['display'] if risks else "Active Infection"
    elif whz < -1: top_driver = "Acute Wasting"
    else: top_driver = "No immediate clinical risk"

    if score >= 70 or whz < -3: status, imm, short = "Critical", "Immediate Referral", "Therapeutic Feeding (RUTF)"
    elif score >= 40 or whz < -2: status, imm, short = "At Risk", "Clinical Consultation", "Supplementary Feeding"
    elif -2 <= whz <= -1: status, imm, short = "Borderline", "Close Monitoring", "Nutritional Counseling"
    else: status, imm, short = "Stable", "Standard Monitoring", "Nutritional Counseling"

    # 4. Growth Velocity (Proactive)
    early_flags = []
    proactive_status = "Initial Assessment: Baseline Established"
    patient = Patient.query.filter_by(name=data['patient_name']).first()
    if not patient:
        patient = Patient(name=data['patient_name'], gender=gender_str)
        db.session.add(patient); db.session.flush()
    
    prev = Screening.query.filter_by(patient_id=patient.patient_id).order_by(Screening.screening_date.desc()).first()
    if prev:
        diff = round(data['weight_kg'] - prev.weight_kg, 2)
        if diff < 0:
            proactive_status = "High Deterioration Risk (Weight Loss Detected)"
            early_flags.append(f"Weight Loss: {abs(diff)}kg")
        elif diff < 0.15:
            proactive_status = "Warning: Faltering Growth Pattern"
            early_flags.append("Insufficient gain")
        else: proactive_status = "Positive Growth Trajectory"

    # 5. Age-Specific & Follow-up logic
    age = data['age_months']
    if age < 6: prev_advice = "Exclusive breastfeeding support."
    elif age <= 24: prev_advice = "Nutrient-dense complementary foods."
    else: prev_advice = "General dietary diversity."

    if status in ["Critical", "At Risk"] or "Weight Loss" in proactive_status:
        days, follow_up = 2, "Immediate reassessment (24-48h)"
    elif status == "Borderline" or "Faltering" in proactive_status:
        days, follow_up = 10, "Recheck in 7–14 days"
    else:
        days, follow_up = 30, "Next screening in 30 days"

    next_date = datetime.now() + timedelta(days=days)
    rec_dict = {"immediate": imm, "short_term": short, "preventive": prev_advice, "follow_up": follow_up}
    
    # 6. Save
    new_scr = Screening(
        patient_id=patient.patient_id, chw_id=session['user_id'],
        age_months=age, weight_kg=data['weight_kg'], height_cm=data['height_cm'],
        diarrhea=data['diarrhea'], anemia=data['anemia'], malaria=data['malaria'],
        danger_score=score, status=status, proactive_status=proactive_status,
        recommendation=json.dumps(rec_dict), next_followup=next_date
    )
    db.session.add(new_scr); db.session.commit()

    return jsonify({"danger_score": f"{score}%", "status": status, "proactive_status": proactive_status, "recommendation": rec_dict})

# --- 8. PROFESSIONAL DASHBOARDS ---

@app.route('/chw/dashboard', methods=['GET'])
@login_required
def chw_dashboard():
    """CHW focused view: Action-oriented tasks and recent history."""
    chw_id = session['user_id']
    # 1. Overdue Tasks
    overdue = Screening.query.filter(
        Screening.chw_id == chw_id,
        Screening.next_followup <= datetime.now()
    ).all()
    
    # 2. Recent activity
    recent = Screening.query.filter_by(chw_id=chw_id).order_by(Screening.screening_date.desc()).limit(10).all()
    
    return jsonify({
        "tasks_overdue": [{"patient": s.patient.name, "due": s.next_followup} for s in overdue],
        "recent_screenings": [{"name": s.patient.name, "status": s.status, "date": s.screening_date} for s in recent]
    })

@app.route('/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    """Admin view: Public health prevalence and CHW oversight."""
    if session.get('role') != 'Admin': return jsonify({"message": "Unauthorized"}), 403
    
    total = Screening.query.count()
    critical_count = Screening.query.filter_by(status='Critical').count()
    
    # Find hotspots (Patients with high risk)
    prevalence = db.session.query(Screening.status, db.func.count(Screening.screening_id)).group_by(Screening.status).all()
    
    return jsonify({
        "system_stats": {
            "total_screenings": total,
            "critical_cases": critical_count,
            "prevalence_summary": dict(prevalence)
        },
        "inventory_alert": "HIGH" if critical_count > (total * 0.1) else "STABLE"
    })

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)