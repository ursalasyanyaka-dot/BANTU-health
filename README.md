Bantu Health AI - Lusaka Local Health Triage Assistant
Bantu Health AI is a localized telehealth triage prototype designed for Lusaka, Zambia. It provides instant preliminary symptom analysis, multi-condition risk scoring, multilingual support (Bemba, Nyanja, Tonga), and intelligent clinic routing filtering by NHIMA insurance acceptance and 24/7 operating hours.

🌟 Key Features

Multi-Condition Triage & Severity Ranking: Evaluates multiple symptoms in a single input, calculating an overall severity score and providing emergency alerts for high-risk symptoms.
Multilingual Support: Recognizes local language phrasings in Bemba (*"nde unfwa umubili nau kaba"*), Nyanja (*"mutu ukupweteka"*), and Tonga (*"muselo"*).
District Clinic Routing & Filtering: Matches users with local Lusaka health facilities (Chilenje, Matero, Kanyama, Lusaka Central, Chelstone, Kalingalinga, Bauleni, Chawama) with toggles for **NHIMA acceptance** and **24/7 operating hours**.
Real-Time Telemetry Dashboard (`/dashboard`): SQLite query logging tracks search frequency, top symptoms, and busiest districts.
Live Cloud Deployment: Hosted live on Render.

🛠️ Tech Stack

Backend: Python (Flask, SQLite3, Gunicorn)
Frontend: HTML5, CSS3, JavaScript (Fetch API)
Deployment: Render.com
