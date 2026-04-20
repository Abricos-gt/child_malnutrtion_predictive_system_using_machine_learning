import pandas as pd
import joblib
import os
import numpy as np
import json
import random
import shap
import string
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime, timedelta
from flask_cors import CORS
from sqlalchemy import func, extract


app = Flask(__name__)
app.secret_key = "abrha_secret_key_2026" 
CORS(app, supports_credentials=True, origins=[
    "http://localhost:5173",
    "http://localhost:5177"
])
app.config['JSON_SORT_KEYS'] = False  # Critical for ordered JSON
# --- 1. DATABASE CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456789@127.0.0.1/malnutrition_proactive_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. LOAD AI MODEL PACKAGE ---
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'malnutrition_proactive_model3.pkl')
try:
    model_pkg = joblib.load(model_path)
    rf_model = model_pkg['model']
    # The model expects: [haz, whz, waz, Age_months, Weight_kg, Height_cm, Gender, Diarrhea, Anemia, Malaria]
except Exception as e:
    print(f"Error loading model: {e}")
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
    
    # Weight-for-Age (WAZ)
    L, M, S = get_lms(wfa, "Month", age)
    waz = zscore_calc(weight, L, M, S)
    
    # Height-for-Age (HAZ)
    L, M, S = get_lms(hfa, "Month", age)
    haz = zscore_calc(height, L, M, S)
    
    # Weight-for-Height (WHZ)
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
    haz = db.Column(db.Float)
    whz = db.Column(db.Float)
    waz = db.Column(db.Float)
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
    if (today - dob_date).days > 1825:
        return jsonify({"error": "Age Limit Exceeded"}), 400 
    new_id = generate_patient_id()
    new_patient = Patient(
        patient_id=new_id, name=data['name'], parent_full_name=data['parent_name'],
        dob=dob_date, gender=data['gender'], address=data.get('address'), phone_number=data.get('phone')
    )
    db.session.add(new_patient); db.session.commit()
    return jsonify({"message": "Patient registered", "patient_id": new_id}), 201

