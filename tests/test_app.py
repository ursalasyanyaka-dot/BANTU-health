import unittest
import json
import os
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

class BantuHealthTestCase(unittest.TestCase):
    
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_clinics_endpoint(self):
        response = self.client.get('/clinics')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)

    def test_stats_endpoint(self):
        response = self.client.get('/stats')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('total_queries', data)

    def test_triage_logic(self):
        # Test symptom payload submission
        response = self.client.post('/chat', json={
            "message": "fever",
            "district": "Chilenje"
        })
        # Check if triage response returns valid guidance and recommended clinics
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('reply', data)

if __name__ == '__main__':
    unittest.main()