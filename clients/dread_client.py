import requests
import json
import hashlib
import hmac
import secrets
from typing import Dict, Any, Optional

class DreadClient:
    """Privacy-focused client for DreadAPI"""

    def __init__(self, base_url: str = "https://dreadapi.dreamaware.ai"):
        self.base_url = base_url
        self.session_id = None
        self.ephemeral_key = None

    def create_session(self) -> bool:
        """Create anonymous session"""
        try:
            response = requests.post(
                f"{self.base_url}/v1/session/create",
                json={"client_public_key": None}  # No key exchange in demo
            )

            if response.status_code == 200:
                data = response.json()
                self.session_id = data["session_id"]
                self.ephemeral_key = data["ephemeral_key"]
                return True

        except Exception as e:
            print(f"Session creation failed: {e}")

        return False

    def _create_signature(self, message: str) -> str:
        """Create HMAC signature for request"""
        return hmac.new(
            self.ephemeral_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

    def send_anonymous_message(self, message: str) -> Optional[Dict[str, Any]]:
        """Send message with maximum privacy"""
        if not self.session_id:
            if not self.create_session():
                return None

        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/anonymous",
                json={"message": message},
                headers={
                    "x-session-id": self.session_id,
                    "x-signature": self._create_signature(message),
                    "x-privacy-required": "true"
                }
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print(f"Message send failed: {e}")

        return None

    def get_privacy_status(self) -> Optional[Dict[str, Any]]:
        """Get current privacy status"""
        if not self.session_id:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/v1/privacy/status",
                headers={
                    "x-session-id": self.session_id,
                    "x-privacy-required": "true"
                }
            )

            if response.status_code == 200:
                return response.json()

        except Exception:
            pass

        return None

# Example usage
if __name__ == "__main__":
    client = DreadClient()

    # Create anonymous session
    if client.create_session():
        print("Anonymous session created")

        # Send private message
        response = client.send_anonymous_message("Hello with maximum privacy!")
        if response:
            print(f"Private response: {response}")

        # Check privacy status
        status = client.get_privacy_status()
        if status:
            print(f"Privacy level: {status['privacy_level']}")