@app.route('/predict', methods=['POST'])
@login_required
def predict():
    data = request.json
    patient = db.session.get(Patient, data['patient_id'])
    
    if not patient: 
        return jsonify({"status": "error", "message": "Patient not found"}), 404

    # 1. RAW DATA & DATES
    today = datetime.now()
    age_months = data.get('age_months') 
    weight = data.get('weight_kg')
    height = data.get('height_cm')
    
    if age_months is None:
        return jsonify({"status": "error", "message": "Manual age entry is required."}), 400

    # --- NEW: GROWTH TRAJECTORY LOGIC ---
    # Fetch the most recent screening for this child to compare weights
    prev_screening = Screening.query.filter_by(patient_id=patient.patient_id)\
                        .order_by(Screening.screening_date.desc()).first()

    trajectory_status = "Baseline"
    weight_change = 0
    trend_description = "Initial screening: Establishing health baseline."
    trend_color = "neutral" # Useful for your frontend UI

    if prev_screening:
        weight_change = round(weight - prev_screening.weight_kg, 2)
        if weight_change > 0.1:
            trajectory_status = "Improving"
            trend_description = f"Positive growth detected: Gained {abs(weight_change)}kg since last visit."
            trend_color = "green"
        elif weight_change < -0.1:
            trajectory_status = "Declining"
            trend_description = f"Urgent: Weight loss of {abs(weight_change)}kg detected. Requires attention."
            trend_color = "red"
        else:
            trajectory_status = "Stable"
            trend_description = "Weight is stable (no significant change since last visit)."
            trend_color = "blue"

    # 2. BACKEND CALCULATES Z-SCORES
    haz, whz, waz = compute_zscores(age_months, weight, height, patient.gender)
    
    # 3. PREPARE HYBRID INPUT FOR AI MODEL
    gender_num = 1 if patient.gender.lower() == 'male' else 0
    input_df = pd.DataFrame([[
        haz, whz, waz, age_months, weight, height, gender_num, 
        data.get('diarrhea', 0), data.get('anemia', 0), data.get('malaria', 0)
    ]], columns=['haz', 'whz', 'waz', 'Age_months', 'Weight_kg', 'Height_cm', 
                 'Gender', 'Diarrhea', 'Anemia', 'Malaria'])
    
    # 4. GET AI PREDICTION & CALCULATE DANGER SCORE
    probs = rf_model.predict_proba(input_df)[0]
    score = round((probs[1] * 100) + (probs[0] * 50), 1)

    # 5. SHAP EXPLAINABILITY LOGIC
    try:
        raw_shap = explainer.shap_values(input_df)
        if isinstance(raw_shap, list):
            vals = raw_shap[1][0] if len(raw_shap) > 1 else raw_shap[0][0]
        else:
            vals = raw_shap[0, :, 1] if raw_shap.ndim == 3 else raw_shap[0]
        
        name_map = {
            "whz": "wasting (weight-for-height)", "waz": "being underweight",
            "haz": "stunting (height-for-age)", "malaria": "active malaria infection",
            "diarrhea": "recent diarrhea", "anemia": "signs of anemia",
            "Weight_kg": "extremely low weight", "Age_months": "age-related vulnerability"
        }
        contributions = sorted(zip(input_df.columns, vals), key=lambda x: x[1], reverse=True)
        top_risks = [name_map.get(f.lower(), name_map.get(f, f)) for f, v in contributions if v > 0][:2]
        explanation = f"This score is primarily driven by {top_risks[0]} and {top_risks[1]}." if len(top_risks) >= 2 else "Indicators are within stable ranges."
    except:
        explanation = "AI assessment based on growth standards and clinical signs."

    # 6. UPDATED TRIAGE & FOLLOW-UP DATES
    d48h = (today + timedelta(hours=48)).strftime('%Y-%m-%d')
    d7d = (today + timedelta(days=7)).strftime('%Y-%m-%d')
    d30d = (today + timedelta(days=30)).strftime('%Y-%m-%d')

    if score >= 80 or (whz < -3 and (data.get('malaria') or data.get('diarrhea'))):
        level, imm, treat, follow, next_v, days = "Critical (Emergency)", "Immediate Referral to Stabilization Center (SC)", "Initial phase treatment with F-75 milk", f"Urgent follow-up required within 24-48 hours (By {d48h})", d48h, 2
    elif score >= 60 or whz < -3:
        level, imm, treat, follow, next_v, days = "Critical (OTP)", "Urgent Referral to Health Center", "Provide RUTF (Plumpy'Nut) and Vitamin A", f"Weekly monitoring required. Next visit: {d7d}", d7d, 7
    elif score >= 40 or whz < -2:
        level, imm, treat, follow, next_v, days = "At Risk (MAM)", "Supplementary Feeding Program", "Provide Fortified Flour (CSB++)", f"Bi-weekly monitoring. Next visit: {d7d}", d7d, 7
    else:
        level, imm, treat, follow, next_v, days = "Stable", "Community Monitoring", "Nutritional Counseling and Hygiene Education", f"Standard monthly growth monitoring. Next visit: {d30d}", d30d, 30

    # 7. SAVE SCREENING (Including Trend Info in Recommendation JSON)
    new_scr = Screening(
        patient_id=patient.patient_id, chw_id=session['user_id'],
        age_months=age_months, weight_kg=weight, height_cm=height,
        haz=haz, whz=whz, waz=waz, diarrhea=data.get('diarrhea', 0),
        anemia=data.get('anemia', 0), malaria=data.get('malaria', 0),
        danger_score=score, status=level,
        recommendation=json.dumps({"imm": imm, "treat": treat, "exp": explanation, "follow": follow, "trend": trend_description}),
        next_followup=today + timedelta(days=days), screening_date=today
    )
    db.session.add(new_scr)
    db.session.commit()

    # 8. ENHANCED RESPONSE (Reordered for Clinical Workflow)
    return jsonify({
         
        "child_information": {
            "full_name": patient.name,
            "patient_id": patient.patient_id,
            "date_of_birth": patient.dob.strftime('%Y-%m-%d'),
            "age_at_screening": f"{age_months} months",
            "gender": patient.gender
        },
        "assessment": {
            "danger_score": f"{score}%",
            "triage_level": level,
            "ai_interpretation": explanation,
            "z_scores": {
                "WHZ": round(whz, 2), 
                "HAZ": round(haz, 2), 
                "WAZ": round(waz, 2)
            }
        },
        "growth_trajectory": {
            "status": trajectory_status,
            "weight_change_kg": weight_change,
            "description": trend_description,
            
        },
        "action_plan": {
            "immediate_action": imm,
            "treatment_regimen": treat,
            "follow_up_schedule": follow,
            "next_visit_date": next_v
        }
    })
