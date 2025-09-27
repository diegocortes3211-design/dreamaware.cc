import unittest
from pathlib import Path
from packages.ingest.fetch import read_file, FetchError
from services.security.net import verify_url, SSRFBlocked

class TestFetch(unittest.TestCase):
    def test_read_file_cap(self):
        p = Path(__file__).parent / "tmp_small.txt"
        p.write_text("ok", encoding="utf-8")
        try:
            txt = read_file(p, max_bytes=10)
            self.assertEqual(txt, "ok")
            with self.assertRaises(FetchError):
                read_file(p, max_bytes=1)
        finally:
            p.unlink(missing_ok=True)

    def test_verify_blocks_private(self):
        with self.assertRaises(SSRFBlocked):
            verify_url("http://127.0.0.1:8080/")

    def test_verify_scheme(self):
        with self.assertRaises(SSRFBlocked):
            verify_url("file:///etc/passwd")

    def test_allowlist_exact_suffix(self):
        # evilgithub.com must not match github.com
        from services.security import net as netmod
        # Temporarily override the allowlist for this test
        original_allowlist = netmod._ALLOWED_DOMAINS
        netmod._ALLOWED_DOMAINS = ["github.com"]
        try:
            with self.assertRaises(SSRFBlocked):
                verify_url("https://evilgithub.com/path")
            # trailing dot should still be blocked
            with self.assertRaises(SSRFBlocked):
                verify_url("https://evilgithub.com./path")
            # block userinfo
            with self.assertRaises(SSRFBlocked):
                verify_url("https://user:pass@github.com/")
        finally:
            netmod._ALLOWED_DOMAINS = original_allowlist # Restore

if __name__ == "__main__":
    unittest.main()