import unittest

from fastapi.testclient import TestClient

from smart_code_analyzer.main import app


class TestMainApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Тест корневого эндпоинта"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Smart Code Analyzer API"})


if __name__ == '__main__':
    unittest.main()
