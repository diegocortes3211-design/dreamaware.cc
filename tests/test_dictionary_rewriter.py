# tests/test_dictionary_rewriter.py

import unittest
from unittest.mock import patch, Mock
import requests  # Import requests at the top level
from services.dictionary.urban_rewriter import UrbanRewriter
from services.dictionary.glossary_builder import GlossaryBuilder

class TestUrbanRewriter(unittest.TestCase):
    """
    Tests for the UrbanRewriter.
    """

    def test_rewrite_text(self):
        """
        Tests that the rewriter correctly replaces slang terms.
        """
        glossary = {
            "GOAT": "Greatest Of All Time",
            "lit": "amazing or cool"
        }
        rewriter = UrbanRewriter(glossary)
        text = "That concert was lit! The artist is the GOAT."
        rewritten_text = rewriter.rewrite(text)

        self.assertIn("lit (meaning: amazing or cool)", rewritten_text)
        self.assertIn("GOAT (meaning: Greatest Of All Time)", rewritten_text)

    def test_rewrite_with_empty_glossary(self):
        """
        Tests that the rewriter returns the original text if the glossary is empty.
        """
        rewriter = UrbanRewriter({})
        text = "This is a test sentence."
        rewritten_text = rewriter.rewrite(text)
        self.assertEqual(text, rewritten_text)

    def test_case_insensitivity(self):
        """
        Tests that rewriting is case-insensitive.
        """
        glossary = {"bae": "before anyone else"}
        rewriter = UrbanRewriter(glossary)
        text = "She is my Bae."
        rewritten_text = rewriter.rewrite(text)
        self.assertIn("Bae (meaning: before anyone else)", rewritten_text)


class TestGlossaryBuilder(unittest.TestCase):
    """
    Tests for the GlossaryBuilder.
    """

    @patch('requests.get')
    def test_build_glossary_success(self, mock_get):
        """
        Tests successful glossary creation from the Urban Dictionary API.
        """
        mock_response = Mock()
        mock_response.json.return_value = {
            "list": [
                {
                    "definition": "The greatest of all time.",
                    "word": "GOAT"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        builder = GlossaryBuilder()
        glossary = builder.build(["GOAT"])
        self.assertEqual(glossary["GOAT"], "The greatest of all time.")
        mock_get.assert_called_once_with("https://api.urbandictionary.com/v0/define", params={"term": "GOAT"})

    @patch('requests.get')
    def test_build_glossary_term_not_found(self, mock_get):
        """
        Tests handling of a term not found in the API.
        """
        mock_response = Mock()
        mock_response.json.return_value = {"list": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        builder = GlossaryBuilder()
        glossary = builder.build(["nonexistentterm"])
        self.assertEqual(glossary["nonexistentterm"], "Definition not found")

    @patch('requests.get')
    def test_build_glossary_api_error(self, mock_get):
        """
        Tests graceful handling of an API request exception.
        """
        mock_get.side_effect = requests.exceptions.RequestException("API is down")

        builder = GlossaryBuilder()
        glossary = builder.build(["anyterm"])
        self.assertEqual(glossary["anyterm"], "Error fetching definition")

if __name__ == "__main__":
    unittest.main()

# commit: test: Add unit tests for Urban Dictionary Rewriter and Glossary Builder.