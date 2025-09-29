# tests/test_wiki_score_fetcher.py

import unittest
from unittest.mock import patch, Mock
import requests  # Import requests at the top level
from services.wiki.score_fetcher import WikipediaScoreFetcher

class TestWikipediaScoreFetcher(unittest.TestCase):
    """
    Tests for the WikipediaScoreFetcher.
    """

    def setUp(self):
        """
        Set up a new WikipediaScoreFetcher for each test.
        """
        self.fetcher = WikipediaScoreFetcher()

    @patch('requests.get')
    def test_fetch_score_success(self, mock_get):
        """
        Tests a successful score fetch for an existing Wikipedia page.
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "6136": {
                        "pageid": 6136,
                        "title": "Artificial intelligence",
                        "extract": "Artificial intelligence (AI) is the intelligence of machines or software..." * 10
                    }
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        score = self.fetcher.fetch_score("Artificial intelligence")
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 1.0)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_fetch_score_nonexistent_page(self, mock_get):
        """
        Tests that a non-existent page returns a score of 0.
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "query": {
                "pages": {
                    "-1": {
                        "ns": 0,
                        "title": "A_Completely_NonExistent_Topic_Abc123",
                        "missing": ""
                    }
                }
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        score = self.fetcher.fetch_score("A_Completely_NonExistent_Topic_Abc123")
        self.assertEqual(score, 0.0)

    @patch('requests.get')
    def test_fetch_score_request_exception(self, mock_get):
        """
        Tests that a request exception is handled gracefully and returns a score of 0.
        """
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        score = self.fetcher.fetch_score("Any Topic")
        self.assertEqual(score, 0.0)

    @patch('requests.get')
    def test_fetch_score_malformed_response(self, mock_get):
        """
        Tests that a malformed API response is handled and returns a score of 0.
        """
        mock_response = Mock()
        # Simulate a response missing the 'pages' key
        mock_response.json.return_value = {"query": {}}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        score = self.fetcher.fetch_score("Any Topic")
        self.assertEqual(score, 0.0)

if __name__ == "__main__":
    unittest.main()

# commit: test: Add unit tests for Wikipedia Score Fetcher with mocking.