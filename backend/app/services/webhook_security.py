"""HMAC signature verification for inbound partner webhooks."""
import hashlib
import hmac


def verify_hmac(secret: str, raw_body: bytes, provided_signature: str) -> bool:
    """Constant-time verify a hex HMAC-SHA256 over the raw request body.

    Accepts a bare hex digest or a 'sha256=' prefixed value (GitHub-style).
    """
    if not secret or not provided_signature:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    provided = provided_signature
    if provided.startswith("sha256="):
        provided = provided.split("=", 1)[1]
    return hmac.compare_digest(expected, provided)
