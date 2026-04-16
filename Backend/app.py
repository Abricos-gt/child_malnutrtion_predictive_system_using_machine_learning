import pandas as pd
import joblib
import os
import shap
import numpy as np
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

# --- 2b. INITIALIZE SHAP EXPLAINER ---
explainer = shap.TreeExplainer(rf_model)

# --- 2c. WHO Z-SCORE TABLES & ENGINE ---
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
    wfa = wfa_b if g == "male" else wfa_g
    hfa = hfa_b if g == "male" else hfa_g
    wfh = wfh_b if g == "male" else wfh_g

    L, M, S = get_lms(wfa, "Month", age)
    waz = zscore_calc(weight, L, M, S)
    L, M, S = get_lms(hfa, "Month", age)
    haz = zscore_calc(height, L, M, S)
    h_col = "Height_Length" if "Height_Length" in wfh.columns else "Height"
    L, M, S = get_lms(wfh, h_col, height)
    whz = zscore_calc(weight, L, M, S)
    return haz, whz, waz

# --- 3. DATABASE MODELS (Aligned with SQL Script) ---
class User(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.Enum('Admin', 'CHW'), nullable=False)

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

# --- 4. ACCESS CONTROL & AUTH ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        password_hash=hashed_password,
        full_name=data.get('full_name', ''),
        role=data.get('role', 'CHW')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered successfully"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        session['user_id'] = user.user_id
        session['role'] = user.role
        return jsonify({"message": "Login successful", "role": user.role})
    return jsonify({"message": "Invalid credentials"}), 401

# --- 5. AI PREDICT ENGINE ---
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    data = request.json
    
    # A. Pre-processing
    gender_str = data['gender'].capitalize() # Ensure 'Male' or 'Female'
    gender_num = 1 if gender_str == 'Male' else 0
    
    haz, whz, waz = compute_zscores(
        data['age_months'], data['weight_kg'], data['height_cm'], gender_str
    )
    
    # B. Model Alignment
    input_df = pd.DataFrame([[
        haz, whz, waz, gender_num, 
        data['diarrhea'], data['anemia'], data['malaria']
    ]], columns=final_features)
    
    # C. Prediction
    probs = rf_model.predict_proba(input_df)[0]
    score = round(probs[1] * 100, 1)
    
    # D. SHAP XAI
    shap_values = explainer.shap_values(input_df)
    if isinstance(shap_values, list):
        local_contrib = np.array(shap_values[1]).flatten()
    elif len(shap_values.shape) == 3:
        local_contrib = shap_values[0, :, 1]
    else:
        local_contrib = np.array(shap_values[0]).flatten()

    clinical_names = {'haz': 'Chronic Stunting (HAZ)', 'whz': 'Acute Wasting (WHZ)', 
                      'waz': 'Underweight (WAZ)', 'Gender': 'Biological Factor',
                      'diarrhea': 'Diarrhea', 'anemia': 'Anemia', 'malaria': 'Malaria'}

    risks = []
    for i, contrib in enumerate(local_contrib):
        if float(contrib) > 0:
            feat = final_features[i]
            risks.append({"display": clinical_names.get(feat, feat), "val": float(contrib)})

    risks = sorted(risks, key=lambda x: x['val'], reverse=True)
    top_driver = risks[0]['display'] if risks else "Standard Growth Variance"

    # E. Status Mapping
    if score >= 70:
        status, base_rec = "Critical", "Immediate clinical referral required."
    elif score >= 40:
        status, base_rec = "At Risk", "Initiate therapeutic feeding."
    else:
        status, base_rec = "Stable", "Continue standard monitoring."

    # F. SAVE TO DATABASE (Relational Logic)
    # 1. Handle Patient
    patient = Patient.query.filter_by(name=data['patient_name']).first()
    if not patient:
        patient = Patient(name=data['patient_name'], gender=gender_str)
        db.session.add(patient)
        db.session.flush()

    # 2. Handle Screening
    full_rec = f"{base_rec} Focus on {top_driver}."
    new_screening = Screening(
        patient_id=patient.patient_id,
        chw_id=session['user_id'],
        age_months=data['age_months'],
        weight_kg=data['weight_kg'],
        height_cm=data['height_cm'],
        diarrhea=data['diarrhea'],
        anemia=data['anemia'],
        malaria=data['malaria'],
        danger_score=score,
        status=status,
        recommendation=full_rec
    )
    db.session.add(new_screening)
    db.session.commit()

    return jsonify({
        "danger_score": f"{score}%",
        "status": status,
        "z_scores": {"HAZ": round(haz, 2), "WHZ": round(whz, 2), "WAZ": round(waz, 2)},
        "primary_risk": top_driver,
        "recommendation": full_rec
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)