import json
import os
import unittest
from unittest.mock import MagicMock, patch

from services.evaluation import reviewscore

class TestReviewScore(unittest.TestCase):

    def setUp(self):
        self.input_dir = "test_input"
        self.output_file = "test_output.jsonl"
        os.makedirs(self.input_dir, exist_ok=True)

        # Create a dummy input file
        self.dummy_review = {
            "id": "123",
            "review": "This is a test review."
        }
        with open(os.path.join(self.input_dir, "test.jsonl"), "w") as f:
            f.write(json.dumps(self.dummy_review))

    def tearDown(self):
        # Clean up the created files and directories
        os.remove(os.path.join(self.input_dir, "test.jsonl"))
        os.rmdir(self.input_dir)
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    @patch('services.evaluation.reviewscore.InferenceClient')
    @patch('services.evaluation.reviewscore.os.getenv')
    def test_main(self, mock_getenv, MockInferenceClient):
        # Mock the environment variables
        mock_getenv.side_effect = lambda key, default: {
            "INPUT_DIR": self.input_dir,
            "OUTPUT_FILE": self.output_file,
            "HF_MODEL": "ReviewScore-v1"
        }.get(key, default)

        # Mock the InferenceClient and its text_generation method
        mock_client = MockInferenceClient.return_value
        mock_response = {
            "misinformed": False,
            "issues": []
        }
        # The model returns a JSON string, so we need to dump it
        mock_client.text_generation.return_value = json.dumps(mock_response)

        # Run the main function of the script
        reviewscore.main()

        # Check that the output file was created and has the correct content
        self.assertTrue(os.path.exists(self.output_file))
        with open(self.output_file, "r") as f:
            result = json.loads(f.readline())

        self.assertEqual(result["id"], self.dummy_review["id"])
        self.assertEqual(result["misinformed"], mock_response["misinformed"])
        self.assertEqual(result["issues"], mock_response["issues"])

if __name__ == "__main__":
    unittest.main()