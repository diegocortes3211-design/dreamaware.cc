from __future__ import annotations
import jwt
import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# --- Key Generation (In-memory for this example) ---
# In a production environment, these keys would be loaded securely from a vault
# or environment variables, not generated on the fly.
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
public_key = private_key.public_key()

# Serialize keys to PEM format for use with pyjwt
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)

ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    """
    Generates a signed JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, private_pem, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    """
    Decodes and validates a JWT access token.
    Returns the payload if the token is valid, otherwise returns None.
    """
    try:
        payload = jwt.decode(token, public_pem, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        # This will catch expired tokens, invalid signatures, etc.
        return None