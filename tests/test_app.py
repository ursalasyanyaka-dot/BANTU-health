import unittest
import sys
import os

# Ensure project root is in path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import app

class BantuHealthTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test client before each test"""
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()
    
    def test_haversine_distance(self):
        """Test that the Haversine formula calculates realistic distances"""
        # Coordinates for Lusaka Central vs Chilenje 
        lat1, lon1 = (-15.3875, 28.3228)
        lat2, lon2 = (-15.4321, 28.3120)
        distance = app.haversine(lat1, lon1, lat2, lon2)
        # Distance should be roughly between 0.5km and 15km
        self.assertTrue(0.5 <= distance <= 15.0)
        
    def test_symptom_lookup(self):
        """Test symptom dictionary parsing and fallback advice"""
        # Check if fever exists in the app symptom dict
        self.assertIn('fever', app.Symptoms)
        self.assertEqual(app.Symptoms['fever']['severity'], 'medium')

if __name__ == '__main__':
    unittest.main()