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

explainer = shap.TreeExplainer(rf_model)

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
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True) # Null until verification
    role = db.Column(db.Enum('Admin', 'CHW'), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)

class Patient(db.Model):
    __tablename__ = 'patients'
    patient_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.Enum('Male', 'Female'))

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
    recommendation = db.Column(db.Text)
    screening_date = db.Column(db.DateTime, default=db.func.current_timestamp())

# --- 5. AUTHENTICATION & VERIFICATION ---
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
            return jsonify({"message": "Account not verified. Check your email."}), 403
        session['user_id'] = user.user_id
        session['role'] = user.role
        return jsonify({"message": "Login successful", "role": user.role})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/admin/invite_chw', methods=['POST'])
@login_required
def invite_chw():
    if session.get('role') != 'Admin':
        return jsonify({"message": "Admin access required"}), 403
    data = request.json
    token = secrets.token_urlsafe(32)
    new_chw = User(
        username=data['username'],
        email=data['email'],
        role='CHW',
        verification_token=token,
        is_verified=False
    )
    db.session.add(new_chw)
    db.session.commit()
    return jsonify({
        "message": "CHW Invitation Created",
        "verification_link": f"http://127.0.0.1:5000/verify/{token}"
    })

@app.route('/verify/<token>', methods=['POST'])
def verify_account(token):
    data = request.json
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        return jsonify({"message": "Invalid or expired token"}), 400
    
    user.password_hash = generate_password_hash(data['password'])
    user.is_verified = True
    user.verification_token = None
    db.session.commit()
    return jsonify({"message": "Account verified successfully. You can now login."})

# --- 6. PROACTIVE PREDICT ENGINE ---
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    data = request.json
    gender_str = data['gender'].capitalize()
    gender_num = 1 if gender_str == 'Male' else 0
    haz, whz, waz = compute_zscores(data['age_months'], data['weight_kg'], data['height_cm'], gender_str)
    
    input_df = pd.DataFrame([[haz, whz, waz, gender_num, data['diarrhea'], data['anemia'], data['malaria']]], columns=final_features)
    probs = rf_model.predict_proba(input_df)[0]
    score = round(probs[1] * 100, 1)
    
    # SHAP Logic
    shap_values = explainer.shap_values(input_df)
    local_contrib = np.array(shap_values[1]).flatten() if isinstance(shap_values, list) else np.array(shap_values[0]).flatten()
    
    clinical_names = {'haz': 'Chronic Stunting', 'whz': 'Acute Wasting', 'waz': 'Underweight', 'Gender': 'Biological Factor', 'diarrhea': 'Diarrhea', 'anemia': 'Anemia', 'malaria': 'Malaria'}
    risks = sorted([{"display": clinical_names.get(final_features[i], final_features[i]), "val": float(contrib)} for i, contrib in enumerate(local_contrib) if contrib > 0], key=lambda x: x['val'], reverse=True)

    if score < 10 and not (data['diarrhea'] or data['malaria']):
        top_driver = "No Immediate Risk Factor"
    else:
        top_driver = risks[0]['display'] if risks else "Growth Maintenance"

    # Patient History & Proactive Logic
    patient = Patient.query.filter_by(name=data['patient_name']).first()
    if not patient:
        patient = Patient(name=data['patient_name'], gender=gender_str)
        db.session.add(patient); db.session.flush(); db.session.refresh(patient)
    
    prev_visit = Screening.query.filter_by(patient_id=patient.patient_id).order_by(Screening.screening_date.desc()).first()

    if score >= 70: status, imm, short = "Critical", "Emergency Clinical Referral", "Therapeutic Feeding (RUTF)"
    elif score >= 40: status, imm, short = "At Risk", "Clinical Consultation", "Supplementary Feeding"
    else: status, imm, short = "Stable", "Standard Monitoring", "Nutritional Counseling"

    early_flags = []
    if whz < -3: early_flags.append("Severe wasting detected")
    if data['diarrhea'] and data['malaria']: early_flags.append("Active infection cluster (High Risk)")
    
    if prev_visit:
        weight_diff = data['weight_kg'] - prev_visit.weight_kg
        if weight_diff < 0:
            proactive_status = "High Deterioration Risk (Negative Velocity)"
            early_flags.append(f"Rapid Weight Loss: {round(abs(weight_diff), 2)}kg lost since last visit")
            imm, short = "Urgent Nutritional Assessment", "High-protein supplementation"
        else: proactive_status = "Healthy / Growth Maintained" if score < 20 else "Stable / Improving Trajectory"
    else:
        proactive_status = "Healthy but Monitor for Stability" if score < 20 else "Initial Baseline Assessment"

    rec_dict = {"immediate": imm, "short_term": short, "preventive": "Maintain balanced nutrition and hygiene practices"}
    new_screening = Screening(patient_id=patient.patient_id, chw_id=session['user_id'], age_months=data['age_months'], weight_kg=data['weight_kg'], height_cm=data['height_cm'], diarrhea=data['diarrhea'], anemia=data['anemia'], malaria=data['malaria'], danger_score=score, status=status, recommendation=json.dumps(rec_dict))
    db.session.add(new_screening); db.session.commit()

    return jsonify({"danger_score": f"{score}%", "status": status, "proactive_status": proactive_status, "primary_risk": top_driver, "early_warning_flags": early_flags, "recommendation": rec_dict, "z_scores": {"HAZ": round(haz, 2), "WHZ": round(whz, 2), "WAZ": round(waz, 2)}})

# --- 7. ADMIN DASHBOARD ---
@app.route('/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    if session.get('role') != 'Admin': return jsonify({"message": "Unauthorized"}), 403
    stats = {"total_screenings": Screening.query.count(), "critical": Screening.query.filter_by(status='Critical').count(), "at_risk": Screening.query.filter_by(status='At Risk').count(), "stable": Screening.query.filter_by(status='Stable').count()}
    return jsonify(stats)

@app.route('/routes')
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:50s} {methods:20s} {rule}")
        output.append(line)
    return "<pre>" + "\n".join(output) + "</pre>",

if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)