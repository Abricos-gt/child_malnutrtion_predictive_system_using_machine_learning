 🚀 Proactive Child Malnutrition Prediction System
AI-Driven Clinical Decision Support for Humanitarian Settings
This system is a proactive clinical decision support tool designed to combat child malnutrition in internally displaced person (IDP) camps. By combining Random Forest Machine Learning with WHO Clinical Standards, it identifies high-risk children before severe wasting occurs, providing actionable treatment plans for Community Health Workers (CHWs).

📊 Project Impact & Motivation
In humanitarian crises, identifying malnutrition is often reactive—caught only after physical deterioration. This project shifts the paradigm to proactive surveillance.

Accuracy: 99.28% validation accuracy on clinical datasets.

Explainability: Integrated SHAP values to provide clinicians with the "why" behind every risk score.

Localization: Built specifically for the nutritional landscape of the Tigray region, Ethiopia.

🏗 System Architecture
The project is divided into a decoupled full-stack architecture designed for edge deployment in low-resource environments.

Folder Structure

├── Backend/           # Flask API, AI Model (.pkl), WHO Tables, & SHAP logic
├── Front-End/         # Vue.js Dashboard & Data Visualizations (Chart.js)
├── .env               # Environment variables (DB Credentials)
├── .gitignore         # Version control exclusion
├── requirements.txt   # Python dependency manifest
└── README.md          # Project Documentation

🛠 Technical Stack
Machine Learning: Random Forest Classifier (Benchmarked against XGBoost, SVM, and KNN).

--Interpretability: SHAP (SHapley Additive exPlanations).

--Backend: Flask (Python 3.x), SQLAlchemy.

Database: PostgreSQL / MySQL (Relational health records).

Frontend: Vue.js, Tailwind CSS (Mobile-responsive for field use).

Standards: WHO Child Growth Standards (LMS Method calculation).

🚀 Getting Started
1. Prerequisites
Python 3.10+

Node.js (for Frontend)

Database (MySQL/PostgreSQL)

2. Installation

   # Clone the repository
git clone https://github.com/yourusername/malnutrition-prediction.git

# Install Backend Dependencies
cd Backend
pip install -r ../requirements.txt

# Setup Environment
# Create a .env file and add your DATABASE_URI

3. Running the System

   # Start Flask Server
python app.py

# Start Frontend (in a new terminal)
cd Front-End
npm install
npm run dev

🩺 Clinical Logic & Triage
The system implements a Knowledge-Based Hybrid Recommender. It doesn't just predict; it triages:

Critical (Emergency): Immediate referral to Stabilization Centers (F-75 protocol).

Critical (OTP): Enrollment in Outpatient Therapeutic Programs (RUTF/Plumpy'Nut).

At Risk (MAM): Supplementary feeding (CSB++) and bi-weekly monitoring.

Stable: Community-based growth monitoring and hygiene education.

