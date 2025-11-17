from django.test import TestCase

class HealthTest(TestCase):
    def test_health_ok(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get('status'), 'ok')
        self.assertIn('db', data)
        self.assertIn('engine', data)