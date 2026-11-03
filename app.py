from flask import Flask, jsonify, request, render_template
import sqlite3
import os
import json
import datetime

app = Flask(__name__)
DB_NAME = 'queries.db'

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

# Helper to look up and filter Clinics by NHIMA and 24/7 Hours
def get_filtered_clinic_by_district(district_name, nhima_required=False, hours_247_required=False):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        clinics_path = os.path.join(base_dir, 'clinics.json')
        if os.path.exists(clinics_path):
            with open(clinics_path, 'r', encoding='utf-8') as f:
                clinics = json.load(f)
                filtered = [c for c in clinics if c['district'].lower() == district_name.lower()]
                
                if nhima_required:
                    filtered = [c for c in filtered if str(c.get('nhima_accepted', '')).lower() in ['yes', 'true', 'accepted']]
                
                if hours_247_required:
                    filtered = [c for c in filtered if '24/7' in str(c.get('hours', ''))]
                
                if filtered:
                    clinic = filtered[0]
                    nhima_status = "Accepted" if clinic.get('nhima_accepted') else "Not Accepted"
                    return f"{clinic['name']} | Phone: {clinic.get('phone', 'N/A')} | NHIMA: {nhima_status} | Hours: {clinic.get('hours', '24/7')}"
    except Exception:
        pass
    return "Chilenje Level 1 Hospital | Phone: 0211-272123 | NHIMA: Accepted | Hours: 24/7 (Default)"

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

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip().lower()
    district = data.get('district', 'chilenje').strip()
    nhima_only = data.get('nhima_only', False)
    hours_247_only = data.get('hours_247_only', False)
    
    # 1. Check for local language alias match first
    translated_symptom = bemba_to_english.get(user_message, user_message)

    # 2. Support multi-condition matching
    detected_conditions = []
    highest_severity = 'low'
    severity_rank = {'low': 1, 'medium': 2, 'high': 3}

    for symptom_key, info in Symptoms.items():
        if symptom_key in translated_symptom or symptom_key in user_message:
            detected_conditions.append((symptom_key, info))
            if severity_rank.get(info['severity'], 1) > severity_rank.get(highest_severity, 1):
                highest_severity = info['severity']

    # 3. Formulate the response
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

    # 4. Append recommended clinic with all filters applied
    clinic_info = get_filtered_clinic_by_district(district, nhima_required=nhima_only, hours_247_required=hours_247_only)
    reply += f"<br><br>Recommended clinic: {clinic_info}"

    # 5. Log query into SQLite database
    primary_symptom = detected_conditions[0][0] if detected_conditions else "unknown"
    log_query_to_db(primary_symptom, district, reply)

    return jsonify({'reply': reply})

@app.route('/dashboard')
def dashboard():
    return render_template('stats.html')

@app.route('/stats', methods=['GET'])
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

if __name__ == '__main__':
    app.run(debug=True)