import pandas as pd
import joblib
import os
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = "abrha_secret_key_2026" 

# --- 1. DATABASE CONFIGURATION ---
# Using 127.0.0.1 to avoid localhost resolution issues found earlier
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456789@127.0.0.1/malnutrition_proactive_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. LOAD AI MODEL PACKAGE ---
base_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(base_dir, 'malnutrition_proactive_model.pkl')
model_pkg = joblib.load(model_path)
rf_model = model_pkg['model']
final_features = model_pkg['features']

# --- 3. DATABASE MODELS ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='CHW') 

class Screening(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100))
    chw_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    age_months = db.Column(db.Integer)
    weight_kg = db.Column(db.Float)
    height_cm = db.Column(db.Float)
    muac = db.Column(db.Float)
    diarrhea = db.Column(db.Integer)
    anemia = db.Column(db.Integer)
    malaria = db.Column(db.Integer)
    danger_score = db.Column(db.Float)
    status = db.Column(db.String(50))
    top_driver = db.Column(db.String(50)) 

# --- 4. ACCESS CONTROL DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"message": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated

# --- 5. AUTHENTICATION ROUTES (ADD THESE) ---
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"message": "User already exists"}), 400
    
    hashed_pw = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(
        username=data['username'],
        password_hash=hashed_pw,
        role=data.get('role', 'CHW')
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": f"User {data['username']} created successfully."})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    
    # Safety Check: Ensure the keys exist in the JSON
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"message": "Missing username or password in request"}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({"message": "Login successful", "role": user.role})
    
    return jsonify({"message": "Invalid credentials"}), 401

# --- 6. THE PROACTIVE AI & XAI ENGINE ---
@app.route('/predict', methods=['POST'])
@login_required
def predict():
    data = request.json
    raw_data = [
        data['age_months'], data['weight_kg'], data['height_cm'],
        data['diarrhea'], data['anemia'], data['malaria']
    ]
    
    input_df = pd.DataFrame([raw_data], columns=final_features)
    probs = rf_model.predict_proba(input_df)[0]
    score = round((probs[0] * 50) + (probs[1] * 100), 1)
    
    importances = rf_model.feature_importances_
    impacts = [importances[i] * raw_data[i] for i in range(len(importances))]
    top_driver = final_features[impacts.index(max(impacts))]

    if score >= 75:
        status, rec = "Critical", "Urgent referral to Stabilization Center."
    elif score >= 50:
        status, rec = "At Risk", "Initiate supplementary feeding program."
    elif score >= 20:
        status, rec = "Borderline", "Nutritional education and follow-up."
    else:
        status, rec = "Normal", "Continue standard growth monitoring."

    new_entry = Screening(
        patient_name=data['patient_name'],
        chw_id=session['user_id'],
        age_months=data['age_months'],
        weight_kg=data['weight_kg'],
        height_cm=data['height_cm'],
        muac=data['muac'],
        diarrhea=data['diarrhea'],
        anemia=data['anemia'],
        malaria=data['malaria'],
        danger_score=score,
        status=status,
        top_driver=top_driver
    )
    db.session.add(new_entry)
    db.session.commit()

    return jsonify({
        "danger_score": f"{score}%",
        "status": status,
        "xai_factor": top_driver.replace('_', ' '),
        "recommendation": rec
    })

# --- 7. ADMIN ANALYTICS ---
@app.route('/admin/dashboard')
@login_required
def admin_summary():
    if session.get('role') != 'Admin':
        return jsonify({"message": "Access Denied"}), 403
    
    stats = {
        "total_screened": Screening.query.count(),
        "avg_risk": db.session.query(db.func.avg(Screening.danger_score)).scalar() or 0,
        "malnourished_count": Screening.query.filter_by(status="Critical").count()
    }
    return jsonify(stats)

if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
    app.run(debug=True)