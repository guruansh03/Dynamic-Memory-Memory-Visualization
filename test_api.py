import unittest
from unittest.mock import patch
from app import app

class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def tearDown(self):
        # Any cleanup can be done here if necessary
        pass

    @patch('app.some_external_service')  # Mocking an external service
    def test_allocate_paging(self, mock_service):
        mock_service.return_value = True  # Simulate successful external service call
        response = self.client.post("/allocate_paging", json={"process_id": "P1", "num_pages": 2})
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json)

    @patch('app.some_external_service')
    def test_allocate_paging_invalid(self, mock_service):
        mock_service.return_value = False  # Simulate failure in external service
        response = self.client.post("/allocate_paging", json={"process_id": "P1", "num_pages": -1})
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json)

    def test_memory_state(self):
        response = self.client.get("/memory_state")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)

    def test_memory_state_empty(self):
        response = self.client.get("/memory_state?empty=true")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, {})

    def test_allocate_paging_multiple_cases(self):
        test_cases = [
            ({"process_id": "P1", "num_pages": 2}, 200),
            ({"process_id": "P2", "num_pages": 0}, 400),  # Invalid case
            ({"process_id": "P3", "num_pages": 5}, 200)
        ]
        for data, expected_status in test_cases:
            with self.subTest(data=data):
                response = self.client.post("/allocate_paging", json=data)
                self.assertEqual(response.status_code, expected_status)

if __name__ == "__main__":
    unittest.main()
