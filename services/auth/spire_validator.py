import time, requests, jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

class SPIREValidator:
    def __init__(self, bundle_url="http://spire-server:8081/bundle", aud="dreamaware-video-gen"):
        self.bundle_url = bundle_url
        self.aud = aud
        self._jwks = None
        self._ts = 0

    def _jwks(self):
        if not self._jwks or time.time() - self._ts > 300:
            r = requests.get(self.bundle_url, timeout=3)
            r.raise_for_status() # SPIRE serves JWKS as {"keys": [...]}
            self._jwks = r.json()["keys"]
            self._ts = time.time()
        return self._jwks

    def verify_svid(self, token: str) -> dict:
        try:
            headers = jwt.get_unverified_header(token)
            kid = headers.get("kid")
            key = next((k for k in self._jwks() if k.get("kid") == kid), None)
            if not key:
                raise HTTPException(status_code=401, detail="Unknown SVID key id")
            pub = RSAAlgorithm.from_jwk(key)
            payload = jwt.decode(token, pub, algorithms=[key.get("alg","RS256")], audience=self.aud)
            return payload
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid SVID: {e}")

def verify_spiffe_identity(credentials=Depends(security)):
    v = SPIREValidator()
    return v.verify_svid(credentials.credentials)
