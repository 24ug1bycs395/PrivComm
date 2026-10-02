"""Ed25519 signing with cryptography, PyNaCl, or a pure Python fallback."""

import hashlib
import json
import os
KEY_FILE = "seal_keys.json"
_P = 2**255 - 19
_Q = 2**252 + 27742317777372353535851937790883648493
_D = (-121665 * pow(121666, _P - 2, _P)) % _P
_I = pow(2, (_P - 1) // 4, _P)
_BY = 4 * pow(5, _P - 2, _P) % _P
_BX = pow((_BY * _BY - 1) * pow(_D * _BY * _BY + 1, _P - 2, _P), (_P + 3) // 8, _P)
if (_BX * _BX - (_BY * _BY - 1) * pow(_D * _BY * _BY + 1, _P - 2, _P)) % _P:
    _BX = (_BX * _I) % _P
_BASE = (_BX, _BY)


def _pure_public(private_key: bytes) -> bytes:
    d = hashlib.sha512(private_key).digest()
    scalar = int.from_bytes(d[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return _pure_encode(_pure_scalar_mult(_BASE, scalar), _P)


def _pure_add(point_a: tuple[int, int], point_b: tuple[int, int], p: int = _P) -> tuple[int, int]:
    """Add two Edwards curve points for the RFC 8032 fallback."""
    x1, y1 = point_a
    x2, y2 = point_b
    factor = _D * x1 * x2 * y1 * y2 % p
    x3 = (x1 * y2 + x2 * y1) * pow(1 + factor, p - 2, p) % p
    y3 = (y1 * y2 + x1 * x2) * pow(1 - factor, p - 2, p) % p
    return x3, y3


def _pure_scalar_mult(point: tuple[int, int], scalar: int) -> tuple[int, int]:
    result = (0, 1)
    current = point
    while scalar:
        if scalar & 1:
            result = _pure_add(result, current)
        current = _pure_add(current, current)
        scalar >>= 1
    return result


def _pure_encode(point: tuple[int, int], p: int) -> bytes:
    x, y = point
    value = y | ((x & 1) << 255)
    return value.to_bytes(32, "little")


def _pure_decode(encoded: bytes) -> tuple[int, int] | None:
    if len(encoded) != 32:
        return None
    value = int.from_bytes(encoded, "little")
    sign_bit = value >> 255
    y = value & ((1 << 255) - 1)
    if y >= _P:
        return None
    xx = (y * y - 1) * pow(_D * y * y + 1, _P - 2, _P) % _P
    x = pow(xx, (_P + 3) // 8, _P)
    if (x * x - xx) % _P:
        x = x * _I % _P
    if (x * x - xx) % _P or (x & 1) != sign_bit:
        return None
    return x, y


def _pure_sign(private_key: bytes, message: bytes) -> bytes:
    digest = hashlib.sha512(private_key).digest()
    scalar_bytes = bytearray(digest[:32])
    scalar_bytes[0] &= 248
    scalar_bytes[31] &= 63
    scalar_bytes[31] |= 64
    scalar = int.from_bytes(scalar_bytes, "little")
    public_key = _pure_encode(_pure_scalar_mult(_BASE, scalar), _P)
    nonce = int.from_bytes(hashlib.sha512(digest[32:] + message).digest(), "little") % _Q
    encoded_r = _pure_encode(_pure_scalar_mult(_BASE, nonce), _P)
    challenge = int.from_bytes(
        hashlib.sha512(encoded_r + public_key + message).digest(), "little"
    ) % _Q
    signature_scalar = (nonce + challenge * scalar) % _Q
    return encoded_r + signature_scalar.to_bytes(32, "little")


def _pure_verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    if len(signature) != 64:
        return False
    point_a = _pure_decode(public_key)
    point_r = _pure_decode(signature[:32])
    scalar_s = int.from_bytes(signature[32:], "little")
    if point_a is None or point_r is None or scalar_s >= _Q:
        return False
    challenge = int.from_bytes(
        hashlib.sha512(signature[:32] + public_key + message).digest(), "little"
    ) % _Q
    left = _pure_scalar_mult(_BASE, scalar_s)
    right = _pure_add(point_r, _pure_scalar_mult(point_a, challenge))
    return _pure_encode(left, _P) == _pure_encode(right, _P)


def generate_keypair() -> tuple[bytes, bytes]:
    """Generate and persist a 32-byte Ed25519 private/public key pair."""
    private_key = os.urandom(32)
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        private = Ed25519PrivateKey.from_private_bytes(private_key)
        from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
        public_key = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    except ImportError:
        try:
            from nacl.signing import SigningKey
            public_key = bytes(SigningKey(private_key).verify_key)
        except ImportError:
            public_key = _pure_public(private_key)
    _save_keypair(private_key, public_key)
    return private_key, public_key


def _save_keypair(private_key: bytes, public_key: bytes) -> None:
    with open(KEY_FILE, "w", encoding="utf-8") as handle:
        json.dump(
            {"private_key": private_key.hex(), "public_key": public_key.hex()},
            handle,
            indent=2,
        )
    try:
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass


def load_keypair() -> tuple[bytes, bytes]:
    """Load the project key pair or generate it on first use."""
    if not os.path.exists(KEY_FILE):
        return generate_keypair()
    try:
        with open(KEY_FILE, encoding="utf-8") as handle:
            data = json.load(handle)
        return bytes.fromhex(data["private_key"]), bytes.fromhex(data["public_key"])
    except (OSError, KeyError, ValueError, json.JSONDecodeError):
        return generate_keypair()


def sign(private_key: bytes, message: bytes) -> bytes:
    """Sign message with Ed25519."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        return Ed25519PrivateKey.from_private_bytes(private_key).sign(message)
    except ImportError:
        try:
            from nacl.signing import SigningKey
            return bytes(SigningKey(private_key).sign(message).signature)
        except ImportError:
            return _pure_sign(private_key, message)


def verify(public_key: bytes, message: bytes, signature: bytes) -> bool:
    """Return whether an Ed25519 signature is valid."""
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
        return True
    except ImportError:
        try:
            from nacl.signing import VerifyKey
            VerifyKey(public_key).verify(message, signature)
            return True
        except ImportError:
            return _pure_verify(public_key, message, signature)
    except (ValueError, TypeError):
        return False
