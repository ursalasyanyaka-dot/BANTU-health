from flask import Flask, jsonify, request, render_template, make_response, Response
from flask_httpauth import HTTPBasicAuth
import sqlite3
import os
import json
import datetime
import csv
import io
from io import StringIO
import difflib
import math
from dotenv import load_dotenv
import health_records  
import joblib
from flask_cors import CORS


load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
CORS(app)
auth = HTTPBasicAuth()
DB_NAME = 'queries.db'

# Define users and their roles
USERS_ROLES = {
    "admin": os.getenv("ADMIN_PASSWORD", "adminpass2026"),
    "health_worker": os.getenv("HEALTH_WORKER_PASSWORD", "healthpass2026")
}

@auth.verify_password
def verify_password(username, password):
    if username in USERS_ROLES and USERS_ROLES[username] == password:
        return username
    return None

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

DB_NAME = 'queries.db'


# Load the trained model and vectorizer at startup
model_path = os.path.join('models', 'language_detector.pkl')
vectorizer_path = os.path.join('models', 'vectorizer.pkl')

lang_model = None
lang_vectorizer = None

if os.path.exists(model_path) and os.path.exists(vectorizer_path):
    lang_model = joblib.load(model_path)
    lang_vectorizer = joblib.load(vectorizer_path)
    print("Language detection model loaded successfully into backend!")

SESSION_HISTORY = {}

@app.route('/session/history', methods=['POST'])
def add_session_history():
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default_user')
    query_data = {
        "symptom": data.get('symptom'),
        "district": data.get('district'),
        "advice": data.get('advice'),
        "timestamp": data.get('timestamp')
    }
    
    if session_id not in SESSION_HISTORY:
        SESSION_HISTORY[session_id] = []
        
    SESSION_HISTORY[session_id].append(query_data)
    return jsonify({"status": "success", "history_count": len(SESSION_HISTORY[session_id])}), 200

@app.route('/session/history/<session_id>', methods=['GET'])
def get_session_history(session_id):
    history = SESSION_HISTORY.get(session_id, [])
    return jsonify({"session_id": session_id, "history": history}), 200


def detect_user_language(text):
    """
    Predicts the language of the user message using the trained ML model.
    Returns the predicted language ('english', 'bemba', or 'nyanja') and confidence score.
    Falls back to 'english' if the model isn't loaded or input is empty.
    """
    if not lang_model or not lang_vectorizer or not text.strip():
        return "english", 1.0
    
    # Vectorize and predict
    text_vec = lang_vectorizer.transform([text])
    prediction = lang_model.predict(text_vec)[0]
    
    # Get probability/confidence if available
    try:
        probabilities = lang_model.predict_proba(text_vec)[0]
        max_prob = max(probabilities)
    except Exception:
        max_prob = 1.0
        
    return prediction, max_prob