@app.route('/vhw/patient-dashboard/<patient_id>', methods=['GET'])
@login_required
def vhw_patient_dashboard(patient_id):
    patient = Patient.query.get(patient_id)
    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    # Fetch every screening record for this child
    screenings = db.session.query(Screening, User.username)\
        .join(User, Screening.chw_id == User.user_id)\
        .filter(Screening.patient_id == patient_id)\
        .order_by(Screening.screening_date.desc()).all()

    # Organized Identity Block
    identity = {
        "full_name": patient.name,
        "id": patient.patient_id,
        "dob": patient.dob.strftime('%Y-%m-%d'),
        "gender": patient.gender,
        "parent": patient.parent_full_name
    }

    # Complete Measurement History
    # This list includes every single data point for every visit
    full_measurements = []
    for scr, chw_name in screenings:
        full_measurements.append({
            "visit_date": scr.screening_date.strftime('%Y-%m-%d'),
            "recorded_by": chw_name,
            "clinical_age": f"{scr.age_months} months",
            "physical_stats": {
                "weight_kg": scr.weight_kg,
                "height_cm": scr.height_cm
            },
            "who_z_scores": {
                "WHZ (Wasting)": round(scr.whz, 2),
                "HAZ (Stunting)": round(scr.haz, 2),
                "WAZ (Underweight)": round(scr.waz, 2)
            },
            "clinical_signs": {
                "diarrhea": "Yes" if scr.diarrhea else "No",
                "anemia": "Yes" if scr.anemia else "No",
                "malaria": "Yes" if scr.malaria else "No"
            },
            "ai_assessment": {
                "danger_score": f"{scr.danger_score}%",
                "triage_status": scr.status
            }
        })

    return jsonify({
        "child_identity": identity,
        "history_count": len(full_measurements),
        "complete_medical_record": full_measurements
    })
@app.route('/search-patients', methods=['GET'])
@login_required
def search_patients():
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([]), 200

    # Search pattern for partial matching
    search_pattern = f"%{query}%"
    
    # Updated to use Patient.phone_number to match your database schema
    results = Patient.query.filter(
        (Patient.name.ilike(search_pattern)) | 
        (Patient.patient_id.ilike(search_pattern)) |
        (Patient.phone_number.ilike(search_pattern)) 
    ).limit(20).all() 

    return jsonify([{
        "id": p.patient_id, 
        "full_name": p.name, 
        "parent_name": p.parent_full_name,
        "dob": p.dob.strftime('%Y-%m-%d'), 
        "parent_phone": p.phone_number, # Mapping DB phone_number to JSON parent_phone
        "gender": p.gender,
        "last_status": p.screenings[-1].status if p.screenings else "New Patient"
    } for p in results])



 

@app.route('/api/chw/upcoming-tasks', methods=['GET'])
@login_required
def get_upcoming_tasks():
    # 1. SETUP PAGINATION
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    
    today = datetime.now().date()
    three_days_later = today + timedelta(days=3)

    # 2. GLOBAL VISIBILITY LOGIC (Shared by all CHWs)
    # Find the latest screening for each patient
    latest_screening_ids = db.session.query(
        func.max(Screening.screening_id)
    ).group_by(Screening.patient_id).subquery()

    # 3. FETCH TASKS DUE SOON
    tasks_pagination = Screening.query.filter(
        Screening.screening_id.in_(latest_screening_ids),
        Screening.next_followup >= today,
        Screening.next_followup <= three_days_later
    ).order_by(Screening.next_followup.asc()).paginate(page=page, per_page=per_page)

    task_list = []
    for t in tasks_pagination.items:
        # Fetch only PREVIOUS screenings (history)
        # We exclude the current one (t.screening_id) to show only past data in the table
        history = Screening.query.filter(
            Screening.patient_id == t.patient_id,
            Screening.screening_id != t.screening_id 
        ).order_by(Screening.screening_date.desc()).all()

        task_list.append({
            "patient_id": t.patient_id,
            "name": t.patient.name,
            "due_date": t.next_followup.strftime('%Y-%m-%d'),
            "current_status": t.status,
            "phone": t.patient.phone_number,
            "screen_button_url": f"/predict?patient_id={t.patient_id}",
            "history_table": [{
                "date": h.screening_date.strftime('%Y-%m-%d'),
                "weight": f"{h.weight_kg}kg",
                "height": f"{h.height_cm}cm",
                "status": h.status
            } for h in history]
        })

    return jsonify({
        "tasks": task_list,
        "pagination": {
            "total_items": tasks_pagination.total,
            "current_page": tasks_pagination.page,
            "total_pages": tasks_pagination.pages,
            "has_next": tasks_pagination.has_next
        }
    })


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
    return jsonify({"total_screenings": total})



