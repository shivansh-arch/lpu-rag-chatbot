"""
vault.py
Encrypted local credential/session storage for action_gateway.
Knows nothing about UMS, LPU, or automation — pure storage layer.
"""

import json
import os
import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


VAULT_PATH = "vault.enc"

# State while unlocked
_fernet = None
_vault_data = None
_salt = None


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    """Convert passphrase + salt into a Fernet-compatible key."""

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    )

    key = kdf.derive(passphrase.encode("utf-8"))
  
    return base64.urlsafe_b64encode(key)


def init_vault(passphrase: str) -> None:
    """Create a brand-new encrypted vault."""

    global _fernet, _vault_data, _salt

    if os.path.exists(VAULT_PATH):
        raise FileExistsError(
            f"Vault already exists at {VAULT_PATH}"
        )

    if not passphrase:
        raise ValueError("Passphrase cannot be empty")

    # Generate a fresh random salt
    salt = os.urandom(16)

    # Derive encryption key
    key = _derive_key(passphrase, salt)

    # Create Fernet instance
    fernet = Fernet(key)

    # Empty vault
    data = {
        "username": None,
        "password": None,
        "session": None,
    }

    # Convert to bytes
    plaintext = json.dumps(data).encode("utf-8")

    # Encrypt
    encrypted_blob = fernet.encrypt(plaintext)

    # Store binary values as base64 strings
    vault_file = {
        "salt": base64.b64encode(salt).decode("ascii"),
        "encrypted_blob": base64.b64encode(encrypted_blob).decode("ascii"),
    }

    # Write vault
    with open(VAULT_PATH, "w", encoding="utf-8") as f:
        json.dump(vault_file, f)

    # Restrict permissions where supported
    try:
        os.chmod(VAULT_PATH, 0o600)
    except OSError:
        pass

    # Keep decrypted state in memory
    _salt = salt
    _fernet = fernet
    _vault_data = data


def unlock(passphrase: str) -> None:
    """Unlock an existing vault."""

    global _fernet, _vault_data, _salt

    if not os.path.exists(VAULT_PATH):
        raise FileNotFoundError(
            "Vault does not exist. Call init_vault() first."
        )

    if not passphrase:
        raise ValueError("Passphrase cannot be empty")

    try:
        with open(VAULT_PATH, "r", encoding="utf-8") as f:
            vault_file = json.load(f)

        salt = base64.b64decode(vault_file["salt"])
        encrypted_blob = base64.b64decode(
            vault_file["encrypted_blob"]
        )

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise ValueError("Vault file is corrupted") from e

    # Derive key using stored salt
    key = _derive_key(passphrase, salt)

    # Create Fernet
    fernet = Fernet(key)

    # Try to decrypt
    try:
        decrypted = fernet.decrypt(encrypted_blob)
    except InvalidToken as e:
        raise ValueError(
            "Wrong passphrase or corrupted vault"
        ) from e

    try:
        data = json.loads(decrypted.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError("Vault contains invalid data") from e

    # IMPORTANT:
    # Only update state after successful decryption.
    _salt = salt
    _fernet = fernet
    _vault_data = data


def _persist() -> None:
    """Encrypt current vault data and atomically save it."""

    if not is_unlocked():
        raise RuntimeError("Vault is locked")

    plaintext = json.dumps(_vault_data).encode("utf-8")

    encrypted_blob = _fernet.encrypt(plaintext)

    vault_file = {
        "salt": base64.b64encode(_salt).decode("ascii"),
        "encrypted_blob": base64.b64encode(encrypted_blob).decode("ascii"),
    }

    tmp_path = VAULT_PATH + ".tmp"

    try:
        # Write completely to temporary file first
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(vault_file, f)
            f.flush()
            os.fsync(f.fileno())

        # Restrict permissions on temporary file
        try:
            os.chmod(tmp_path, 0o600)
        except OSError:
            pass

        # Atomically replace old vault
        os.replace(tmp_path, VAULT_PATH)

    finally:
        # Clean up temp file if something failed
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # Restrict permissions on final vault
    try:
        os.chmod(VAULT_PATH, 0o600)
    except OSError:
        pass


def store_credentials(username: str, password: str) -> None:
    """Store username and password."""

    if not is_unlocked():
        raise RuntimeError("Vault is locked")

    if not username or not password:
        raise ValueError(
            "Username and password cannot be empty"
        )

    _vault_data["username"] = username
    _vault_data["password"] = password

    _persist()


def store_session(cookies: dict) -> None:
    """Store Playwright session/cookies."""

    if not is_unlocked():
        raise RuntimeError("Vault is locked")

    if not isinstance(cookies, dict):
        raise TypeError("Session must be a dictionary")

    _vault_data["session"] = cookies

    _persist()


def get_credentials() -> tuple[str, str]:
    """Return stored username and password."""

    if not is_unlocked():
        raise RuntimeError("Vault is locked")

    username = _vault_data.get("username")
    password = _vault_data.get("password")

    if username is None or password is None:
        raise ValueError(
            "Credentials have not been stored"
        )

    return username, password


def get_session() -> dict | None:
    """Return stored session or None."""

    if not is_unlocked():
        raise RuntimeError("Vault is locked")

    return _vault_data.get("session")


def is_unlocked() -> bool:
    """Return True if the vault is currently unlocked."""

    return _fernet is not None and _vault_data is not None


def lock() -> None:
    """Clear decrypted vault state from memory."""

    global _fernet, _vault_data, _salt

    _fernet = None
    _vault_data = None
    _salt = None