"""
Compatibility shim for `jwt.exceptions` to provide a few exception
names expected by third-party libraries (e.g. rest_framework_simplejwt
or jwt.algorithms) when a conflicting or minimal jwt package is present.

This defines lightweight exception classes and intentionally keeps
dependencies minimal.
"""

class InvalidKeyError(Exception):
    """Raised when a provided key is invalid for an operation."""
    pass


class InvalidAlgorithmError(Exception):
    """Raised when an algorithm is not supported or invalid."""
    pass


class InvalidTokenError(Exception):
    """Base class for invalid token errors."""
    pass


class DecodeError(InvalidTokenError):
    """Raised when a token cannot be decoded."""
    pass


class ExpiredSignatureError(InvalidTokenError):
    """Raised when a token's signature has expired."""
    pass


class InvalidSignatureError(InvalidTokenError):
    """Raised when a token signature is invalid."""
    pass
