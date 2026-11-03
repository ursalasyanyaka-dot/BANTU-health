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

# Bemba Translation Aliases
bemba_to_english = {
    'nde unfwa umubili nau kaba': 'fever',
    'nde unfwa umutwe ule kalipa': 'headache',
    'nin jamba uku kola sana': 'cough',
    'nindwala shiki': 'diarrhea',
    'chifuba chule kalipa': 'chest pain',
    'umubili wandi nau kaba': 'fever',
    'nda lwala umutwe': 'headache',
    'inda yalabila': 'stomach ache',
    'ndi na malali': 'malaria'
}

# Helper to look up Clinics from clinics.jsn
def get_clinic_by_district(district_name):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        clinics_path = os.path.join(base_dir, 'clinics.json')
        if os.path.exists(clinics_path):
            with open(clinics_path, 'r', encoding='utf-8') as f:
                clinics = json.load(f)
                # Filter matching district case-insensitively
                filtered = [c for c in clinics if c['district'].lower() == district_name.lower()]
                if filtered:
                    clinic = filtered[0]
                    nhima_status = "Accepted" if clinic['nhima_accepted'] else "Not Accepted"
                    return f"{clinic['name']} | Phone: {clinic['phone']} | NHIMA: {nhima_status} | Hours: {clinic['hours']}"
    except Exception:
        pass
    return "Chilenje Level 1 Hospital | Phone: 0211-272123 | NHIMA: Accepted | Hours: 24/7 (Default)"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip().lower()
    district = data.get('district', 'chilenje').strip().lower()
    
    # Translate Bemba to English if applicable
    if user_message in bemba_to_english:
        user_message = bemba_to_english[user_message]
    
    # Check symptom dictionary
    if user_message in Symptoms:
        advice = Symptoms[user_message]['advice']
        severity = Symptoms[user_message]['severity']
        clinic_info = get_clinic_by_district(district)
        
        reply = f"[{severity.upper()} SEVERITY] {advice.capitalize()}. Recommended clinic in {district.title()}: {clinic_info}."
        
        # Save query to database with timestamp, symptom, district, and advice
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('INSERT INTO queries (timestamp, symptom, district, advice) VALUES (?, ?, ?, ?)', 
                  (timestamp_str, user_message, district, advice))
        conn.commit()
        conn.close()
        
    elif user_message in ['hi', 'hello', 'muli bwanji', 'start']:
        reply = "Muli bwanji! I am your health assistant. Please tell me your symptom in English or Bemba."
    else:
        reply = "Symptom not recognized. Please consult a doctor or visit your nearest health center."

    return jsonify({'reply': reply})

@app.route('/dashboard')
def dashboard():
    return render_template('stats.html')

@app.route('/stats', methods=['GET'])
def stats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Total queries count
    c.execute('SELECT COUNT(*) FROM queries')
    total_queries = c.fetchone()[0]
    
    # Top 3 symptoms searched
    c.execute("""
        SELECT symptom, COUNT(*) as count
        FROM queries
        GROUP BY symptom
        ORDER BY count DESC
        LIMIT 3
    """)
    top_symptoms = [{'symptom': row[0], 'count': row[1]} for row in c.fetchall()]
    
    # Busiest district
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