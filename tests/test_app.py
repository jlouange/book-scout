import unittest
from unittest.mock import Mock, patch

from app import app

class TestBookScoutApi(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
    def test_health_check(self):
        response = self.client.get("/api/health")


        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"status": "healthy"})

    def test_invalid_search_type(self):
        response = self.client.get("/api/books?q=Linux&type=publisher")
        self.assertEqual(response.status_code, 400)

    @patch("app.requests.get")
    def test_book_search(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value ={
            "numFound": 1,
            "docs": [
                {
                    "key": "/works/OL1W",
                    "title": "Linux Basics",
                    "author_name": ["Laus"],
                    "first_publish_year": 2023
                }
            ]
        }

        mock_get.return_value = mock_response

        response = self.client.get("/api/books?q=Linux&type=title")


        self.assertEqual(response.status_code, 200)
        result = response.get_json()
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["books"][0]["book_title"], "Linux Basics")


if __name__ == "__main__":
    unittest.main()