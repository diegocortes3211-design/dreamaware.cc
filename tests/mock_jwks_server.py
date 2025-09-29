from fastapi import FastAPI
from jose import jwa, jwk
from jose.constants import ALGORITHMS
import json

# Generate a new RSA key pair
private_key = jwk.generate_key('RSA', algorithm=ALGORITHMS.RS256)
public_key = {**private_key, 'd': None} # Remove private component

# Create a JWKS (JSON Web Key Set)
jwks = {
    "keys": [
        {
            "kty": "RSA",
            "kid": "test-key-1",
            "use": "sig",
            "alg": "RS256",
            "n": public_key['n'],
            "e": public_key['e'],
        }
    ]
}

app = FastAPI()

@app.get("/.well-known/jwks.json")
async def get_jwks():
    return jwks

# A helper endpoint for tests to get the private key for signing tokens
@app.get("/private-key")
async def get_private_key():
    return {
        "kty": "RSA",
        "kid": "test-key-1",
        "use": "sig",
        "alg": "RS256",
        "n": private_key['n'],
        "e": private_key['e'],
        "d": private_key['d'],
    }