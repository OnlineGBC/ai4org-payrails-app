from cryptography.fernet import Fernet
from app.config import settings

_key = None
_fernet = None


def _get_fernet() -> Fernet:
    global _key, _fernet
    if _fernet is None:
        if settings.ENCRYPTION_KEY:
            _key = settings.ENCRYPTION_KEY.encode()
        else:
            _key = Fernet.generate_key()
        _fernet = Fernet(_key)
    return _fernet


def encrypt_value(value: str) -> str:
    f = _get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    f = _get_fernet()
    return f.decrypt(encrypted_value.encode()).decode()