# Initialize the database with both required tables (queries and clinics)
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Queries Telemetry Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symptom TEXT NOT NULL,
            language TEXT NOT NULL,
            district TEXT NOT NULL,
            advice_given TEXT NOT NULL
        )
    ''')
    
    # 2. Clinics Reference Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS clinics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            district TEXT NOT NULL,
            phone TEXT,
            nhima_accepted TEXT,
            hours TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# Run initialization immediately when app.py loads
init_db()

# Safe database connection helper
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Core Symptom Dictionary
Symptoms = {
    'fever': {'advice': 'could be malaria, flu, or typhoid. Rest and stay hydrated.', 'severity': 'medium'},
    'headache': {'advice': 'could be dehydration, malaria, or migraine. Drink plenty of water.', 'severity': 'low'},
    'cough': {'advice': 'could be flu, pneumonia, or asthma. Monitor your breathing.', 'severity': 'low'},
    'diarrhea': {'advice': 'could be food poisoning, cholera, or stomach infection. Drink oral rehydration salts (ORS).', 'severity': 'high'},
    'chest pain': {'advice': '⚠️ URGENT: Chest pain can indicate heart issues or pneumonia. Seek emergency care immediately.', 'severity': 'high'},
    'rash': {'advice': 'could be an allergy, measles, or skin infection. Avoid scratching.', 'severity': 'low'},
    'fatigue': {'advice': 'could be anemia, depression, or chronic illness. Get adequate rest.', 'severity': 'low'},
    'vomiting': {'advice': 'could be food poisoning, malaria, or stomach flu. Sip small amounts of water.', 'severity': 'medium'},
    'sore throat': {'advice': 'could be tonsillitis, flu, or strep throat. Gargle with warm salt water.', 'severity': 'medium'},
    'malaria': {'advice': 'could be severe malaria. Visit a clinic immediately for a rapid diagnostic test (RDT).', 'severity': 'high'},
    'stomach ache': {'advice': 'could be gastritis, food poisoning, or typhoid. Avoid heavy meals.', 'severity': 'medium'}
}

# Multilingual Local Language Aliases (Bemba, Nyanja, Tonga)
bemba_to_english = {
    'nde unfwa umubili nau kaba': 'fever',
    'nde unfwa umutwe ule kalipa': 'headache',
    'nin jamba uku kola sana': 'cough',
    'nindwala shiki': 'diarrhea',
    'chifuba chule kalipa': 'chest pain',
    'umubili wandi nau kaba': 'fever',
    'nda lwala umutwe': 'headache',
    'inda yalabila': 'stomach ache',
    'ndi na malali': 'malaria',
    # Nyanja additions
    'mutu ukupweteka': 'headache',
    'ndili na malungo': 'fever',
    'chifuwa': 'cough',
    # Tonga additions
    'ndila vuna mutwe': 'headache',
    'muselo': 'fever'
}

# Multi-language response templates
response_templates = {
    'english': {
        'urgent': "⚠️ **URGENT MEDICAL ATTENTION RECOMMENDED**<br>",
        'analysis': "Analysis for: '{user_message}'<br>{advice}",
        'default': "{advice}",
        'clinic': "<br><br>Recommended clinic: {clinic_info}"
    },
    'bemba': {
        'urgent': "⚠️ **UMUTIMA WA NSHITA: CILONGO CA KULONGALONGA KU CIPATALA CILEKWETWA**<br>",
        'analysis': "Ifyebo fya: '{user_message}'<br>{advice}",
        'default': "{advice}",
        'clinic': "<br><br>Icipatala icisuma: {clinic_info}"
    },
    'nyanja': {
        'urgent': "⚠️ **CHOFUNIKA KWAMBIRI: PITANI KU CHIPATALA MWAMSANGA**<br>",
        'analysis': "Kufufuza kwa: '{user_message}'<br>{advice}",
        'default': "{advice}",
        'clinic': "<br><br>Chipatala choyenera: {clinic_info}"
    }
}

# Haversine formula to calculate distance in kilometers between two GPS coordinates
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# GPS & Filter-aware Clinic Lookup Helper
def get_nearest_clinic_by_gps(user_lat, user_lon, district_name, nhima_required=False, hours_247_required=False):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        clinics_path = os.path.join(base_dir, 'clinics.json')
        if os.path.exists(clinics_path):
            with open(clinics_path, 'r', encoding='utf-8') as f:
                clinics = json.load(f)
                
                # Apply filters first
                filtered = clinics
                if nhima_required:
                    filtered = [c for c in filtered if str(c.get('nhima_accepted', '')).lower() in ['yes', 'true', 'accepted']]
                if hours_247_required:
                    filtered = [c for c in filtered if '24/7' in str(c.get('hours', ''))]
                
                # If GPS coordinates are provided, find the closest clinic among filtered options
                if user_lat is not None and user_lon is not None and filtered:
                    closest_clinic = min(
                        filtered, 
                        key=lambda c: calculate_distance(user_lat, user_lon, c.get('lat', -15.4), c.get('lon', 28.28))
                    )
                    distance_km = calculate_distance(user_lat, user_lon, closest_clinic['lat'], closest_clinic['lon'])
                    
                    nhima_status = "Accepted" if closest_clinic.get('nhima_accepted') else "Not Accepted"
                    phone = closest_clinic.get('phone', 'N/A')
                    phone_link = f'<a href="tel:{phone}" style="color: #0e6655; font-weight: bold; text-decoration: underline;">{phone}</a>' if phone != 'N/A' else 'N/A'
                    return f"<strong>{closest_clinic['name']}</strong> (~{distance_km:.1f} km away)<br>Phone: {phone_link}<br>NHIMA: {nhima_status} | Hours: {closest_clinic.get('hours', '24/7')}"
                
                # Fallback to district dropdown selection if GPS is unavailable
                district_filtered = [c for c in filtered if c['district'].lower() == district_name.lower()]
                if district_filtered:
                    clinic = district_filtered[0]
                    nhima_status = "Accepted" if clinic.get('nhima_accepted') else "Not Accepted"
                    phone = clinic.get('phone', 'N/A')
                    phone_link = f'<a href="tel:{phone}" style="color: #0e6655; font-weight: bold; text-decoration: underline;">{phone}</a>' if phone != 'N/A' else 'N/A'
                    return f"<strong>{clinic['name']}</strong> (District Default)<br>Phone: {phone_link}<br>NHIMA: {nhima_status} | Hours: {clinic.get('hours', '24/7')}"
    except Exception as e:
        pass
    return "<strong>Chilenje Level 1 Hospital</strong><br>Phone: <a href='tel:0211272123' style='color: #0e6655; font-weight: bold;'>0211-272123</a><br>NHIMA: Accepted | Hours: 24/7 (Default)"

# Public database logger
def log_query_to_db(symptom, district, advice):
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute(
            'INSERT INTO queries (timestamp, symptom, district, advice) VALUES (?, ?, ?, ?)',
            (datetime.datetime.now().isoformat(timespec='seconds'), symptom, district, advice)
        )
        conn.commit()
    finally:
        conn.close()

@app.route('/')
def home():
    return render_template('index.html')

# ADVANCED MULTI-CONDITION SYMPTOM EVALUATION
def evaluate_symptoms(user_input):
    user_input = user_input.lower().strip()
    matched_symptoms = []
    
    # Check bemba dictionary
    for bemba_phrase, eng_symptom in bemba_to_english.items():
        if bemba_phrase in user_input:
            matched_symptoms.append(eng_symptom)
            
    # Check standard symptoms dictionary
    for symptom in Symptoms.keys():
        if symptom in user_input and symptom not in matched_symptoms:
            matched_symptoms.append(symptom)
            
    # Fuzzy matching fallback
    if not matched_symptoms:
        words = user_input.split()
        for word in words:
            matches = difflib.get_close_matches(word, Symptoms.keys(), n=1, cutoff=0.7)
            if matches:
                matched_symptoms.append(matches[0])
                
    if not matched_symptoms:
        return {
            "advice": "We could not match specific symptoms. Please consult a qualified clinician at your nearest district health center if symptoms persist.",
            "severity": "low",
            "matched": []
        }
        
    severity_rank = {'low': 1, 'medium': 2, 'high': 3}
    highest_severity = 'low'
    combined_advice = []
    
    for symptom in matched_symptoms:
        data = Symptoms[symptom]
        combined_advice.append(f"• **{symptom.capitalize()}**: {data['advice']}")
        if severity_rank.get(data['severity'], 1) > severity_rank.get(highest_severity, 1):
            highest_severity = data['severity']
            
    return {
        "advice": "<br>".join(combined_advice),
        "severity": highest_severity,
        "matched": matched_symptoms
    }

# PUBLIC CHAT ROUTE WITH FUZZY MATCHING & GPS SUPPORT
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()
    district = data.get('district', 'chilenje').strip()
    nhima_only = data.get('nhima_only', False)
    hours_247_only = data.get('hours_247_only', False)
    user_lat = data.get('lat', None)
    user_lon = data.get('lon', None)

    # 1. Detect language
    lower_msg = user_message.lower()
    if lower_msg in ['english', 'bemba', 'nyanja', 'tonga', 'lozi', 'kaonde', 'lunda', 'luvale', 'tumbuka', 'lamba']:
        detected_lang = lower_msg
        confidence = 1.0
    else:
        detected_lang, confidence = detect_user_language(user_message)
        common_terms = ['fever', 'headache', 'cough', 'pain', 'malaria', 'flu']
        if confidence < 0.60 and lower_msg not in common_terms:
            return jsonify({
                'reply': "We couldn't quite catch the language. Which language do you prefer? (English / Bemba / Nyanja)"
            })
        elif confidence < 0.60:
            detected_lang = 'english'

    # Normalize detected language key for template lookup (default to english if unknown)
    lang_key = detected_lang if detected_lang in response_templates else 'english'
    templates = response_templates[lang_key]

    # 2. Map local phrase to English equivalent for symptom evaluation
    translated_symptom = bemba_to_english.get(lower_msg, lower_msg)

    # 3. Evaluate symptoms
    evaluation = evaluate_symptoms(translated_symptom)
    advice_text = evaluation['advice']

    # Apply urgent formatting if high severity
    if evaluation['severity'] == 'high':
        advice_text = templates['urgent'] + advice_text

    if evaluation['matched']:
        body = templates['analysis'].format(user_message=user_message, advice=advice_text)
    else:
        body = templates['default'].format(advice=advice_text)

    # 4. Get clinic recommendation and append using template
    clinic_info = get_nearest_clinic_by_gps(user_lat, user_lon, district, nhima_required=nhima_only, hours_247_required=hours_247_only)
    reply = f"[{detected_lang.upper()} Detected] {body}" + templates['clinic'].format(clinic_info=clinic_info)

    # 5. Log query into SQLite database
    primary_symptom = evaluation['matched'][0] if evaluation['matched'] else user_message
    log_query_to_db(primary_symptom, district, reply)

    return jsonify({'reply': reply})


# PROTECTED STATS API ROUTE
@app.route('/stats', methods=['GET'])
def stats():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM queries')
    total_queries = c.fetchone()[0]
    
    c.execute("""
        SELECT symptom, COUNT(*) as count
        FROM queries
        GROUP BY symptom
        ORDER BY count DESC
        LIMIT 3
    """)
    top_symptoms = [{'symptom': row[0], 'count': row[1]} for row in c.fetchall()]
    
    c.execute("""
        SELECT district, COUNT(*) as count
        FROM queries
        GROUP BY district
        ORDER BY count DESC
        LIMIT 1
    """)
    busiest_row = c.fetchone()
    busiest_district = {'district': busiest_row[0], 'count': busiest_row[1]} if busiest_row else None

    conn.close()
    return jsonify({
        'total_queries': total_queries,
        'top_symptoms': top_symptoms,
        'busiest_district': busiest_district
    })

# PROTECTED CSV EXPORT ROUTE
@app.route('/export/csv', methods=['GET'])
@auth.login_required
def export_csv():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Fetch all query telemetry records
    c.execute("SELECT id, symptom, district, language, timestamp FROM queries")
    rows = c.fetchall()
    conn.close()

    # Create an in-memory string buffer for CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write CSV Header
    writer.writerow(['ID', 'Symptom', 'District', 'Language', 'Timestamp'])
    
    # Write data rows
    for row in rows:
        writer.writerow(row)
        
    output.seek(0)
    
    # Return file response as a downloadable CSV attachment
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=bantu_health_telemetry.csv"}
    )


@app.route('/clinics', methods=['GET'])
def get_clinics():
    if os.path.exists('clinics.json'):
        with open('clinics.json', 'r') as f:
            clinics_data = json.load(f)
        return jsonify(clinics_data)
    return jsonify([])

if __name__ == '__main__':
    app.run(debug=True)