@app.route('/api/admin/stats', methods=['GET'])
@login_required
def get_admin_stats():
    if session.get('role') != 'Admin':
        return jsonify({"message": "Unauthorized"}), 403

    # 1. SIMPLE COUNTS
    total_children = Patient.query.count()
    total_chws = User.query.filter_by(role='CHW').count()

    # 2. SCREENINGS BY MONTH (Last 6 Months)
    monthly_stats = db.session.query(
        extract('month', Screening.screening_date).label('month'),
        func.count(Screening.screening_id)
    ).group_by('month').order_by('month').all()
    
    screenings_chart = {m: count for m, count in monthly_stats}

    # 3. STATUS TRANSITIONS (The "Improvement vs Deterioration" Logic)
    # We look for patients with at least 2 screenings
    patients = Patient.query.all()
    transitions = {
        "stable_to_critical": 0,
        "critical_to_stable": 0,
        "remained_stable": 0,
        "remained_critical": 0
    }

    for p in patients:
        if len(p.screenings) >= 2:
            # Sort by date to get the last two
            sorted_scr = sorted(p.screenings, key=lambda x: x.screening_date)
            prev_status = sorted_scr[-2].status
            curr_status = sorted_scr[-1].status

            # Simple logic: define 'Critical' as SAM or Emergency
            was_critical = "Severe" in prev_status or "Emergency" in prev_status
            is_critical = "Severe" in curr_status or "Emergency" in curr_status

            if not was_critical and is_critical:
                transitions["stable_to_critical"] += 1
            elif was_critical and not is_critical:
                transitions["critical_to_stable"] += 1
            elif was_critical and is_critical:
                transitions["remained_critical"] += 1
            else:
                transitions["remained_stable"] += 1

    return jsonify({
        "summary": {
            "total_children": total_children,
            "total_chws": total_chws,
            "total_screenings": sum(screenings_chart.values())
        },
        "monthly_activity": screenings_chart,
        "patient_outcomes": transitions
    })

@app.route('/api/admin/reset-password', methods=['POST'])
@login_required
def admin_reset_password():
    # Security Check: Only allow 'Admin' role
    if session.get('role') != 'Admin':
        return jsonify({"status": "error", "message": "Access denied. Admin privileges required."}), 403

    data = request.json
    username_to_reset = data.get('username')
    new_password = data.get('new_password')

    if not username_to_reset or not new_password:
        return jsonify({"status": "error", "message": "Username and new password are required."}), 400

    # Find the target user
    user = User.query.filter_by(username=username_to_reset).first()

    if not user:
        return jsonify({"status": "error", "message": "User not found."}), 404

    # Update the password hash
    user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    
    try:
        db.session.commit()
        return jsonify({
            "status": "success", 
            "message": f"Password for '{username_to_reset}' updated successfully."
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/api/user/change-password', methods=['POST'])
@login_required
def change_own_password():
    # Use session to get the ID of the currently logged-in user
    user_id = session.get('user_id')
    data = request.json
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"status": "error", "message": "Both current and new passwords are required."}), 400

    user = db.session.get(User, user_id)

    # 1. Verify the OLD password first (Security Best Practice)
    from werkzeug.security import check_password_hash
    if not check_password_hash(user.password_hash, current_password):
        return jsonify({"status": "error", "message": "Incorrect current password."}), 401

    # 2. Update to the NEW password
    user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    
    try:
        db.session.commit()
        return jsonify({"status": "success", "message": "Your password has been updated successfully."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": "Database error occurred."}), 500
if __name__ == '__main__':
    with app.app_context(): db.create_all()
    app.run(debug=True)