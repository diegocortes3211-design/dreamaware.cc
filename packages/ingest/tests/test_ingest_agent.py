from __future__ import annotations
import unittest
from pathlib import Path
from unittest.mock import patch

from packages.ingest.ingestion import IngestAgent, MAX_FILE_BYTES, FetchError

class DummyRetriever: ...
class DummyPrompt: ...

class TestIngestAgent(unittest.TestCase):
    def setUp(self):
        self.agent = IngestAgent(DummyRetriever(), DummyPrompt())

    @patch("packages.ingest.ingestion.fetch_url")
    def test_fetch_content_http_https(self, mock_fetch_url):
        mock_fetch_url.return_value = "OK"
        self.assertEqual(self.agent.fetch_content("http://example.com"), "OK")
        self.assertEqual(self.agent.fetch_content("https://example.com"), "OK")
        mock_fetch_url.assert_any_call("http://example.com", max_bytes=MAX_FILE_BYTES)
        mock_fetch_url.assert_any_call("https://example.com", max_bytes=MAX_FILE_BYTES)

    def test_fetch_content_reject_scheme(self):
        with self.assertRaises(FetchError):
            self.agent.fetch_content("file:///etc/passwd")
        with self.assertRaises(FetchError):
            self.agent.fetch_content("ftp://example.com/x")

    @patch("packages.ingest.ingestion.read_file")
    @patch("packages.ingest.ingestion.Path.is_file")
    def test_fetch_content_local(self, mock_is_file, mock_read_file):
        mock_is_file.return_value = True
        p = Path(__file__).parent / "tmp_local.txt"

        mock_read_file.return_value = "LOCAL_OK"
        self.assertEqual(self.agent.fetch_content(str(p)), "LOCAL_OK")
        mock_read_file.assert_called_once_with(p, max_bytes=MAX_FILE_BYTES)

    def test_preprocess_chunking(self):
        text = ("A"*800) + "\n\n" + ("B"*800) + "\n\n" + ("C"*1600)
        chunks = self.agent.preprocess(text)
        self.assertTrue(all(1 <= len(c) <= 1200 for c in chunks))
        self.assertGreaterEqual(len(chunks), 3)

if __name__ == "__main__":
    unittest.main()