import os
from typing import Dict, Any

class DreadConfig:
    """Configuration for DreadAPI privacy settings"""

    # Privacy levels
    PRIVACY_MAXIMUM = "maximum"
    PRIVACY_HIGH = "high"
    PRIVACY_STANDARD = "standard"

    def __init__(self):
        self.privacy_level = os.getenv("DREAD_PRIVACY_LEVEL", self.PRIVACY_MAXIMUM)
        self.enable_onion_routing = os.getenv("DREAD_ENABLE_ONION", "true").lower() == "true"
        self.enable_ring_signatures = os.getenv("DREAD_ENABLE_RING_SIG", "true").lower() == "true"
        self.session_timeout = int(os.getenv("DREAD_SESSION_TIMEOUT", "3600"))
        self.rate_limit_per_hour = int(os.getenv("DREAD_RATE_LIMIT", "100"))

        # Cryptography settings
        self.encryption_algorithm = os.getenv("DREAD_ENC_ALGO", "chacha20-poly1305")
        self.key_rotation_interval = int(os.getenv("DREAD_KEY_ROTATION", "900"))  # 15 minutes

    def get_privacy_manifest(self) -> Dict[str, Any]:
        """Get privacy manifest for API transparency"""
        return {
            "privacy_level": self.privacy_level,
            "data_collection": "none",
            "log_retention": "0_days",
            "ip_handling": "immediate_discard",
            "user_tracking": "disabled",
            "third_party_sharing": "none",
            "compliance": [
                "gdpr_article_17_right_to_erasure",
                "ccpa_do_not_sell",
                "zero_knowledge_principles"
            ]
        }