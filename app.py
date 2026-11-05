from flask import Flask, jsonify, request, render_template, make_response
from flask_httpauth import HTTPBasicAuth
import sqlite3
import os
import json
import datetime
import csv
import difflib
import math
from dotenv import load_dotenv

app = Flask(__name__)
auth = HTTPBasicAuth()
DB_NAME = 'queries.db'

#load virtual credentials
load_dotenv()

# Define users and their roles
USERS_ROLES = {
    "admin": os.getenv("ADMIN_PASSWORD"),
    "health_worker": os.getenv("HEALTH_WORKER_PASSWORD")
}

@auth.verify_password
def verify_password(username, password):
    if username in USERS_ROLES and USERS_ROLES[username] == password:
        return username
    return None

# Initialize the database with all required columns
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symptom TEXT NOT NULL,
            district TEXT NOT NULL,
            advice TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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

# PUBLIC CHAT ROUTE WITH FUZZY MATCHING & GPS SUPPORT
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip().lower()
    district = data.get('district', 'chilenje').strip()
    nhima_only = data.get('nhima_only', False)
    hours_247_only = data.get('hours_247_only', False)
    user_lat = data.get('lat', None)
    user_lon = data.get('lon', None)

    # 1. Check local language alias match first
    translated_symptom = bemba_to_english.get(user_message, user_message)

    detected_conditions = []
    highest_severity = 'low'
    severity_rank = {'low': 1, 'medium': 2, 'high': 3}

    # 2. Tokenize words to support fuzzy/typo matching
    words = user_message.split()

    for symptom_key, info in Symptoms.items():
        if symptom_key in translated_symptom or symptom_key in user_message:
            if (symptom_key, info) not in detected_conditions:
                detected_conditions.append((symptom_key, info))
        else:
            matches = difflib.get_close_matches(symptom_key, words, n=1, cutoff=0.6)
            if matches:
                if (symptom_key, info) not in detected_conditions:
                    detected_conditions.append((symptom_key, info))

        for _, inf in detected_conditions:
            if severity_rank.get(inf['severity'], 1) > severity_rank.get(highest_severity, 1):
                highest_severity = inf['severity']

    # 3. Formulate response
    if detected_conditions:
        advice_parts = []
        for symptom_key, info in detected_conditions:
            advice_parts.append(f"• **{symptom_key.capitalize()}**: {info['advice']}")
        
        advice_text = "<br>".join(advice_parts)
        if highest_severity == 'high':
            advice_text = "⚠️ **URGENT MEDICAL ATTENTION RECOMMENDED**<br>" + advice_text

        reply = f"Analysis for: '{user_message}'<br>{advice_text}"
    else:
        reply = f"I didn't recognize specific symptoms in '{user_message}'. Try typing common symptoms like 'fever', 'headache', 'chest pain', or phrases like 'mutu ukupweteka'."

    # 4. Append recommended clinic using GPS coordinates & filters
    clinic_info = get_nearest_clinic_by_gps(user_lat, user_lon, district, nhima_required=nhima_only, hours_247_required=hours_247_only)
    reply += f"<br><br>Recommended clinic: {clinic_info}"

    # 5. Log query into SQLite database
    primary_symptom = detected_conditions[0][0] if detected_conditions else "unknown"
    log_query_to_db(primary_symptom, district, reply)

    return jsonify({'reply': reply})

# PROTECTED DASHBOARD (Requires Admin or Health Worker Login)
@app.route('/dashboard')
@auth.login_required
def dashboard():
    return render_template('stats.html')

# PROTECTED STATS API ROUTE
@app.route('/stats', methods=['GET'])
@auth.login_required
def stats():
    conn = sqlite3.connect(DB_NAME)
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
@app.route('/export', methods=['GET'])
@auth.login_required
def export_csv():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT id, timestamp, symptom, district, advice FROM queries ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()

    csv_output = "id,timestamp,symptom,district,advice\n"
    for row in rows:
        clean_advice = row[4].replace('<br>', ' ').replace('<strong>', '').replace('</strong>', '')
        csv_output += f"{row[0]},{row[1]},{row[2]},{row[3]},\"{clean_advice}\"\n"

    response = make_response(csv_output)
    response.headers["Content-Disposition"] = "attachment; filename=bantu_health_queries.csv"
    response.headers["Content-Type"] = "text/csv"
    return response

if __name__ == '__main__':
    app.run(debug=True)