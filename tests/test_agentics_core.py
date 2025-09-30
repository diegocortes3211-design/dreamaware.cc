import unittest
from unittest.mock import patch, MagicMock
from services.agentics.executive import plan
from services.agentics.self_modify import propose

class TestAgenticsLLM(unittest.TestCase):

    @patch('services.agentics.executive.GeminiClient')
    @patch('services.agentics.executive.load_catalog')
    def test_plan_llm_success(self, mock_load_catalog, mock_gemini_client):
        """Tests that the planner returns a plan from the LLM when the call is successful."""
        # Arrange
        mock_load_catalog.return_value = [{"name": "test_action"}]
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_json.return_value = {"plan": [{"name": "llm_generated_action"}]}
        mock_gemini_client.return_value = mock_llm_instance

        # Act
        result = plan("test objective", "dummy_path")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'llm_generated_action')
        mock_llm_instance.generate_json.assert_called_once()

    @patch('services.agentics.executive.GeminiClient')
    @patch('services.agentics.executive.load_catalog')
    def test_plan_llm_fallback(self, mock_load_catalog, mock_gemini_client):
        """Tests that the planner returns a fallback plan when the LLM call fails."""
        # Arrange
        mock_load_catalog.return_value = [{"name": "test_action"}]
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_json.return_value = {}  # Simulate LLM failure
        mock_gemini_client.return_value = mock_llm_instance

        # Act
        result = plan("http://example.com", "dummy_path")

        # Assert
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['name'], 'fetch_url')
        self.assertEqual(result[0]['inputs']['url'], 'http://example.com')
        mock_llm_instance.generate_json.assert_called_once()

    @patch('services.agentics.self_modify.GeminiClient')
    def test_propose_llm_success(self, mock_gemini_client):
        """Tests that the proposer returns proposals from the LLM when the call is successful."""
        # Arrange
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_json.return_value = {"proposals": [{"target": "llm_proposal"}]}
        mock_gemini_client.return_value = mock_llm_instance
        evaluation_data = {"score": {"safety": 0.8}}

        # Act
        result = propose(evaluation_data)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['target'], 'llm_proposal')
        mock_llm_instance.generate_json.assert_called_once()

    @patch('services.agentics.self_modify.GeminiClient')
    def test_propose_llm_fallback(self, mock_gemini_client):
        """Tests that the proposer returns a fallback proposal when the LLM call fails."""
        # Arrange
        mock_llm_instance = MagicMock()
        mock_llm_instance.generate_json.return_value = {}  # Simulate LLM failure
        mock_gemini_client.return_value = mock_llm_instance
        evaluation_data = {"score": {"safety": 0.8}}

        # Act
        result = propose(evaluation_data)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['target'], 'docs')
        self.assertEqual(result[0]['rationale'], 'no valid llm output')
        mock_llm_instance.generate_json.assert_called_once()

if __name__ == '__main__':
    unittest.main()