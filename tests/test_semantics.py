# tests/test_semantics.py

import unittest
import sys
from unittest.mock import patch, MagicMock
from types import ModuleType

# This is a sample tensor-like object that the real library might return.
class MockTensor:
    def __init__(self, value):
        self.value = value
    def item(self):
        return self.value

class TestSemanticsComparator(unittest.TestCase):
    """
    Tests for the SemanticsComparator.
    """
    def setUp(self):
        """Set up mocks for sentence-transformers before each test."""
        # Create mock objects for the class and function we need
        self.mock_st_class = MagicMock()
        self.mock_cos_sim = MagicMock(return_value=MockTensor(0.99))

        # Create a mock module structure that the importer can understand
        mock_st_module = ModuleType('sentence_transformers')
        mock_st_util_module = ModuleType('sentence_transformers.util')

        # Assign the mocked class and function to the mock modules
        mock_st_module.SentenceTransformer = self.mock_st_class
        mock_st_module.util = mock_st_util_module
        mock_st_util_module.cos_sim = self.mock_cos_sim

        # This dictionary will be used to patch sys.modules
        self.modules = {
            'sentence_transformers': mock_st_module,
            'sentence_transformers.util': mock_st_util_module,
            'torch': MagicMock() # sentence-transformers also imports torch
        }

        # We need to remove the module under test from cache before patching
        # to ensure it's re-imported under the mock environment.
        if 'services.semantics.comparator' in sys.modules:
            del sys.modules['services.semantics.comparator']

    def test_compare_similar_texts_with_mock(self):
        """
        Tests that the comparator initializes and works correctly with mocked dependencies.
        """
        with patch.dict('sys.modules', self.modules):
            # Import the class *inside* the patch context so it sees the mocks
            from services.semantics.comparator import SemanticsComparator
            comparator = SemanticsComparator()

        # 1. Check if the comparator initialized correctly
        self.assertTrue(comparator.ready, "Comparator should be ready when dependencies are mocked.")

        # 2. Call the method under test
        score = comparator.compare("This is a test sentence.", "This is a test sentence.")

        # 3. Assert the results
        self.assertAlmostEqual(score, 0.99, places=2)
        self.assertEqual(comparator.model.encode.call_count, 2)
        self.mock_cos_sim.assert_called_once()

    def test_compare_with_empty_text(self):
        """
        Tests that comparing with an empty string returns a score of 0.
        """
        with patch.dict('sys.modules', self.modules):
            from services.semantics.comparator import SemanticsComparator
            comparator = SemanticsComparator()

        score1 = comparator.compare("", "Some text")
        score2 = comparator.compare("Some text", "")
        self.assertEqual(score1, 0.0)
        self.assertEqual(score2, 0.0)

    def test_initialization_failure_on_import_error(self):
        """
        Tests that the comparator handles an ImportError gracefully.
        """
        # To reliably trigger an ImportError, we patch the module name in
        # sys.modules to be None for the duration of the test.
        faulty_modules = sys.modules.copy()
        faulty_modules['sentence_transformers'] = None

        # Remove the module under test from cache to force a re-import
        if 'services.semantics.comparator' in sys.modules:
            del sys.modules['services.semantics.comparator']

        with patch.dict('sys.modules', faulty_modules):
            from services.semantics.comparator import SemanticsComparator
            comparator = SemanticsComparator()

        self.assertFalse(comparator.ready, "Comparator should not be ready if import fails.")

        # Ensure that compare returns 0 if initialization failed
        score = comparator.compare("text1", "text2")
        self.assertEqual(score, 0.0)

if __name__ == '__main__':
    unittest.main()

# commit: fix: Correctly simulate ImportError in Semantics Comparator tests.