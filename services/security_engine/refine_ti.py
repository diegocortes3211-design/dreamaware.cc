import os, requests, json

VT_API_KEY = os.getenv("VT_API_KEY")
MOCK_FIXTURES = True  # CI mode

class TIRefiner:
    def __init__(self): pass

    def refine(self, mask: dict) -> dict:
        for c in mask.get("components", []):
            h = c.get("sha256")
            if h:
                rep = self._vt_lookup(h)
                if rep and rep.get("malicious", 0) > 0:
                    c["score"] = min(1.0, c.get("score", 0.5) + 0.3)
                    c.setdefault("tags", []).append(f"vt:malicious:{rep['malicious']}")
        return mask

    def _vt_lookup(self, hash: str) -> dict | None:
        if MOCK_FIXTURES:
            # CI stub: return mock based on hash pattern
            if hash.startswith("deadbeef"): return {"malicious": 5, "harmless": 0}
            return {"malicious": 0, "harmless": 42}
        if not VT_API_KEY: return None
        url = f"https://www.virustotal.com/api/v3/files/{hash}"
        headers = {"x-apikey": VT_API_KEY}
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.raise_for_status()
            data = r.json()["data"]["attributes"]["last_analysis_stats"]
            return data
        except Exception:
            return None

if __name__ == "__main__":
    # Test stub
    ref = TIRefiner()
    mask = {"components": [{"sha256": "deadbeef1234", "score": 0.6}]}
    refined = ref.refine(mask)
    print(json.dumps(refined, indent=2))
