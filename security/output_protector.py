import hmac
import hashlib
import json
import base64
from cryptography.fernet import Fernet, InvalidToken

DEFAULT_PRIVATE_SECRET = "surgeguard_private_key_2026"


def _fernet_key(secret):
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_packet(payload, secret_key=DEFAULT_PRIVATE_SECRET):
    """Encrypt a decision packet with Fernet symmetric encryption."""
    if not isinstance(payload, (dict, list)):
        raise TypeError("Payload must be serializable to JSON")
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    fernet = Fernet(_fernet_key(secret_key))
    token = fernet.encrypt(serialized)
    return token.decode("utf-8")


def decrypt_packet(token, secret_key=DEFAULT_PRIVATE_SECRET):
    """Decrypt a decision packet encrypted with Fernet."""
    fernet = Fernet(_fernet_key(secret_key))
    try:
        data = fernet.decrypt(token.encode("utf-8"))
        return json.loads(data.decode("utf-8"))
    except InvalidToken:
        raise ValueError("Invalid encrypted token or wrong secret key")


def sign_payload(payload, private_secret=DEFAULT_PRIVATE_SECRET):
    """Sign a JSON payload with a secret key using HMAC-SHA256."""
    if not isinstance(payload, (dict, list)):
        raise TypeError("Payload must be serializable to JSON")
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(private_secret.encode("utf-8"), serialized, hashlib.sha256).hexdigest()
    return signature


def verify_signature(payload, signature, private_secret=DEFAULT_PRIVATE_SECRET):
    """Verify a signed JSON payload."""
    expected = sign_payload(payload, private_secret=private_secret)
    return hmac.compare_digest(expected, signature)


def authorize_role(role, action):
    """Mock RBAC check for alert acknowledgement."""
    permissions = {
        "SURGEON": {"ACK_BLEED_ALERT", "VIEW_REPORT"},
        "NURSE": {"VIEW_REPORT"},
        "TECH": set(),
    }
    allowed_actions = permissions.get(role.upper(), set())
    return action in allowed_actions


def acknowledge_alert(user_role, alert_payload):
    """Return acknowledgement status only if user has surgeon privileges."""
    if not authorize_role(user_role, "ACK_BLEED_ALERT"):
        raise PermissionError("User role does not have permission to acknowledge bleed alerts")
    return {
        "acknowledged_by": user_role,
        "timestamp": int(__import__("time").time()),
        "alert": alert_payload,
    }
